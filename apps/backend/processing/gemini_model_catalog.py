"""Fail-closed Gemini catalog refresh using Google's official models.list API.

Run only on the backend in an operator-approved environment. No API token is
embedded in URLs, CLI output, snapshots, or logs.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .gemini_model_policy import parse_model_catalog

MODELS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_PAGES = 20
MAX_RESPONSE = 2 * 1024 * 1024


def list_models(api_key: str, *, transport=urlopen) -> list[dict]:
    if not api_key or "\n" in api_key or "\r" in api_key:
        raise ValueError("missing_or_invalid_gemini_api_key")
    models = {}
    page_token = None
    for _ in range(MAX_PAGES):
        params = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token
        request = Request(
            MODELS_ENDPOINT + "?" + urlencode(params),
            headers={"x-goog-api-key": api_key, "Accept": "application/json"},
            method="GET",
        )
        try:
            with transport(request, timeout=20) as response:
                body = response.read(MAX_RESPONSE + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("gemini_catalog_unavailable") from exc
        if len(body) > MAX_RESPONSE:
            raise ValueError("gemini_catalog_response_too_large")
        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("invalid_gemini_catalog_response") from exc
        for model in parse_model_catalog(data):
            models[model["model_id"]] = model
        page_token = data.get("nextPageToken")
        if not page_token:
            return sorted(models.values(), key=lambda row: row["model_id"])
        if not isinstance(page_token, str) or len(page_token) > 2048:
            raise ValueError("invalid_gemini_page_token")
    raise ValueError("gemini_catalog_pagination_limit")


def snapshot(models: list[dict], previous: dict | None = None) -> dict:
    old = {item["model_id"]: item for item in (previous or {}).get("models", [])}
    new = {item["model_id"]: item for item in models}
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source": "Gemini REST models.list",
        "quota_information": "NOT_AVAILABLE_IN_MODELS_LIST",
        "candidates_require_verification": True,
        "models": models,
        "new_models": sorted(new.keys() - old.keys()),
        "removed_models": sorted(old.keys() - new.keys()),
        "changed_models": sorted(k for k in new.keys() & old.keys() if new[k] != old[k]),
    }


def update_catalog(output_path: Path, api_key: str) -> dict:
    previous = None
    if output_path.is_file():
        try:
            previous = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # Never erase the only known good state with an unreadable response.
            raise ValueError("existing_gemini_catalog_invalid")
    current = snapshot(list_models(api_key), previous)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent,
                                         prefix=".gemini-catalog-", delete=False) as temp:
            temp_name = temp.name
            os.chmod(temp_name, 0o600)
            json.dump(current, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(temp_name, output_path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return {k: current[k] for k in (
        "checked_at", "new_models", "removed_models", "changed_models", "quota_information"
    )}
