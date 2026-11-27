"""Literal numeric keys embedded in item text, extraction text and link annotations."""

import re
import unicodedata

from .quantities import DASH, RANGE_GAP, quantity_key_spans


ALNUM = r"[^\W_]"
CODE_DASH = "-‐‑‒–—−"
RANGE_END = r"[0-9]+(?:[.,:][0-9]+)?"
NUMERIC_RANGE = rf"{RANGE_END}{RANGE_GAP}{RANGE_END}"
# Punctuation joins two pieces of a key where a digit marks it as structured.
CONNECTOR = rf"(?:{DASH}|/|[.](?=\d)|(?<=\d)[.]|(?<=\d)[,:](?=\d))"
KEY_TOKEN = re.compile(
    rf"(?<![\w.,:/])(?:{NUMERIC_RANGE})(?![\w/]|[.,:]\d|{DASH}{ALNUM})"
    rf"|{ALNUM}+(?:{CONNECTOR}{ALNUM}+)*"
)
SQL_ALNUM = r"[[:alnum:]]"
SQL_SUFFIX = rf"(?![.,:/]{SQL_ALNUM}|{DASH}{SQL_ALNUM})"
SQL_PREFIX = r"(?<![[:alnum:]][.,:/])" + rf"(?<!{SQL_ALNUM}{DASH})"


def numeric_tokens(query):
    """Yield intact numeric keys and their positions in the query."""
    return (match for match in KEY_TOKEN.finditer(query) if any(ch.isdigit() for ch in match[0]))


def remembered_code(query):
    """Index an explicitly supplied compound code even if the surrounding prose differs."""
    if len(query.split()) < 2 or "://" in query or any(ch in query for ch in '\\"“”@_#%'):
        return None
    codes = [token for match in numeric_tokens(query) if len(token := match[0]) >= 4
             and any(char in token for char in CODE_DASH + "/") and any(ch.isalpha() for ch in token)]
    return max(codes, key=len, default=None)


def identifier_patterns(query):
    # PostgreSQL folds the pattern and source with the same Vietnamese rules.
    query = unicodedata.normalize("NFC", query)
    quantities = list(quantity_key_spans(query))
    patterns = []
    for match in numeric_tokens(query):
        if any(start <= match.start() and match.end() <= end for start, end in quantities):
            continue
        token = match[0]
        # Administrative codes have a supported textual prefix, e.g.
        # 123/QD-UB finds 123/QĐ-UBND. A written number or year is complete.
        suffix = "[[:alpha:]]*" if token[0].isdigit() and "/" in token and token[-1].isalpha() else ""
        if re.fullmatch(NUMERIC_RANGE, token):
            first, last = re.split(rf"{RANGE_GAP}", token, maxsplit=1)
            key = first.replace(".", "[.]") + RANGE_GAP + last.replace(".", "[.]")
        else:
            key = "".join(DASH if char in CODE_DASH else "[.]" if char == "." else char for char in token)
        if any(char in token for char in CODE_DASH + "/.,:"):
            key = SQL_PREFIX + key + suffix + SQL_SUFFIX
        # \y is a word boundary and survives kt_search_fold's lowercasing.
        patterns.append(r"\y" + key + r"\y")
    return list(dict.fromkeys(patterns)) or None


def identifier_condition(source):
    """Check each numeric key on an already indexed candidate for this source."""
    return f"""(%(identifier_patterns)s::text[] IS NULL OR
        public.kt_search_fold({source}) ~ ALL (ARRAY(
            SELECT public.kt_search_fold(pattern)
            FROM unnest(%(identifier_patterns)s::text[]) AS keys(pattern)
        )))"""
