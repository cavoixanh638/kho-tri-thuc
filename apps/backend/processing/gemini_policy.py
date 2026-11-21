"""Curated *input understanding* policy for Gemini. Not a generated-image selector.

The Google Models API lists generation methods and token limits, but does not
certify OCR quality, image input support or project quota availability.
New models must be independently reviewed before entering these profiles.
"""

from dataclasses import dataclass

# Last manually reviewed 2026-11-21; never infer ability from version alone.
# Price/capabilities must be rechecked in official docs on policy changes.
MODEL_PROFILES = {
    "gemini-3.5-flash-lite": {
        "label": "Gemini 3.5 Flash-Lite",
        "tier": "economy", "image_ocr": True, "preview": False,
        "tasks": ("ocr_simple", "ocr_complex", "tagging"),
        "reviewed": "2026-11-21",
    },
    "gemini-3.6-flash": {
        "label": "Gemini 3.6 Flash",
        "tier": "balanced", "image_ocr": True, "preview": False,
        "tasks": ("ocr_simple", "ocr_complex", "tagging"),
        "reviewed": "2026-11-21",
    },
    "gemini-3.8-flash": {
        "label": "Gemini 3.8 Flash",
        "tier": "premium", "image_ocr": True, "preview": False,
        "tasks": ("ocr_complex", "tagging"),
        "reviewed": "2026-11-21",
    },
}

# Higher power models are NEVER switched on just because models.list
# announces a bigger version number. Explicitly exclude image-generation
# models and TTS/Live/video-generation endpoints from OCR.
PROFILES = {
    "economy": {
        "ocr_simple": ("gemini-3.5-flash-lite",),
        "ocr_complex": ("gemini-3.5-flash-lite",),
        "tagging": ("gemini-3.5-flash-lite",),
    },
    "balanced": {
        "ocr_simple": ("gemini-3.5-flash-lite", "gemini-3.6-flash"),
        "ocr_complex": ("gemini-3.6-flash", "gemini-3.5-flash-lite"),
        "tagging": ("gemini-3.5-flash-lite", "gemini-3.6-flash"),
    },
    "quality": {
        "ocr_simple": ("gemini-3.6-flash", "gemini-3.5-flash-lite"),
        "ocr_complex": ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"),
        "tagging": ("gemini-3.6-flash", "gemini-3.5-flash-lite"),
    },
}


@dataclass(frozen=True)
class ModelChoice:
    model: str | None
    reason: str
    candidates: tuple[str, ...]
    quota_estimate: str = "unknown"  # Gemini Models API does not return remaining quota.


def choose_model(*, mode, task, catalog, manual_model="", cooldown=(),
                 allowed_tiers=("economy", "balanced"), allow_preview=False):
    """Select from reviewed capabilities in the *current* API catalog.

    catalog: mapping model ID -> {generation_methods:..., active:...}.
    Cooldown is a set of model IDs recently returning *model-specific* limits.
    This is a candidate decision, not a guarantee that the project has quota.
    """
    if mode not in {"economy", "balanced", "quality", "manual"}:
        return ModelChoice(None, "invalid_mode", ())
    if task not in {"ocr_simple", "ocr_complex", "tagging"}:
        return ModelChoice(None, "invalid_task", ())
    if mode == "manual":
        candidates = (manual_model,) if manual_model else ()
    else:
        candidates = PROFILES[mode][task]
    considered = []
    for model in candidates:
        profile = MODEL_PROFILES.get(model)
        if not profile or profile["tier"] not in allowed_tiers:
            continue
        if task not in profile["tasks"]:
            continue
        if profile["preview"] and not allow_preview:
            continue
        meta = catalog.get(model)
        if not meta or not meta.get("active") or not meta.get("reviewed"):
            continue
        if "generateContent" not in meta.get("generation_methods", ()):
            continue
        considered.append(model)
    for model in considered:
        if model not in cooldown:
            return ModelChoice(model, "reviewed_candidate", tuple(considered))
    return ModelChoice(None, "no_eligible_model_or_recent_rate_limit", tuple(considered))
