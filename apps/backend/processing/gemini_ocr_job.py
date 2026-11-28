"""Feature-gated Gemini image OCR in a separate, idempotent PostgreSQL job.

Never sends an unverified original or a user-authored note to the provider.
The real image is read only from the checksum-verified owner's Drive storage.
"""
import hashlib
import io
import warnings
from datetime import datetime
from uuid import UUID

from catalog.models import Item, RelatedItem
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from PIL import Image, ImageOps, UnidentifiedImageError
from storage.drive import DriveError
from storage.models import Asset, StorageLocation
from storage.service import storage_for_owner

from .gemini_ocr_client import (
    GeminiProviderError, MAX_IMAGE_BYTES, VERSION, generate_ocr,
)
from .gemini_routing import select_for_user
from .models import DerivedContent, GeminiCatalogState, GeminiPreference, GeminiUsageEvent

KIND = "gemini_image_ocr"
OCR_KIND = "image_ocr"
DESCRIPTION_KIND = "image_description"
ALLOWED_MIMES = {
    "image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp", "image/avif"
}
MAX_PIXELS = 24_000_000
MAX_SIDE = 3200


def _enabled():
    return bool(
        settings.GEMINI_OCR_ENABLED
        and settings.GEMINI_API_KEY
        and getattr(settings, "GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED", False)
    )


def _user_consented(owner_id):
    return GeminiPreference.objects.filter(
        owner_id=owner_id, external_ocr_consent=True
    ).exists()


def _job_key(asset):
    return "ocr:" + hashlib.sha256(
        f"{asset.pk}:{asset.sha256}:{VERSION}".encode("ascii")
    ).hexdigest()


def enqueue_image_ocr(asset):
    """Call only after owner Drive verifies the original; manual opt-in only."""
    if (not _enabled() or not _user_consented(asset.item.owner_id)
            or asset.role != "original" or asset.item.deleted_at
            or asset.mime not in ALLOWED_MIMES
            or not asset.sha256 or not asset.size
            or asset.size > MAX_IMAGE_BYTES
            or not asset.locations.filter(
                provider="google_drive", status=StorageLocation.Status.VERIFIED
            ).exists()):
        return False
    JobRepository.enqueue(
        kind=KIND, idempotency_key=_job_key(asset), item=asset.item,
        input_ref={"asset_id": str(asset.pk), "input_hash": asset.sha256},
    )
    return True


def _checked_image_bytes(asset):
    try:
        body = storage_for_owner(asset.item.owner_id).read_range(
            asset, 0, asset.size - 1
        )
    except DriveError as exc:
        raise JobFailure(exc.code, retryable=exc.retryable) from None
    except (OSError, ValueError):
        raise JobFailure("ocr_source_unavailable") from None
    if len(body) != asset.size or hashlib.sha256(body).hexdigest() != asset.sha256:
        raise JobFailure("ocr_source_checksum_mismatch", retryable=False)
    return body


