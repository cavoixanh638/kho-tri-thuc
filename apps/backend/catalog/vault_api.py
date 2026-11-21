"""Self-contained P02 Ninja router. G00 mounts it in config/api.py after review."""

import json

from django.http import HttpResponse
from ninja import File, Form, Router, Status
from ninja.files import UploadedFile
from ninja.security import django_auth

from .vault import MAX_ZIP, VaultError, apply_import, export_vault, preview_import

router = Router(tags=["Portable Markdown vault"], auth=django_auth)


def _archive(file: UploadedFile) -> bytes:
    if file.size > MAX_ZIP:
        raise VaultError("vault_archive_limit")
    raw = file.read(MAX_ZIP + 1)
    if len(raw) > MAX_ZIP:
        raise VaultError("vault_archive_limit")
    return raw


def _failure(error: VaultError):
    code = str(error)
    status = (
        413 if code in ("vault_archive_limit", "vault_expanded_limit", "zip_bomb_or_file_limit")
        else 409 if any(word in code for word in ("conflict", "scope_mismatch", "database_changed", "expired"))
        else 422
    )
    return Status(status, {"code": code})


@router.get("/vault/export", response={200: None, 413: dict, 422: dict})
def export_archive(request):
    try:
        body = export_vault(request.user)
    except VaultError as error:
        return _failure(error)
    response = HttpResponse(body, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="kho-tri-thuc-vault.zip"'
    response["Cache-Control"] = "no-store, private"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@router.post("/vault/import/preview", response={200: dict, 413: dict, 422: dict})
def preview_archive(request, file: File[UploadedFile]):
    try:
        return preview_import(request.user, _archive(file))
    except VaultError as error:
        return _failure(error)


@router.post("/vault/import", response={200: dict, 409: dict, 413: dict, 422: dict})
def import_archive(
    request, file: File[UploadedFile], receipt: Form[str], selected: Form[str],
):
    try:
        try:
            keys = json.loads(selected)
        except (ValueError, TypeError):
            raise VaultError("invalid_vault_selection") from None
        return apply_import(request.user, _archive(file), receipt, keys)
    except VaultError as error:
        return _failure(error)
