"""Read authored knowledge or current extracted source text with provenance."""

from catalog.models import Source

from .models import DerivedContent

TRANSCRIPTS = {
    "transcript",
    "video_transcript",
    "subtitle",
    "subtitles",
    "caption",
    "captions",
}
MAX_TEXT = 100_000


def source_evidence(part, item, sources):
    """Expose internal provenance, never provider IDs, preview URLs or credentials."""
    evidence = {
        "state": "unverified",
        "version": part.input_hash,
        "source_id": None,
        "source_url": None,
        "mime": None,
        "asset_version": None,
    }
    if part.asset_id:
        asset = part.asset
        if asset.item_id != item.pk:
            evidence.update(state="missing", version="")
            return evidence
        evidence.update(mime=asset.mime, asset_version=asset.content_version)
        if part.input_hash and asset.sha256 and part.input_hash != asset.sha256:
            evidence["state"] = "stale"
        elif not any(location.status == "verified" for location in asset.locations.all()):
            evidence["state"] = "missing"
        elif part.input_hash and asset.sha256:
            evidence["state"] = "current"
    else:
        locator = part.source_locator if isinstance(part.source_locator, dict) else {}
        source_id = locator.get("source_id")
        source = sources.get(source_id) if type(source_id) is int else None
        if source:
            evidence.update(
                state="current", source_id=source.pk, source_url=source.original_url
            )
        else:
            evidence["state"] = "missing"
    return evidence


class ReadKnowledgeService:
    def read(self, item):
        if item.note.strip():
            return {
                "origin": "authored",
                "text": item.note,
                "format": "markdown",
                "parts": [],
                "truncated": False,
                "needs_review": False,
            }
        query = DerivedContent.objects.filter(item=item, status="active").exclude(
            text=""
        )
        if query.filter(kind__in=TRANSCRIPTS).exists():
            query = query.filter(kind__in=TRANSCRIPTS)
        sources = {source.pk: source for source in Source.objects.filter(item=item)}
        parts, used, truncated = [], 0, False
        query = query.select_related("asset").prefetch_related("asset__locations")
        for part in query.order_by("asset_id", "created_at", "id")[:1001]:
            if len(parts) >= 1000 or used >= MAX_TEXT:
                truncated = True
                break
            text = part.text[: MAX_TEXT - used]
            truncated |= len(text) != len(part.text)
            used += len(text)
            if text.strip():
                parts.append(
                    {
                        "id": part.pk,
                        "kind": part.kind,
                        "text": text,
                        "asset_id": part.asset_id
                        if part.asset and part.asset.item_id == item.pk
                        else None,
                        "locator": part.source_locator
                        if isinstance(part.source_locator, dict)
                        else {},
                        "processor": part.processor,
                        "processor_version": part.processor_version,
                        "source": source_evidence(part, item, sources),
                        "format": "markdown"
                        if part.processor == "utf-8-markdown"
                        else "text",
                    }
                )
        return {
            "origin": "extracted" if parts else "missing",
            "text": "",
            "format": "text",
            "parts": parts,
            "truncated": truncated,
            "needs_review": any(
                part["processor"] == "faster-whisper" for part in parts
            ),
        }
