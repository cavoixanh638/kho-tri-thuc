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
        elif not any(
            location.status == "verified" for location in asset.locations.all()
        ):
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
            metadata = source.metadata if isinstance(source.metadata, dict) else {}
            fetch = metadata.get("fetch", {})
            fetch = fetch if isinstance(fetch, dict) else {}
            provenance = fetch.get("provenance", {})
            provenance = provenance if isinstance(provenance, dict) else {}
            previous_hash = locator.get("body_sha256")
            current_hash = provenance.get("body_sha256")
            if locator.get(
                "source_url", source.original_url
            ) != source.original_url or (
                previous_hash and current_hash and previous_hash != current_hash
            ):
                evidence["state"] = "stale"
            elif fetch.get("status") in {"not_found", "access_denied", "blocked"}:
                evidence["state"] = "missing"
            elif fetch.get("status") == "failed" or not part.input_hash:
                evidence["state"] = "unverified"
        else:
            evidence["state"] = "missing"
    return evidence


class ReadKnowledgeService:
    def read(self, item):
        # Authored Markdown is always authoritative. Source citations are a
        # separate, versioned layer; they must not disappear when a note exists.
        authored = bool(item.note.strip())
        query = DerivedContent.objects.filter(item=item, status="active").exclude(
            text=""
        )
        # Preserve the transcript-first reading policy only for unedited items.
        # An authored item needs evidence from *all* its PDF/ASR/web sources.
        if not authored and query.filter(kind__in=TRANSCRIPTS).exists():
            query = query.filter(kind__in=TRANSCRIPTS)
        sources = {source.pk: source for source in Source.objects.filter(item=item)}
        parts, used, truncated = [], 0, False
        query = query.select_related("asset").prefetch_related("asset__locations")
        for part in query.order_by("asset_id", "created_at", "id")[:1001]:
            locator = part.source_locator if isinstance(part.source_locator, dict) else {}
            # An unlinked extraction cannot substantiate an authored note.
            # Keep broken *linked* sources visible, with a missing/stale warning,
            # but do not mislabel an orphaned metadata row as a citation.
            if authored and not part.asset_id and type(locator.get("source_id")) is not int:
                continue
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
            "origin": "authored" if authored else ("extracted" if parts else "missing"),
            "text": item.note if authored else "",
            "format": "markdown" if authored else "text",
            "parts": parts,
            "truncated": truncated,
            # The curated note has already been authored. ASR citations still
            # carry their individual processor provenance for review in the UI.
            "needs_review": not authored and any(
                part["processor"] == "faster-whisper" for part in parts
            ),
        }
