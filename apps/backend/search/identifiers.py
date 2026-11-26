"""Literal numeric keys embedded in item text, extraction text and link annotations."""

import re


def identifier_patterns(query):
    # Only letters, digits and the two code separators can enter a pattern.
    # PostgreSQL folds the pattern and source with the same Vietnamese rules.
    tokens = re.findall(r"[^\W_]+(?:[-/][^\W_]+)*", query)
    patterns = []
    for token in dict.fromkeys(tokens):
        if not any(character.isdigit() for character in token):
            continue
        # Administrative codes have a supported textual prefix, e.g.
        # 123/QD-UB finds 123/QĐ-UBND. A written number or year is complete.
        suffix = "[[:alpha:]]*" if token[0].isdigit() and "/" in token and token[-1].isalpha() else ""
        # \y is a word boundary and survives kt_search_fold's lowercasing.
        patterns.append(r"\y" + token + suffix + r"\y")
    return patterns or None


def identifier_condition(source):
    """Check each numeric key on an already indexed candidate for this source."""
    return f"""(%(identifier_patterns)s::text[] IS NULL OR
        public.kt_search_fold({source}) ~ ALL (ARRAY(
            SELECT public.kt_search_fold(pattern)
            FROM unnest(%(identifier_patterns)s::text[]) AS keys(pattern)
        )))"""
