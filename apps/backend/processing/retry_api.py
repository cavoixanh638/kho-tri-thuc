from uuid import UUID

from catalog.models import Item
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from jobs.models import Job
from ninja import Router, Schema
from ninja.security import django_auth

from .transcript_job import enqueue_transcript

router = Router(auth=django_auth, tags=["Processing"])


class RetryReceipt(Schema):
    queued: int


@router.post("/items/{item_id}/retry", response=RetryReceipt)
def retry_item(request, item_id: UUID):
    with transaction.atomic():
        item = get_object_or_404(
            Item.objects.select_for_update(),
            pk=item_id,
            owner=request.user,
            deleted_at__isnull=True,
        )
        retryable_jobs = Job.objects.filter(
            item=item,
            kind__in=[
                "fetch_source",
                "download_video",
                "upload_asset",
                "transcribe_media",
            ],
            state__in=[Job.State.FAILED, Job.State.DONE],
        )
        source_retry = retryable_jobs.filter(
            kind__in=["fetch_source", "download_video"]
        ).exists()
        upload_retry = retryable_jobs.filter(kind="upload_asset").exists()
        queued = retryable_jobs.update(
            state=Job.State.RETRY,
            attempt=0,
            retry_at=timezone.now(),
            lease_token=None,
            lease_until=None,
            completed_at=None,
            error_code="",
        )
        # Existing uploaded media predates ASR enablement: enqueue without
        # downloading its source again or manufacturing a new capture event.
        for asset in item.assets.filter(role="original"):
            before = Job.objects.filter(item=item, kind="transcribe_media").count()
            pending = enqueue_transcript(asset)
            if (
                pending
                and Job.objects.filter(item=item, kind="transcribe_media").count()
                > before
            ):
                queued += 1
        if source_retry:
            Item.objects.filter(pk=item.pk).update(source_fetch="pending")
        if upload_retry:
            Item.objects.filter(pk=item.pk).exclude(asset_storage="verified").update(
                asset_storage="pending"
            )
    return {"queued": queued}
