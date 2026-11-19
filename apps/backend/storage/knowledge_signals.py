"""Only opted-in projections are queued; user edits and originals stay untouched."""

import logging

from catalog.models import (
    Item,
    ItemProject,
    ItemTag,
    ItemTopic,
    Project,
    Source,
    Tag,
    Topic,
)
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from ingestion.models import CaptureEvent
from processing.models import DerivedContent

from .models import Asset, KnowledgeExport, StorageLocation

logger = logging.getLogger(__name__)


def changed(sender, instance, **kwargs):
    if kwargs.get("raw") or kwargs.get("using", "default") != "default":
        return
    if sender is Item:
        ids = [instance.pk]
    elif sender is StorageLocation:
        ids = list(
            Asset.objects.filter(pk=instance.asset_id).values_list("item_id", flat=True)
        )
    elif sender in (Topic, Project, Tag):
        from catalog.knowledge_tree import descendants

        relation = {
            Topic: (ItemTopic, "topic"),
            Project: (ItemProject, "project"),
            Tag: (ItemTag, "tag"),
        }[sender]
        ids = list(
            relation[0]
            .objects.filter(
                **{
                    relation[1] + "_id__in": descendants(
                        instance.owner_id, instance.pk, archived=True
                    )
                    if sender is Topic
                    else [instance.pk]
                }
            )
            .values_list("item_id", flat=True)
        )
    else:
        ids = [instance.item_id]
    # Keep ordinary writes cheap: the pilot has at most ten enabled records.
    ids = list(
        KnowledgeExport.objects.filter(item_id__in=ids).values_list(
            "item_id", flat=True
        )
    )
    for item_id in ids:

        def queue(item_id=item_id):
            from processing.knowledge_sync import request_sync

            try:
                request_sync(item_id)
            except Exception:  # noqa: BLE001 - user transaction already committed; no private error details
                logger.warning("Knowledge sync queue unavailable")

        transaction.on_commit(queue)


for model in (
    Item,
    Source,
    Asset,
    StorageLocation,
    DerivedContent,
    CaptureEvent,
    ItemTopic,
    ItemProject,
    ItemTag,
    Topic,
    Project,
    Tag,
):
    post_save.connect(
        changed, sender=model, dispatch_uid=f"knowledge-save-{model._meta.label}"
    )
    post_delete.connect(
        changed, sender=model, dispatch_uid=f"knowledge-delete-{model._meta.label}"
    )
