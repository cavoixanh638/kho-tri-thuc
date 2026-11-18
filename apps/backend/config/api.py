from typing import Literal

from django.db import DatabaseError
from ninja import NinjaAPI, Schema, Status

from .health import check_database

api = NinjaAPI(title="Kho Tri Thức", version="1.0.0")


class HealthResponse(Schema):
    status: Literal["ready", "unavailable"]


@api.get("/health", response={200: HealthResponse, 503: HealthResponse})
def health(request):
    try:
        check_database()
    except DatabaseError:
        return Status(503, {"status": "unavailable"})

    return {"status": "ready"}
