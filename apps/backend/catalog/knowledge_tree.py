"""Owner-scoped tree over existing Topics; one article can belong to several paths."""

import unicodedata

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import ItemTopic, Topic

MAX_NODES = 5000
MAX_DEPTH = 64


class TreeError(ValueError):
    pass


def owner_nodes(owner_id, *, archived=False):
    query = Topic.objects.filter(owner_id=owner_id)
    if not archived:
        query = query.filter(archived=False)
    rows = list(query.order_by("sort_order", "name", "id")[: MAX_NODES + 1])
    if len(rows) > MAX_NODES:
        raise TreeError("knowledge_tree_limit")
    return rows


def descendants(owner_id, node_id, *, archived=False):
    rows = owner_nodes(owner_id, archived=archived)
    children = {}
    for row in rows:
        children.setdefault(row.parent_id, []).append(row.pk)
    available = {row.pk for row in rows}
    if node_id not in available:
        return set()
    found, pending = set(), [node_id]
    while pending:
        current = pending.pop()
        if current not in found:
            found.add(current)
            pending.extend(children.get(current, []))
    return found


def tree(owner_id):
    rows = owner_nodes(owner_id)
    by_id = {row.pk: row for row in rows}
    paths = {}
    for row in rows:
        path, seen, current = [], set(), row
        while current is not None:
            if current.pk in seen or len(path) >= MAX_DEPTH:
                path = []
                break
            seen.add(current.pk)
            path.append(current.pk)
            if current.parent_id is None:
                break
            current = by_id.get(current.parent_id)
            if current is None:
                path = []
                break
        if path:
            paths[row.pk] = path[::-1]
    direct, totals = {pk: set() for pk in paths}, {pk: set() for pk in paths}
    for node_id, item_id in ItemTopic.objects.filter(
        topic_id__in=paths, item__owner_id=owner_id, item__deleted_at__isnull=True
    ).values_list("topic_id", "item_id"):
        direct[node_id].add(item_id)
        for ancestor in paths[node_id]:
            totals[ancestor].add(item_id)
    ordered = []
    children = {}
    for row in rows:
        if row.pk in paths:
            children.setdefault(row.parent_id, []).append(row)
    pending = list(reversed(children.get(None, [])))
    while pending:
        row = pending.pop()
        ids = paths[row.pk]
        ordered.append(
            {
                "id": row.pk,
                "parent_id": row.parent_id,
                "name": row.name,
                "node_kind": row.node_kind,
                "sort_order": row.sort_order,
                "depth": len(ids) - 1,
                "path_ids": ids,
                "path": " / ".join(by_id[pk].name for pk in ids),
                "direct_count": len(direct[row.pk]),
                "item_count": len(totals[row.pk]),
                "child_count": len(children.get(row.pk, [])),
            }
        )
        pending.extend(reversed(children.get(row.pk, [])))
    return ordered


@transaction.atomic
def save_node(owner_id, *, node_id=None, name, parent_id, node_kind, sort_order=0):
    get_user_model().objects.select_for_update().get(pk=owner_id)
    rows = owner_nodes(owner_id, archived=True)
    by_id = {row.pk: row for row in rows}
    node = by_id.get(node_id) if node_id is not None else None
    if node_id is not None and (node is None or node.archived):
        raise TreeError("unknown_knowledge_node")
    name = unicodedata.normalize("NFC", name.strip())
    if not name or len(name) > 120 or "\x00" in name:
        raise TreeError("invalid_group_name")
    try:
        name.encode()
    except UnicodeError as error:
        raise TreeError("invalid_group_name") from error
    if node_kind not in Topic.Kind.values or not 0 <= sort_order <= 1_000_000:
        raise TreeError("invalid_knowledge_node")
    path, seen, current = [], {node_id} if node_id is not None else set(), parent_id
    while current is not None:
        parent = by_id.get(current)
        if parent is None or parent.archived:
            raise TreeError("unknown_parent_node")
        if current in seen:
            raise TreeError("knowledge_tree_cycle")
        seen.add(current)
        path.append(current)
        current = parent.parent_id
        if len(path) >= MAX_DEPTH:
            raise TreeError("knowledge_tree_depth")
    if node:
        subtree = descendants(owner_id, node.pk, archived=True)
        for child in rows:
            if child.pk not in subtree:
                continue
            depth, parent = 1, child
            while parent.pk != node.pk:
                parent = by_id[parent.parent_id]
                depth += 1
            if len(path) + depth > MAX_DEPTH:
                raise TreeError("knowledge_tree_depth")
    for peer in rows:
        if (
            peer.pk != node_id
            and peer.parent_id == parent_id
            and unicodedata.normalize("NFC", peer.name).casefold() == name.casefold()
        ):
            if peer.archived:
                raise TreeError("group_archived")
            if node_id is None:
                return peer, False
            raise TreeError("knowledge_name_exists")
    if node is None:
        if len(rows) >= MAX_NODES:
            raise TreeError("knowledge_tree_limit")
        node = Topic(owner_id=owner_id)
    created = node.pk is None
    node.name, node.parent_id, node.node_kind, node.sort_order = (
        name,
        parent_id,
        node_kind,
        sort_order,
    )
    node.save()
    return node, created
