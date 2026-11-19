from typing import Literal

from django.db import DatabaseError
from ninja import NinjaAPI, Schema, Status

from catalog.api import router as library_router
from catalog.groups_api import router as groups_router
from ingestion.api import router as capture_router
from processing.content_api import router as content_router
from processing.knowledge_api import router as knowledge_router
from processing.retry_api import router as retry_router
from processing.thumbnail_api import router as thumbnail_router
from search.api import router as search_router
from storage.api import router as drive_router
from storage.uploads import router as upload_router

from .health import check_database

api = NinjaAPI(title="Kho Tri Thức", version="1.0.0")
api.add_router("/integrations/drive", drive_router)
api.add_router("", library_router)
api.add_router("", groups_router)
api.add_router("", search_router)
api.add_router("", capture_router)
api.add_router("", content_router)
api.add_router("", knowledge_router)
api.add_router("", retry_router)
api.add_router("", thumbnail_router)
api.add_router("/uploads", upload_router)


class HealthResponse(Schema):
    status: Literal["ready", "unavailable"]


@api.get("/health", response={200: HealthResponse, 503: HealthResponse})
def health(request):
    try:
        check_database()
    except DatabaseError:
        return Status(503, {"status": "unavailable"})

    return {"status": "ready"}
