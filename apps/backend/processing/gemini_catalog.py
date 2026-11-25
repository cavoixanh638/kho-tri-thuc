"""Gemini models.list discovery, at most twice a day, with a DB lease.

No text/image data or paid generateContent probes are sent during discovery.
The model catalog is metadata only: it cannot prove model-level account access,
modality, current free tokens, price, or deprecation date.
"""
import json
import logging
import os
import re
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.db import transaction
from django.utils import timezone

from .gemini_policy import MODEL_PROFILES
from .models import GeminiCatalogState, GeminiModelCatalog

logger = logging.getLogger(__name__)
API = "https://generativelanguage.googleapis.com/v1beta/models"
REFRESH_HOURS = 12
RETRY_MINUTES = 60
ID = re.compile(r"^models/(gemini-[a-zA-Z0-9_.-]{1,110})$")


class DiscoveryError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise DiscoveryError("unexpected_redirect")


def normalize_model(value):
    if not isinstance(value, dict):
        return None
    match = ID.fullmatch(value.get("name", ""))
    if not match:
        return None
    methods = value.get("supportedGenerationMethods", [])
    if not isinstance(methods, list):
        methods = []
    methods = [method for method in methods if isinstance(method, str) and method in
               {"generateContent", "countTokens", "embedContent", "batchGenerateContent"}]
    return {
        "model_id": match[1],
        "label": str(value.get("displayName") or match[1])[:128],
        "description": str(value.get("description") or "")[:512],
        "generation_methods": sorted(set(methods)),
        "input_token_limit": bounded_int(value.get("inputTokenLimit")),
        "output_token_limit": bounded_int(value.get("outputTokenLimit")),
    }


def bounded_int(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        return 0
    return min(max(number, 0), 2_147_483_647)


def list_models(api_key, *, opener=None):
    """Read only Google's fixed HTTPS host, bounded pagination and payload."""
    if not api_key or not isinstance(api_key, str):
        raise DiscoveryError("not_configured")
    opener = opener or build_opener(NoRedirects())
    items = {}
    token = ""
    seen_tokens = set()
    try:
        for page in range(10):
            params = {"pageSize": "1000"}
            if token:
                params["pageToken"] = token
            url = API + "?" + urlencode(params)
            response = opener.open(Request(
                url,
                headers={"x-goog-api-key": api_key, "Accept": "application/json"},
                method="GET",
            ), timeout=10)
            with response:
                raw = response.read(3 * 1024 * 1024 + 1)
            if len(raw) > 3 * 1024 * 1024:
                raise DiscoveryError("response_too_large")
            result = json.loads(raw)
            if not isinstance(result, dict) or not isinstance(result.get("models"), list):
                raise DiscoveryError("invalid_catalog_response")
            for row in result["models"]:
                normalized = normalize_model(row)
                if normalized:
                    items[normalized["model_id"]] = normalized
            token = result.get("nextPageToken") or ""
            if not token:
                return list(items.values())
            if not isinstance(token, str) or len(token) > 2048 or token in seen_tokens:
                raise DiscoveryError("invalid_pagination")
            seen_tokens.add(token)
        raise DiscoveryError("too_many_pages")
    except HTTPError as exc:
        code = "invalid_api_key" if exc.code == 401 else (
            "permission_denied" if exc.code == 403 else
            "rate_limited" if exc.code == 429 else
            "provider_unavailable" if exc.code >= 500 else "provider_http_error"
        )
        raise DiscoveryError(code) from None
    except (URLError, TimeoutError, OSError):
        raise DiscoveryError("network_unavailable") from None
    except (UnicodeError, json.JSONDecodeError, ValueError, TypeError):
        raise DiscoveryError("invalid_catalog_response") from None


def apply_discovery(models, now=None):
    """Only commit a complete catalog; partial failure never removes models."""
    now = now or timezone.now()
    seen = set()
    new = 0
    with transaction.atomic():
        for meta in models:
            model_id = meta["model_id"]
            seen.add(model_id)
            profile = MODEL_PROFILES.get(model_id)
            reviewed = bool(profile and profile.get("image_ocr")
                            and "generateContent" in meta["generation_methods"])
            record, created = GeminiModelCatalog.objects.get_or_create(
                model_id=model_id,
                defaults={
                    "label": meta["label"], "description": meta["description"],
                    "generation_methods": meta["generation_methods"],
                    "input_token_limit": meta["input_token_limit"],
                    "output_token_limit": meta["output_token_limit"],
                    "last_seen_at": now, "active": True, "reviewed": reviewed,
                },
            )
            if created:
                new += 1
            else:
                GeminiModelCatalog.objects.filter(pk=model_id).update(
                    label=meta["label"], description=meta["description"],
                    generation_methods=meta["generation_methods"],
                    input_token_limit=meta["input_token_limit"],
                    output_token_limit=meta["output_token_limit"],
                    active=True, reviewed=reviewed, missing_sync_count=0,
                    last_seen_at=now,
                )
        # Only mark missing after TWO successful, complete snapshots.
        for absent in GeminiModelCatalog.objects.exclude(model_id__in=seen):
            count = min(absent.missing_sync_count + 1, 65535)
            GeminiModelCatalog.objects.filter(pk=absent.pk).update(
                missing_sync_count=count, active=count < 2,
            )
        GeminiCatalogState.objects.update_or_create(pk=1, defaults={
            "last_success_at": now, "last_attempt_at": now,
            "next_refresh_at": now + timedelta(hours=REFRESH_HOURS),
            "last_error_code": "", "discovered_count": len(seen),
            "newly_discovered": new,
        })
    return {"seen": len(seen), "new": new}


def refresh_if_due(*, force=False, api_key=None, now=None, fetcher=None):
    """Project-wide lease; force is only for an authenticated staff action."""
    api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "not_configured"
    now = now or timezone.now()
    with transaction.atomic():
        state, _ = GeminiCatalogState.objects.select_for_update().get_or_create(
            pk=1,
        )
        if state.next_refresh_at and state.next_refresh_at > now:
            # Force is manually requested but still capped at 5 min between calls.
            if not force or (state.last_attempt_at and
                             state.last_attempt_at > now - timedelta(minutes=5)):
                return "not_due"
        state.last_attempt_at = now
        # Lease keeps concurrent workers from hammering the endpoint.
        state.next_refresh_at = now + timedelta(minutes=15)
        state.save(update_fields=["last_attempt_at", "next_refresh_at"])
    try:
        data = (fetcher or list_models)(api_key)
        apply_discovery(data, now=now)
        return "refreshed"
    except DiscoveryError as exc:
        GeminiCatalogState.objects.filter(pk=1).update(
            last_error_code=exc.code,
            next_refresh_at=now + timedelta(minutes=RETRY_MINUTES),
        )
        logger.warning("Gemini model catalog refresh failed: %s", exc.code)
        return exc.code
