"""Owner-scoped, bounded mixed explorer and explicit note structure."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Substr
from ingestion.services import CaptureSubmission, submit_capture

from .models import Item, ItemTopic, Topic

MAX_DEPTH = 64


class ExplorerError(ValueError):
    pass


def active_item(owner_id, item_id, *, lock=False):
    query = Item.objects.filter(owner_id=owner_id, deleted_at__isnull=True)
    if lock:
        query = query.select_for_update()
    try:
        return query.get(pk=item_id)
    except Item.DoesNotExist:
        raise ExplorerError("unknown_item") from None


def active_folder(owner_id, folder_id):
    if folder_id is None:
        return None
    try:
        return Topic.objects.get(pk=folder_id, owner_id=owner_id, archived=False)
    except Topic.DoesNotExist:
        raise ExplorerError("unknown_folder") from None


def lock_owner(owner_id):
    get_user_model().objects.select_for_update().only("pk").get(pk=owner_id)


def title(item):
    return (
        item.title
        or getattr(item, "excerpt", "").strip().split("\n")[0].lstrip("# ")
        or "Ghi chú chưa có tiêu đề"
    )


def summarize(item, folder_id=None, *, unfiled=False):
    live_parent = bool(item.parent_item_id and getattr(item, "parent_active", False))
    return {
        "item_id": str(item.pk),
        "title": title(item),
        "kind": item.kind,
        "home_topic_id": item.home_topic_id,
        "parent_item_id": str(item.parent_item_id) if item.parent_item_id else None,
        "sort_order": item.outline_order,
        "structure_version": item.structure_version,
        "child_count": getattr(item, "child_count", 0),
        "shortcut": bool(
            (folder_id is not None and (live_parent or item.home_topic_id != folder_id))
            or (unfiled and live_parent)
        ),
        "source_fetch": item.source_fetch,
        "asset_storage": item.asset_storage,
    }


def item_query(owner_id):
    live_parent = Item.objects.filter(
        pk=OuterRef("parent_item_id"), owner_id=owner_id, deleted_at__isnull=True
    )
    return (
        Item.objects.filter(owner_id=owner_id, deleted_at__isnull=True)
        .only(
            "id",
            "title",
            "kind",
            "home_topic_id",
            "parent_item_id",
            "outline_order",
            "structure_version",
            "source_fetch",
            "asset_storage",
        )
        .annotate(
            excerpt=Substr("note", 1, 120),
            parent_active=Exists(live_parent),
            child_count=Count(
                "structural_children",
                filter=Q(
                    structural_children__owner_id=owner_id,
                    structural_children__deleted_at__isnull=True,
                ),
                distinct=True,
            ),
        )
    )



def without_visible_folder(query, owner_id):
    """A note is unfiled only when it has no visible Topic placement.

    Structural note parents do not implicitly supply a folder. Archived
    memberships/home folders are invisible; active shortcuts still count.
    """
    placements = ItemTopic.objects.filter(
        item_id=OuterRef("pk"), topic__owner_id=owner_id, topic__archived=False
    )
    return (
        query.alias(_has_visible_placement=Exists(placements))
        .filter(_has_visible_placement=False)
        .exclude(home_topic__owner_id=owner_id, home_topic__archived=False)
    )


def children(
    owner_id, *, folder_id=None, parent_item_id=None, unfiled=False, offset=0, limit=50
):
    """One bounded folder-first stream; next_offset is across both node types."""
    if (parent_item_id is not None and (folder_id is not None or unfiled)) or (
        folder_id is not None and unfiled
    ):
        raise ExplorerError("invalid_scope")

    if parent_item_id is not None:
        parent = active_item(owner_id, parent_item_id)
        notes = item_query(owner_id).filter(parent_item_id=parent.pk)
        folders = Topic.objects.none()
    else:
        active_folder(owner_id, folder_id)
        folders = Topic.objects.filter(
            owner_id=owner_id, archived=False, parent_id=folder_id
        )
        notes = item_query(owner_id)
        if folder_id is not None:
            # A valid primary home must remain reachable even when a legacy
            # ItemTopic row is missing. Other memberships are shortcuts.
            notes = notes.filter(
                Q(itemtopic__topic_id=folder_id) | Q(home_topic_id=folder_id)
            )
        elif unfiled:
            folders = Topic.objects.none()
            notes = without_visible_folder(notes, owner_id)
        else:
            # Root contains canonical placements not under a live note parent.
            notes = notes.exclude(
                home_topic__owner_id=owner_id, home_topic__archived=False
            ).filter(parent_active=False)

    # Home-only legacy records and M:N shortcuts are counted once per Item.
    # The correlated count never loads bodies/Assets and is bounded by the
    # returned folder slice, not all children of the account.
    direct_items = (
        Item.objects.filter(owner_id=owner_id, deleted_at__isnull=True)
        .filter(
            Q(home_topic_id=OuterRef("pk"))
            | Q(itemtopic__topic_id=OuterRef("pk"))
        )
        .order_by()
        .values("owner_id")
        .annotate(total=Count("pk", distinct=True))
        .values("total")[:1]
    )
    folders = folders.annotate(
        direct_count=Coalesce(
            Subquery(direct_items, output_field=IntegerField()),
            0,
            output_field=IntegerField(),
        )
    ).order_by("sort_order", "name", "id")

    folder_total = folders.count()
    folder_end = min(offset + limit, folder_total)
    page_folders = list(folders[min(offset, folder_total) : folder_end])
    folder_rows = [
        {
            "id": row.pk,
            "name": row.name,
            "node_kind": row.node_kind,
            "parent_id": row.parent_id,
            "sort_order": row.sort_order,
            "direct_count": row.direct_count,
        }
        for row in page_folders
    ]

    remaining = limit - len(folder_rows)
    more_folders = folder_total > offset + len(folder_rows)
    rows = []
    more_notes = False
    if remaining:
        note_offset = max(0, offset - folder_total)
        rows = list(
            notes.distinct().order_by("outline_order", "id")[
                note_offset : note_offset + remaining + 1
            ]
        )
        more_notes = len(rows) > remaining
        rows = rows[:remaining]
    elif not more_folders:
        # A page ending exactly on the final folder still needs a cursor when
        # notes follow it; do not issue a phantom empty page otherwise.
        more_notes = notes.exists()

    returned = len(folder_rows) + len(rows)
    return {
        "folders": folder_rows,
        "folders_truncated": more_folders,
        "notes": [summarize(row, folder_id, unfiled=unfiled) for row in rows],
        "next_offset": offset + returned if more_folders or more_notes else None,
    }


def placement(item):
    memberships = list(
        ItemTopic.objects.filter(
            item=item, topic__owner_id=item.owner_id, topic__archived=False
        ).values("topic_id", "topic__name", "user_pinned")
    )
    return {
        "item_id": str(item.pk),
        "home_topic_id": item.home_topic_id,
        "structure_version": item.structure_version,
        "memberships": [
            {
                "folder_id": row["topic_id"],
                "name": row["topic__name"],
                "shortcut": row["topic_id"] != item.home_topic_id
                or item.parent_item_id is not None,
                "pinned": row["user_pinned"],
            }
            for row in memberships
        ],
    }


def set_home(item, folder):
    item.home_topic = folder
    if folder:
        ItemTopic.objects.update_or_create(
            item=item,
            topic=folder,
            defaults={
                "origin": "user",
                "user_pinned": True,
                "method_version": "explorer-home-v1",
            },
        )


@transaction.atomic
def place(owner_id, item_id, *, action, folder_id, expected_version):
    lock_owner(owner_id)
    item = active_item(owner_id, item_id, lock=True)
    if item.structure_version != expected_version:
        raise ExplorerError("structure_conflict")
    folder = active_folder(owner_id, folder_id)
    if action == "move":
        set_home(item, folder)
    elif action == "add" and folder:
        ItemTopic.objects.update_or_create(
            item=item,
            topic=folder,
            defaults={
                "origin": "user",
                "user_pinned": True,
                "method_version": "explorer-shortcut-v1",
            },
        )
    elif action == "remove" and folder:
        ItemTopic.objects.filter(item=item, topic=folder).delete()
        if item.home_topic_id == folder.pk:
            item.home_topic = None
    else:
        raise ExplorerError("invalid_placement")
    item.structure_version += 1
    item.structure_origin = "user"
    item.save(
        update_fields=[
            "home_topic",
            "structure_version",
            "structure_origin",
            "updated_at",
        ]
    )
    return placement(item)


def check_parent(owner_id, item, parent_id):
    current, seen, depth = parent_id, {item.pk}, 0
    while current is not None:
        if current in seen:
            raise ExplorerError("structure_cycle")
        seen.add(current)
        parent = active_item(owner_id, current)
        current = parent.parent_item_id
        depth += 1
        if depth >= MAX_DEPTH:
            raise ExplorerError("structure_depth")
    # A deep existing subtree must still fit after its root moves.
    frontier, visited, subtree_depth = [item.pk], set(), 0
    while frontier:
        if subtree_depth + depth >= MAX_DEPTH:
            raise ExplorerError("structure_depth")
        visited.update(frontier)
        frontier = list(
            Item.objects.filter(
                owner_id=owner_id, deleted_at__isnull=True, parent_item_id__in=frontier
            )
            .exclude(pk__in=visited)
            .values_list("pk", flat=True)
        )
        subtree_depth += 1


@transaction.atomic
def structure(owner_id, item_id, *, parent_item_id, sort_order, expected_version):
    lock_owner(owner_id)
    item = active_item(owner_id, item_id, lock=True)
    if item.structure_version != expected_version:
        raise ExplorerError("structure_conflict")
    check_parent(owner_id, item, parent_item_id)
    item.parent_item_id, item.outline_order = parent_item_id, sort_order
    item.structure_version += 1
    item.structure_origin = "user"
    item.save(
        update_fields=[
            "parent_item",
            "outline_order",
            "structure_version",
            "structure_origin",
            "updated_at",
        ]
    )
    return structure_info(owner_id, item.pk)


def structure_info(owner_id, item_id):
    item = active_item(owner_id, item_id)
    path, seen, current = [], set(), item
    while current.parent_item_id and len(path) < MAX_DEPTH:
        if current.parent_item_id in seen:
            break
        seen.add(current.parent_item_id)
        try:
            current = active_item(owner_id, current.parent_item_id)
        except ExplorerError:
            break
        path.append(
            {
                "item_id": str(current.pk),
                "title": current.title
                or current.note[:120].strip().split("\n")[0].lstrip("# ")
                or "Ghi chú",
            }
        )
    return {
        "item_id": str(item.pk),
        "parent_item_id": str(item.parent_item_id) if item.parent_item_id else None,
        "home_topic_id": item.home_topic_id,
        "sort_order": item.outline_order,
        "structure_version": item.structure_version,
        "origin": item.structure_origin,
        "ancestors": path[::-1],
        "children": children(owner_id, parent_item_id=item.pk)["notes"],
    }


def create_note(owner, *, text, title_text, home_topic_id, parent_item_id, key):
    try:
        title_text.encode("utf-8")
    except UnicodeEncodeError:
        raise ExplorerError("invalid_title") from None
    if "\x00" in title_text:
        raise ExplorerError("invalid_title")

    def locate(event):
        folder = active_folder(owner.pk, home_topic_id)
        item = event.item
        if parent_item_id:
            check_parent(owner.pk, item, parent_item_id)
            item.parent_item_id = parent_item_id
        set_home(item, folder)
        item.title = title_text
        item.save(update_fields=["home_topic", "parent_item", "title"])

    return submit_capture(
        owner,
        CaptureSubmission(kind="text", text=text, idempotency_key=key),
        on_created=locate,
    )