def _prepare_image(original):
    """Decode once and strip EXIF/metadata before sending an image to Gemini."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(original)) as image:
                if image.width < 1 or image.height < 1 or image.width * image.height > MAX_PIXELS:
                    raise ValueError("invalid_image_dimensions")
                image.seek(0)  # Animated files: intentionally process frame zero only.
                upright = ImageOps.exif_transpose(image)
                upright.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
                rgb = upright.convert("RGB")
                output = io.BytesIO()
                rgb.save(output, format="PNG", optimize=True)
                payload, mime = output.getvalue(), "image/png"
                if len(payload) > MAX_IMAGE_BYTES:
                    output = io.BytesIO()
                    rgb.save(output, format="JPEG", quality=90, optimize=True)
                    payload, mime = output.getvalue(), "image/jpeg"
                if not 0 < len(payload) <= MAX_IMAGE_BYTES:
                    raise ValueError("normalized_image_too_large")
                return payload, mime
    except (OSError, ValueError, OverflowError, UnidentifiedImageError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise JobFailure("invalid_ocr_image", retryable=False) from None


def _active_lease(job):
    if not JobRepository._active_lease(job).exists():
        raise JobFailure("ocr_lease_lost", retryable=False)


def _scope(job):
    try:
        asset = Asset.objects.select_related("item").get(
            pk=UUID(job.input_ref["asset_id"]),
            item_id=job.item_id, item__deleted_at__isnull=True,
            role="original",
        )
        if job.input_ref["input_hash"] != asset.sha256:
            raise ValueError("hash changed")
    except (KeyError, TypeError, ValueError, AttributeError, Asset.DoesNotExist):
        raise JobFailure("invalid_ocr_job", retryable=False) from None
    if asset.mime not in ALLOWED_MIMES or not asset.size or asset.size > MAX_IMAGE_BYTES:
        raise JobFailure("unsupported_ocr_asset", retryable=False)
    if not asset.locations.filter(
        provider="google_drive", status=StorageLocation.Status.VERIFIED
    ).exists():
        raise JobFailure("ocr_original_not_verified", retryable=True)
    return asset


def _existing(asset, model):
    return DerivedContent.objects.filter(
        asset=asset, kind=OCR_KIND, status=DerivedContent.Status.ACTIVE,
        input_hash=asset.sha256, processor_version=VERSION,
        source_locator__model_id=model,
    ).exists()


def _reserve(owner, asset=None):
    """Atomic project-wide *local* request cap, never provider quota remaining."""
    with transaction.atomic():
        GeminiCatalogState.objects.get_or_create(pk=1)
        GeminiCatalogState.objects.select_for_update().get(pk=1)
        selection = select_for_user(
            owner, task="ocr_simple",
            allowed_models=getattr(settings, "GEMINI_OCR_APPROVED_MODELS", frozenset()),
        )
        model = selection["model"]
        if model and model not in getattr(settings, "GEMINI_OCR_APPROVED_MODELS", frozenset()):
            raise JobFailure("ocr_model_not_validated", retryable=False)
        if not model:
            reason = selection["reason"]
            # Only the operator can approve a model, enable paid use or clear
            # a provider billing/project budget block.
            safe = "ocr_local_budget_limit" if reason == "local_daily_budget_limit" else (
                "ocr_model_unavailable"
            )
            raise JobFailure(safe, retryable=False)
        if asset is not None and _existing(asset, model):
            return model, None
        event = GeminiUsageEvent.objects.create(
            owner=owner, model_id=model, task="ocr_simple", status="reserved"
        )
    return model, event


def _settle_usage(event, *, status, result=None, error_code=""):
    GeminiUsageEvent.objects.filter(pk=event.pk, status="reserved").update(
        status=status,
        input_tokens=result.input_tokens if result else 0,
        output_tokens=result.output_tokens if result else 0,
        provider_error_code=error_code[:40],
    )


def _save(job, asset, model, result):
    with transaction.atomic():
        if not JobRepository._active_lease(job).select_for_update().exists():
            raise JobFailure("ocr_lease_lost", retryable=False)
        item = Item.objects.select_for_update().get(pk=asset.item_id)
        if item.deleted_at:
            return
        if _existing(asset, model):
            return
        # OCR/visual descriptions are separate from human-authored notes.
        DerivedContent.objects.filter(
            asset=asset, kind__in=[OCR_KIND, DESCRIPTION_KIND],
            status=DerivedContent.Status.ACTIVE,
        ).update(status=DerivedContent.Status.STALE)
        locator = {
            "asset_id": str(asset.pk), "model_id": model,
            "provider_model_version": result.model_version,
            "input_sha256": asset.sha256,
            "review_required": True,
            "image_frame": 0,
        }
        for kind, text in [(OCR_KIND, result.text), (DESCRIPTION_KIND, result.description)]:
            DerivedContent.objects.create(
                item=item, asset=asset, kind=kind, text=text,
                source_locator=locator, processor="gemini-image",
                processor_version=VERSION, input_hash=asset.sha256,
            )
        # Already stored image metadata is kept in the separate Item fields.
        if result.text.strip():
            Item.objects.filter(pk=item.pk).update(content_extract="done")
        elif result.description.strip():
            Item.objects.filter(pk=item.pk).update(content_extract="partial")
        elif not DerivedContent.objects.filter(item=item, status="active").exclude(text="").exists():
            Item.objects.filter(pk=item.pk).update(content_extract="not_available")
        RelatedItem.objects.filter(
            Q(item_a=item) | Q(item_b=item), status=RelatedItem.Status.ACTIVE
        ).update(status=RelatedItem.Status.STALE)
        classify_key = "ocr-classify:" + hashlib.sha256(
            f"{asset.pk}:{asset.sha256}:{VERSION}:{model}".encode()
        ).hexdigest()
        JobRepository.enqueue(
            kind="organize", idempotency_key=classify_key,
            item=item, input_ref={"item_id": str(item.pk)},
        )


def process_image_ocr(job):
    """One model/attempt; no automatic provider hopping or unbounded retries."""
    _active_lease(job)
    if not _enabled():
        raise JobFailure("ocr_not_enabled", retryable=False)
    asset = _scope(job)
    if not _user_consented(asset.item.owner_id):
        raise JobFailure("ocr_consent_required", retryable=False)
    # Do not call Gemini (or reserve paid use) if same model already produced
    # current OCR. Choose from the approved catalog again after reading bytes.
    original = _checked_image_bytes(asset)
    normalized, mime = _prepare_image(original)
    _active_lease(job)
    # A model-specific 429 may justify ONE alternative model for Auto modes.
    # Unknown/project-wide 429 or Manual mode must NEVER hop models.
    from .models import GeminiPreference
    preference = GeminiPreference.objects.filter(owner_id=asset.item.owner_id).first()
    auto = preference is None or preference.mode != "manual"
    for index in range(2 if auto else 1):
        model, event = _reserve(asset.item.owner, asset=asset)
        if event is None:
            return
        try:
            result = generate_ocr(
                api_key=settings.GEMINI_API_KEY, model_id=model,
                image=normalized, mime_type=mime,
            )
        except GeminiProviderError as exc:
            _settle_usage(event, status=exc.status, error_code=exc.code)
            if auto and index == 0 and exc.status == "model_rate_limit":
                continue
            raise JobFailure(exc.code, retryable=exc.retryable) from None
        except Exception:
            _settle_usage(event, status="error", error_code="unexpected_response")
            raise JobFailure("gemini_ocr_unavailable", retryable=False) from None
        _settle_usage(event, status="success", result=result)
        _save(job, asset, model, result)
        return
