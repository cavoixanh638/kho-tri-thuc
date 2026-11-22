"""Authenticated Gemini model catalogue and preference UI.

Read uses only cached provider metadata. User cannot insert arbitrary model
names or trigger remote paid calls. Only staff can trigger an early refresh.
"""
from typing import Literal

from django.conf import settings
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from .gemini_catalog import refresh_if_due
from .gemini_policy import MODEL_PROFILES
from .gemini_routing import local_usage_snapshot, select_for_user
from .models import GeminiCatalogState, GeminiModelCatalog, GeminiPreference

router = Router(auth=django_auth, tags=["Gemini model discovery"])


def _view_model(row):
    known = MODEL_PROFILES.get(row.model_id)
    return {
        "model_id": row.model_id,
        "display_name": row.label,
        "reviewed_for_ocr": row.reviewed,
        "listed_in_last_snapshot": row.active,
        "generation_supported": "generateContent" in row.generation_methods,
        "category": known["tier"] if known else "unreviewed",
        "input_token_limit": row.input_token_limit,
        "output_token_limit": row.output_token_limit,
        "last_seen_at": row.last_seen_at.isoformat(),
        "quota_remaining": None,
        "quota_status": "unknown",
    }


@router.get("/integrations/gemini/models", response={200: dict})
def get_models(request):
    state = GeminiCatalogState.objects.filter(pk=1).first()
    preference, _ = GeminiPreference.objects.get_or_create(owner=request.user)
    rows = list(GeminiModelCatalog.objects.order_by(
        "-reviewed", "-active", "model_id"
    )[:200])
    selected = select_for_user(request.user, task="ocr_simple")
    return {
        "configured": bool(settings.GEMINI_API_KEY),
        "ocr_enabled": bool(settings.GEMINI_OCR_ENABLED),
        "external_processing_allowed": bool(getattr(settings, "GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED", False)),
        "external_ocr_consent": preference.external_ocr_consent,
        "premium_models_enabled": bool(settings.GEMINI_ALLOW_PREMIUM_MODELS),
        "refresh_hours": 12,
        "last_attempt_at": state.last_attempt_at.isoformat() if state and state.last_attempt_at else None,
        "last_success_at": state.last_success_at.isoformat() if state and state.last_success_at else None,
        "last_error_code": state.last_error_code if state else "",
        "new_models_last_scan": state.newly_discovered if state else 0,
        "mode": preference.mode,
        "manual_model_id": preference.manual_model_id,
        "automatic_candidate": selected["model"],
        "automatic_status": selected["reason"],
        "models": [_view_model(row) for row in rows],
        "usage": local_usage_snapshot(),
        "note": "models.list does not report quota remaining, OCR accuracy or pricing.",
    }


class PreferenceInput(Schema):
    mode: Literal["economy", "balanced", "quality", "manual"]
    manual_model_id: str = Field(default="", max_length=128)
    external_ocr_consent: bool | None = None


@router.post("/integrations/gemini/preferences", response={200: dict, 422: dict})
def update_preferences(request, payload: PreferenceInput):
    model_id = payload.manual_model_id.strip()
    if payload.mode == "manual":
        if not model_id:
            return Status(422, {"code": "manual_model_required"})
        target = GeminiModelCatalog.objects.filter(
            pk=model_id, reviewed=True, active=True
        ).first()
        if not target or "generateContent" not in target.generation_methods:
            return Status(422, {"code": "model_not_reviewed_or_unavailable"})
        policy = MODEL_PROFILES.get(model_id)
        if not policy or (policy["tier"] == "premium"
                          and not settings.GEMINI_ALLOW_PREMIUM_MODELS):
            return Status(422, {"code": "model_not_allowed_by_cost_policy"})
    else:
        model_id = ""
    defaults = {"mode": payload.mode, "manual_model_id": model_id}
    if payload.external_ocr_consent is not None:
        defaults["external_ocr_consent"] = payload.external_ocr_consent
    preference, _ = GeminiPreference.objects.update_or_create(
        owner=request.user, defaults=defaults,
    )
    return {
        "mode": preference.mode,
        "manual_model_id": preference.manual_model_id,
        "external_ocr_consent": preference.external_ocr_consent,
        "effective_candidate": select_for_user(request.user)["model"],
    }


@router.post("/integrations/gemini/refresh", response={200: dict, 403: dict})
def manual_refresh(request):
    if not request.user.is_staff:
        return Status(403, {"code": "staff_required"})
    status = refresh_if_due(force=True)
    return {"refresh_status": status}

