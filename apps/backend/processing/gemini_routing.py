"""User-facing model selector. Local usage does NOT equal remaining Google quota."""
from datetime import datetime, timedelta, timezone as utc_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .gemini_policy import choose_model
from .models import GeminiModelCatalog, GeminiPreference, GeminiUsageEvent

PACIFIC = ZoneInfo("America/Los_Angeles")


def pacific_day_start(now=None):
    now = now or timezone.now()
    local = now.astimezone(PACIFIC)
    return datetime(local.year, local.month, local.day, tzinfo=PACIFIC).astimezone(
        utc_timezone.utc
    )


def local_usage_snapshot(now=None):
    now = now or timezone.now()
    today = pacific_day_start(now)
    observed = GeminiUsageEvent.objects.filter(created_at__gte=today)
    return {
        "today_local_requests": observed.count(),
        "today_input_tokens": observed.aggregate(total=Sum("input_tokens"))["total"] or 0,
        "today_output_tokens": observed.aggregate(total=Sum("output_tokens"))["total"] or 0,
        "observed_since": today.isoformat(),
        "provider_remaining_requests": None,
        "provider_remaining_tokens": None,
        "remaining_is_estimate": False,
        "limits_source": "Google AI Studio Rate Limits (project-specific)",
    }


def select_for_user(user, *, task="ocr_simple", now=None):
    """A conservative candidate, never a quota guarantee or billable call."""
    now = now or timezone.now()
    if not settings.GEMINI_API_KEY:
        return {"model": None, "reason": "provider_not_configured", "quota": "unknown"}
    if not settings.GEMINI_OCR_ENABLED:
        return {"model": None, "reason": "ocr_not_enabled", "quota": "unknown"}
    daily = GeminiUsageEvent.objects.filter(created_at__gte=pacific_day_start(now))
    # Billing/prepay exhaustion may persist longer than a single day; fail
    # closed until an operator reviews and explicitly clears the block.
    if GeminiUsageEvent.objects.filter(status="billing_exhausted").exists():
        return {"model": None, "reason": "billing_requires_review", "quota": "unknown"}
    # Unknown project-wide quota is not proof another model has free headroom.
    if daily.filter(status="project_quota").exists():
        return {"model": None, "reason": "project_limit_or_billing", "quota": "unknown"}
    if daily.count() >= settings.GEMINI_MAX_LOCAL_REQUESTS_PER_DAY:
        return {"model": None, "reason": "local_daily_budget_limit", "quota": "local_only"}
    preference = GeminiPreference.objects.filter(owner=user).first()
    mode = preference.mode if preference else "balanced"
    manual = preference.manual_model_id if preference else ""
    reviewed = {
        record.model_id: {
            "active": record.active,
            "reviewed": record.reviewed,
            "generation_methods": record.generation_methods,
        }
        for record in GeminiModelCatalog.objects.filter(reviewed=True)
    }
    cooldown = set(
        GeminiUsageEvent.objects.filter(
            created_at__gte=now - timedelta(minutes=10),
            status="model_rate_limit",
        ).values_list("model_id", flat=True)
    )
    tiers = ("economy", "balanced", "premium") if settings.GEMINI_ALLOW_PREMIUM_MODELS else (
        "economy", "balanced"
    )
    result = choose_model(
        mode=mode, task=task, catalog=reviewed, manual_model=manual,
        cooldown=cooldown, allowed_tiers=tiers,
    )
    return {
        "model": result.model,
        "reason": result.reason,
        "fallback_candidates": result.candidates if mode != "manual" else (),
        "quota": result.quota_estimate,
    }


def record_observed_outcome(*, owner, model, task, status, input_tokens=0,
                            output_tokens=0, provider_error_code=""):
    """To be invoked by the future OCR request adapter on every call.

    Do not persist raw provider responses, API keys or content. Status values
    are coarse and must be classified conservatively by the request adapter.
    """
    safe = {"success", "model_rate_limit", "project_quota",
            "billing_exhausted", "provider_unavailable", "error"}
    if status not in safe:
        raise ValueError("invalid_status")
    if not isinstance(model, str) or len(model) > 128:
        raise ValueError("invalid_model")
    return GeminiUsageEvent.objects.create(
        owner=owner, model_id=model, task=task[:24], status=status,
        input_tokens=max(0, min(int(input_tokens), 2_147_483_647)),
        output_tokens=max(0, min(int(output_tokens), 2_147_483_647)),
        provider_error_code=provider_error_code[:40],
    )
