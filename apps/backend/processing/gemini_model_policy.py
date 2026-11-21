"""Model discovery and deterministic Gemini OCR routing policy.

This module does not call inference, store API keys, or claim live quota
visibility. All actual Gemini calls must be routed by a separate adapter.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable


class SelectionMode(str, Enum):
    BALANCED = "balanced"
    QUALITY = "quality"
    ECONOMY = "economy"
    MANUAL = "manual"


@dataclass(frozen=True)
class ModelCandidate:
    model_id: str
    supports_image_input: bool
    supports_text_output: bool
    supported_actions: frozenset[str]
    stable: bool
    quality_score: float | None = None   # from evaluated Vietnamese OCR corpus
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    accessible: bool = False             # checked by actual eligible inference
    validated_at: datetime | None = None
    cooldown_until: datetime | None = None
    retired: bool = False


@dataclass(frozen=True)
class RouterPolicy:
    mode: SelectionMode = SelectionMode.BALANCED
    manual_model_id: str | None = None
    max_input_cost_per_million: float = 1.0
    max_output_cost_per_million: float = 5.0
    minimum_ocr_score: float = 0.90
    allow_preview: bool = False


def parse_model_catalog(payload: dict) -> list[dict]:
    """Parse a single paginated models.list response; never infer quotas here."""
    if not isinstance(payload, dict) or not isinstance(payload.get("models", []), list):
        raise ValueError("invalid_models_list")
    result = []
    for item in payload.get("models", []):
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        actions = item.get("supportedGenerationMethods") or item.get("supportedActions") or []
        if not isinstance(name, str) or not name.startswith("models/") or not isinstance(actions, list):
            continue
        model_id = name.removeprefix("models/")
        result.append({
            "model_id": model_id,
            "display_name": str(item.get("displayName", ""))[:128],
            "description": str(item.get("description", ""))[:500],
            "supported_actions": sorted(str(x) for x in actions if isinstance(x, str)),
            "input_token_limit": item.get("inputTokenLimit"),
            "output_token_limit": item.get("outputTokenLimit"),
        })
    return result


def eligible(candidate: ModelCandidate, policy: RouterPolicy, now: datetime) -> bool:
    if candidate.retired or not candidate.stable and not policy.allow_preview:
        return False
    if not (candidate.supports_image_input and candidate.supports_text_output
            and "generateContent" in candidate.supported_actions):
        return False
    if not candidate.accessible or candidate.quality_score is None:
        return False
    if candidate.validated_at is None or now - candidate.validated_at > timedelta(days=30):
        return False
    if candidate.cooldown_until and candidate.cooldown_until > now:
        return False
    return True


def select_model(models: Iterable[ModelCandidate], policy: RouterPolicy,
                 now: datetime | None = None) -> str | None:
    """Select only validated candidates. Never guess live remaining quotas.

    A 429 temporarily excludes a model via cooldown_until; a 404 should revoke
    accessible; insufficient local budget must be enforced by the caller before
    dispatch, not inferred from models.list.
    """
    now = now or datetime.now(timezone.utc)
    candidates = [m for m in models if eligible(m, policy, now)]
    if policy.mode == SelectionMode.MANUAL:
        return next((m.model_id for m in candidates if m.model_id == policy.manual_model_id), None)
    candidates = [
        m for m in candidates
        if m.quality_score >= policy.minimum_ocr_score
        and m.input_cost_per_million is not None
        and m.output_cost_per_million is not None
        and m.input_cost_per_million <= policy.max_input_cost_per_million
        and m.output_cost_per_million <= policy.max_output_cost_per_million
    ]
    if policy.mode == SelectionMode.QUALITY:
        candidates.sort(key=lambda m: (-m.quality_score, m.input_cost_per_million, m.model_id))
    elif policy.mode == SelectionMode.ECONOMY:
        candidates.sort(key=lambda m: (m.input_cost_per_million + m.output_cost_per_million,
                                        -m.quality_score, m.model_id))
    else:
        # Conservative blended score: measured quality dominates but cost
        # differentiates models near one another.
        candidates.sort(key=lambda m: (
            -(m.quality_score * 100 - m.input_cost_per_million - m.output_cost_per_million / 4),
            m.model_id,
        ))
    return candidates[0].model_id if candidates else None
