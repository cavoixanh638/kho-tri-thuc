"""Literal numeric keys embedded in item text, extraction text and link annotations."""

import re


def _numeric_tokens(query):
    # A decimal, version or time separator belongs to the key only between
    # digits. A comma followed by whitespace still separates two numbers.
    tokens = re.findall(r"[^\W_]+(?:[-/][^\W_]+|(?<=\d)[.,:](?=\d)[^\W_]+)*", query)
    return [token for token in dict.fromkeys(tokens) if any(ch.isdigit() for ch in token)]


def remembered_code(query):
    """Index an explicitly supplied compound code even if the surrounding prose differs."""
    if len(query.split()) < 2 or "://" in query or any(ch in query for ch in '\\"“”@_#%'):
        return None
    codes = [token for token in _numeric_tokens(query)
             if len(token) >= 4 and ("-" in token or "/" in token) and any(ch.isalpha() for ch in token)]
    return max(codes, key=len, default=None)


def identifier_patterns(query):
    # PostgreSQL folds the pattern and source with the same Vietnamese rules.
    patterns = []
    for token in _numeric_tokens(query):
        # Administrative codes have a supported textual prefix, e.g.
        # 123/QD-UB finds 123/QĐ-UBND. A written number or year is complete.
        suffix = "[[:alpha:]]*" if token[0].isdigit() and "/" in token and token[-1].isalpha() else ""
        # \y is a word boundary and survives kt_search_fold's lowercasing.
        patterns.append(r"\y" + token.replace(".", "[.]") + suffix + r"\y")
    return patterns or None


def identifier_condition(source):
    """Check each numeric key on an already indexed candidate for this source."""
    return f"""(%(identifier_patterns)s::text[] IS NULL OR
        public.kt_search_fold({source}) ~ ALL (ARRAY(
            SELECT public.kt_search_fold(pattern)
            FROM unnest(%(identifier_patterns)s::text[]) AS keys(pattern)
        )))"""
