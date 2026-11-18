from uuid import UUID

from django.http import FileResponse, HttpResponseNotFound
from ninja import Router
from ninja.security import django_auth

from .thumbnail_integration import thumbnail_service, verified_assets_for

router = Router(auth=django_auth, tags=["Thumbnails"])


def _private(response):
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@router.get("/assets/{asset_id}/thumbnail")
def asset_thumbnail(request, asset_id: UUID):
    asset = verified_assets_for(request.auth.pk).filter(pk=asset_id).first()
    if asset is not None:
        try:
            service = thumbnail_service()
            cached = service.get_cached(asset.pk, asset.sha256) if service else None
            if cached and cached.path.resolve().is_relative_to(service.cache_root):
                return _private(
                    FileResponse(
                        cached.path.open("rb"), content_type=cached.content_type
                    )
                )
        except (OSError, ValueError):
            pass
    return _private(HttpResponseNotFound())
