from uuid import UUID

from catalog.models import Item
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from jobs.models import Job
from ninja import Router, Schema
from ninja.security import django_auth

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
        queued = Job.objects.filter(
            item=item,
            kind__in=["fetch_source", "download_video", "upload_asset"],
            state__in=[Job.State.FAILED, Job.State.DONE],
        ).update(
            state=Job.State.RETRY,
            attempt=0,
            retry_at=timezone.now(),
            lease_token=None,
            lease_until=None,
            completed_at=None,
            error_code="",
        )
        if queued:
            if item.kind == Item.Kind.LINK:
                Item.objects.filter(pk=item.pk).update(source_fetch="pending")
            elif item.kind == Item.Kind.FILE:
                Item.objects.filter(pk=item.pk).exclude(
                    asset_storage="verified"
                ).update(asset_storage="pending")
    return {"queued": queued}
