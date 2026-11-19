"""Read authored knowledge or current extracted source text with provenance."""

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
        parts, used, truncated = [], 0, False
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
                        "asset_id": part.asset_id,
                        "locator": part.source_locator
                        if isinstance(part.source_locator, dict)
                        else {},
                        "processor": part.processor,
                        "processor_version": part.processor_version,
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
