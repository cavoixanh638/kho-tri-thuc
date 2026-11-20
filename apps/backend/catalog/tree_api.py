from typing import Literal

from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from .knowledge_tree import TreeError, save_node, tree
from .models import Topic

router = Router(tags=["Knowledge tree"], auth=django_auth)


class NodeInput(Schema):
    name: str = Field(min_length=1, max_length=120)
    parent_id: int | None = Field(default=None, ge=1)
    node_kind: Literal["library", "field", "series", "book", "chapter", "folder"] = (
        "folder"
    )
    sort_order: int = Field(default=0, ge=0, le=1_000_000)


class Node(NodeInput):
    id: int
    depth: int
    path_ids: list[int]
    path: str
    direct_count: int
    item_count: int
    child_count: int


class Tree(Schema):
    nodes: list[Node]


class Error(Schema):
    code: str


@router.get("/knowledge-tree", response=Tree)
def read_tree(request):
    return {"nodes": tree(request.user.pk)}


@router.post("/knowledge-tree", response={200: Node, 201: Node, 422: Error})
def create_node(request, payload: NodeInput):
    try:
        node, created = save_node(request.user.pk, **payload.model_dump())
    except TreeError as error:
        return Status(422, {"code": str(error)})
    result = next(row for row in tree(request.user.pk) if row["id"] == node.pk)
    return Status(201 if created else 200, result)


@router.patch("/knowledge-tree/{node_id}", response={200: Node, 422: Error})
def change_node(request, node_id: int, payload: NodeInput):
    get_object_or_404(Topic, pk=node_id, owner=request.user, archived=False)
    try:
        save_node(request.user.pk, node_id=node_id, **payload.model_dump())
    except TreeError as error:
        return Status(422, {"code": str(error)})
    return next(row for row in tree(request.user.pk) if row["id"] == node_id)
