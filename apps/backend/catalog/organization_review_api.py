"""Standalone KT129 router. G00 registers this router in config/api.py."""
from uuid import UUID
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from . import organization_review as service

router = Router(auth=django_auth, tags=["Organization review"])


class ReceiptInput(Schema):
    receipt: str = Field(min_length=1, max_length=8192)


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except service.ReviewError as error:
        return Status(error.status, {"code": error.code})


@router.get("/organization-review/queue", response={200: dict, 422: dict})
def queue(request, limit: int = 25, offset: int = 0):
    return _call(service.queue, request.user.pk, limit=limit, offset=offset)


@router.get("/items/{item_id}/organization-review", response={200: dict, 404: dict})
def preview(request, item_id: UUID):
    return _call(service.review, request.user.pk, item_id, request.session)


@router.post("/items/{item_id}/organization-review/{action}",
             response={200: dict, 404: dict, 409: dict, 422: dict})
def decision(request, item_id: UUID, action: str, payload: ReceiptInput):
    return _call(service.decide, request.user.pk, item_id, payload.receipt,
                 action, request.session)


@router.post("/items/{item_id}/organization-review/undo",
             response={200: dict, 404: dict, 409: dict, 422: dict})
def undo(request, item_id: UUID, payload: ReceiptInput):
    return _call(service.undo, request.user.pk, item_id,
                 payload.receipt, request.session)
