import logging

from django.db import transaction
from django.db.models import Q

from catalog.models import Item, RelatedItem
from jobs.repository import JobRepository

from .document_extract import PROCESSOR_VERSION, extract_document
from .models import DerivedContent

logger = logging.getLogger(__name__)


def extract_from_staging(asset, path):
    """Preserve the original and persist only derived content from verified bytes."""
    existing = DerivedContent.objects.filter(
        asset=asset,
        input_hash=asset.sha256,
        processor_version=PROCESSOR_VERSION,
        kind="document_text",
        status=DerivedContent.Status.ACTIVE,
    )
    if existing.exists():
        return
    result = extract_document(path, mime=asset.mime, filename=asset.original_filename)
    with transaction.atomic():
        item = Item.objects.select_for_update().get(pk=asset.item_id)
        if existing.exists():
            return
        state = result["state"]
        Item.objects.filter(pk=item.pk).update(
            content_extract="not_available" if state == "encrypted" else state
        )
        parts = result["parts"]
        if not parts:
            return
        DerivedContent.objects.filter(
            asset=asset,
            kind="document_text",
            status=DerivedContent.Status.ACTIVE,
        ).update(status=DerivedContent.Status.STALE)
        DerivedContent.objects.bulk_create(
            [
                DerivedContent(
                    item=item,
                    asset=asset,
                    kind="document_text",
                    text=part["text"],
                    source_locator=part["locator"],
                    processor=result["processor"],
                    processor_version=PROCESSOR_VERSION,
                    input_hash=asset.sha256,
                )
                for part in parts
            ]
        )
        RelatedItem.objects.filter(
            Q(item_a=item) | Q(item_b=item),
            status=RelatedItem.Status.ACTIVE,
        ).update(status=RelatedItem.Status.STALE)
        JobRepository.enqueue(
            kind="organize",
            idempotency_key=f"asset:{asset.pk}:text:{asset.sha256}",
            item=item,
            input_ref={"item_id": str(item.pk)},
        )
