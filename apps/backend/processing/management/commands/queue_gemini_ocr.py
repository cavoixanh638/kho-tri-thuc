"""Review/enqueue verified images for Gemini OCR; dry run by default.

--execute never sends images itself. Worker jobs send images only after global
flags and each user's consent are still enabled.
"""
from django.core.management.base import BaseCommand, CommandError

from jobs.models import Job
from processing.gemini_ocr_job import (
    ALLOWED_MIMES, KIND, MAX_IMAGE_BYTES, _enabled, _job_key, _user_consented,
    enqueue_image_ocr,
)
from storage.models import Asset, StorageLocation


class Command(BaseCommand):
    help = "Review/enqueue verified image OCR jobs. Dry-run unless --execute."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true")
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= 500:
            raise CommandError("--limit must be between 1 and 500")
        if options["execute"] and not _enabled():
            raise CommandError("Gemini OCR global flags or API key are not enabled")
        images = (
            Asset.objects.filter(
                role="original", mime__in=ALLOWED_MIMES,
                size__gt=0, size__lte=MAX_IMAGE_BYTES,
                item__deleted_at__isnull=True,
                locations__provider="google_drive",
                locations__status=StorageLocation.Status.VERIFIED,
            )
            .select_related("item")
            .distinct().order_by("id")
        )
        sampled, eligible, queued = 0, 0, 0
        for asset in images.iterator(chunk_size=100):
            if sampled >= limit:
                break
            sampled += 1
            if not _user_consented(asset.item.owner_id):
                continue
            if Job.objects.filter(kind=KIND, idempotency_key=_job_key(asset)).exists():
                continue
            eligible += 1
            if options["execute"] and enqueue_image_ocr(asset):
                queued += 1
        self.stdout.write(
            f"scanned={sampled} eligible_with_user_consent={eligible} "
            f"queued={queued} mode={'execute' if options['execute'] else 'dry_run'}"
        )
