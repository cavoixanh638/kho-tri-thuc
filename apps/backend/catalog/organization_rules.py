"""Deterministic evidence rules for existing groups and lexical relationships."""

import re
import unicodedata
from dataclasses import dataclass


def _fold(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.casefold()).replace("đ", "d")
        if not unicodedata.combining(char)
    )


def normalize_phrase(text: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", _fold(text)))


@dataclass(frozen=True)
class GroupEvidence:
    phrases: tuple[str, ...]
    declarations: frozenset[tuple[str, str]]

    @classmethod
    def from_texts(cls, note: str, texts: tuple[str, ...]):
        # Only the user's note can make an explicit declaration.
        declarations = set()
        for line in note.splitlines():
            label, colon, value = line.partition(":")
            if colon:
                declarations.add((_fold(label.strip()), normalize_phrase(value)))
        return cls(
            tuple(f" {normalize_phrase(text)} " for text in texts),
            frozenset(declarations),
        )

    def supports(self, group_type: str, phrase: str) -> bool:
        if not phrase:
            return False
        aliases = {
            "project": ("project", "du an"),
            "topic": ("topic", "chu de"),
            "tag": ("tag", "nhan"),
        }
        if any((label, phrase) in self.declarations for label in aliases[group_type]):
            return True
        # A shared keyword or a name in fetched content is insufficient for a project.
        # Single-word Topic/Tag names require a declaration to limit incidental matches.
        return (
            group_type != "project"
            and " " in phrase
            and any(f" {phrase} " in text for text in self.phrases)
        )


@dataclass(frozen=True)
class LexicalSimilarity:
    """Thresholds must come from the caller's quality evaluation before production use."""

    min_shared_tokens: int
    min_similarity: float

    def __post_init__(self):
        if self.min_shared_tokens < 1 or not 0 < self.min_similarity <= 1:
            raise ValueError("Expected a positive token count and similarity in (0, 1]")

    def match(
        self,
        left: tuple[tuple[str, frozenset[str]], ...],
        right: tuple[tuple[str, frozenset[str]], ...],
    ) -> tuple[str, float] | None:
        best = None
        best_rank = (0.0, 0)
        for left_label, left_tokens in left:
            for right_label, right_tokens in right:
                shared = len(left_tokens & right_tokens)
                if shared < self.min_shared_tokens:
                    continue
                confidence = shared / len(left_tokens | right_tokens)
                rank = (confidence, shared)
                if confidence >= self.min_similarity and rank > best_rank:
                    best_rank = rank
                    reason = (
                        f"Trùng {shared} từ sau chuẩn hóa "
                        f"({left_label} ↔ {right_label})."
                    )
                    best = reason, confidence
        return best


def lexical_fields(
    parts: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, frozenset[str]], ...]:
    return tuple((label, frozenset(normalize_phrase(text).split())) for label, text in parts)
