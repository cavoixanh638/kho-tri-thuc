"""Feature-gated review API; no AI provider is configured or invoked."""

from dataclasses import asdict
from uuid import UUID

from django.conf import settings
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from . import suggestions

router = Router(auth=django_auth, tags=["Suggestion review PoC"])


class Preview(Schema):
    proposed_note: str = Field(max_length=100_000)


class Receipt(Schema):
    receipt: str = Field(max_length=2_000_000)


def review(request, item_id, action, payload):
    if not getattr(settings, "SUGGESTION_REVIEW_POC_ENABLED", False):
        return Status(404, {"code": "suggestion_review_not_enabled"})
    try:
        result = action(request.user.pk, item_id, payload)
        return (
            asdict(result) if isinstance(result, suggestions.ReviewResult) else result
        )
    except suggestions.SuggestionError as error:
        code = str(error)
        status = (
            404
            if code == "suggestion_item_unavailable"
            else 409
            if "conflict" in code or code == "suggestion_has_no_change"
            else 422
        )
        return Status(status, {"code": code})


@router.post(
    "/items/{item_id}/suggestions/preview",
    response={200: dict, 404: dict, 409: dict, 422: dict},
)
def preview(request, item_id: UUID, body: Preview):
    return review(request, item_id, suggestions.proposal, body.proposed_note)


@router.post(
    "/items/{item_id}/suggestions/accept",
    response={200: dict, 404: dict, 409: dict, 422: dict},
)
def accept(request, item_id: UUID, body: Receipt):
    return review(request, item_id, suggestions.accept, body.receipt)


@router.post(
    "/items/{item_id}/suggestions/reject",
    response={200: dict, 404: dict, 409: dict, 422: dict},
)
def reject(request, item_id: UUID, body: Receipt):
    return review(request, item_id, suggestions.reject, body.receipt)


@router.post(
    "/items/{item_id}/suggestions/undo",
    response={200: dict, 404: dict, 409: dict, 422: dict},
)
def undo(request, item_id: UUID, body: Receipt):
    return review(request, item_id, suggestions.undo, body.receipt)
