"""Discard platform engagement counters; retain substantive source text."""

import re

COUNTER = re.compile(
    r"^(?:[\d.,\s]+\s*(?:k|m|b|nghìn|ngàn|triệu|tỷ|thousand|million|billion)?\s+)(?:lượt xem|lượt thích|cảm xúc|lượt chia sẻ|bình luận|views?|likes?|reactions?|shares?|comments?)\s*$",
    re.IGNORECASE,
)
COUNTER_KEYS = {
    "view_count",
    "like_count",
    "reaction_count",
    "share_count",
    "comment_count",
    "repost_count",
    "views",
    "likes",
    "reactions",
    "shares",
    "comments",
}


def source_text(text):
    if not text:
        return text
    lines = []
    for line in text.splitlines():
        parts = [part.strip() for part in re.split(r"\s*[|·•]\s*", line)]
        kept = [part for part in parts if not COUNTER.fullmatch(part)]
        if len(kept) != len(parts):
            line = " | ".join(part for part in kept if part)
        if line.strip() or not COUNTER.fullmatch(text.strip()):
            lines.append(line)
    return "\n".join(lines).strip()


def source_metadata(value):
    if isinstance(value, dict):
        return {
            key: source_metadata(item)
            if key not in {"title", "description"}
            else source_text(item)
            if isinstance(item, str)
            else item
            for key, item in value.items()
            if key.casefold() not in COUNTER_KEYS
        }
    if isinstance(value, list):
        return [source_metadata(item) for item in value]
    return value
