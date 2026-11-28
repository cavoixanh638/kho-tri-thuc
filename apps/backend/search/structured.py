"""Choose indexed lexical probes for a literal quote or a written value.

The original source predicates still verify every value before pagination.
Only surrounding prose is eligible to form a less restrictive lookup.
"""

import math
import re
import unicodedata
from itertools import product

from .claims import _fold
from .identifiers import CODE_DASH, numeric_tokens
from .quantities import COUNT, DATE_KEY, MEASUREMENT, quantity_key_spans
from .recall import QUESTION_WORDS


# Fold width variants only. General compatibility normalization would also
# turn square units and superscript digits into different quantities.
ASCII_GRAPHIC = "".join(chr(n) for n in range(33, 127))
WIDE_GRAPHIC = "".join(chr(n + 0xFEE0) for n in range(33, 127))
TO_ASCII = str.maketrans(WIDE_GRAPHIC, ASCII_GRAPHIC)
TO_WIDE = str.maketrans(ASCII_GRAPHIC, WIDE_GRAPHIC)
VI_LOWER = "đ" + "".join(unicodedata.normalize("NFC", vowel + tone)
                         for vowel in "aăâeêioôơuưy" for tone in ("", "\u0300", "\u0301", "\u0303", "\u0309", "\u0323"))
QUOTE_WORD = "[[:alnum:]_" + VI_LOWER + "]"
WORD = re.compile(r"[^\W\d_]+")
QUOTES = {'"': '"', '“': '”', '«': '»'}
FRAMING = QUESTION_WORDS | {"cả", "mọi", "tất", "theo", "lúc"}
FRAMING_FOLDED = {_fold(word) for word in FRAMING}
NEGATION = r"\b(?:không|chưa|chẳng|tránh|ngoại trừ|thay vì|trừ khi)\b"
NEGATION_FOLDED = _fold(NEGATION)
ALTERNATIVES = re.compile(r"\b([^\W\d_]+) ([^\W\d_]+) (?:và|hoặc|hay|va|hoac) \1 ([^\W\d_]+)\b")


def normalize_query(query):
    return " ".join(unicodedata.normalize("NFC", query).translate(TO_ASCII).split())


def _quote_lookup(query):
    end = QUOTES.get(query[0])
    if not end or not query.endswith(end) or end in query[1:-1] or query[0] in query[1:-1]:
        return None
    value = query[1:-1].strip()
    words = re.findall(r"[^\W_]+", value)
    if not words:
        return None
    # Some PostgreSQL text parsers attach curly quotation marks to the
    # first and last lexemes. Interior words are still in both GIN indexes.
    probes = [value, "“" + value + "”", "«" + value + "»"]
    if len(words) >= 3:
        probes.append(" ".join(words[1:-1]))
    # Only an unaccented phrase uses the ordinary Vietnamese accent folding.
    # Supplying a diacritic inside quotation marks makes it part of the quote.
    fold = all(word.isascii() for word in words)
    pattern = ""
    for piece in re.split(r"([ \t]*[" + CODE_DASH + r"][ \t]*|[ \t]+)", value):
        if piece.isspace():
            pattern += "[[:blank:]]+"
        elif piece and piece.strip() in CODE_DASH:
            pattern += "[[:blank:]]*[" + CODE_DASH + "][[:blank:]]*"
        else:
            pattern += re.escape(_fold(piece) if fold else piece.lower())
    if value[0].isalnum():
        pattern = "(?<!" + QUOTE_WORD + ")" + pattern
    if value[-1].isalnum():
        pattern += "(?!" + QUOTE_WORD + ")"
    return probes, (pattern, fold)


def _key_spellings(key):
    """Equivalent index spellings when a query has no words outside its key."""
    probes = [key]
    if measurement := MEASUREMENT.fullmatch(key):
        if measurement["start"]:
            for dash in CODE_DASH:
                probes.append(key[:measurement.end("start")] + dash + key[measurement.start("number"):])
        elif re.search(r"[.,]\d+$", measurement["number"]):
            probes.append(key.translate(str.maketrans(".,", ",.")))
    elif count := COUNT.fullmatch(key):
        digits = count["number"].replace(".", "")
        if len(digits) > 3 and not digits.startswith("0"):
            for number in (digits, re.sub(r"(?<=\d)(?=(?:\d{3})+$)", ".", digits)):
                probes.append(number + key[count.end("number"):])
    elif DATE_KEY.fullmatch(key):
        first, month, last = re.split(r"[./-]", key)
        day, year = (last, first) if len(first) == 4 else (first, last)
        for m in {month.zfill(2), str(int(month))}:
            for d in {day.zfill(2), str(int(day))}:
                probes.extend((f"{year}-{m}-{d}", f"{year}/{m}/{d}", f"{d}/{m}/{year}",
                               f"{d}.{m}.{year}", f"{d}-{m}-{year}"))
    elif any(ch in CODE_DASH for ch in key):
        for dash in CODE_DASH:
            probes.append(re.sub("[" + CODE_DASH + "]", dash, key))
        if key.isascii():
            probes.append(key.translate(TO_WIDE))
    return list(dict.fromkeys(probes))


def _names(text, original):
    """Keep contiguous capitalized words as written, including short names."""
    groups = []
    run = []
    for word in WORD.finditer(text):
        if run and (not word[0].istitle() or not original[run[-1].end():word.start()].isspace()):
            if len(run) >= 2:
                groups.append((run[0].start(), run[-1].end()))
            run = []
        if word[0].istitle():
            run.append(word)
    if len(run) >= 2:
        groups.append((run[0].start(), run[-1].end()))
    return groups


def _without(text, spans):
    masked = list(text)
    for start, end in spans:
        masked[start:end] = " " * (end - start)
    return "".join(masked)


def lookup(query):
    """Return strict probes, a quoted witness, and an optional contextual lookup."""
    if quote := _quote_lookup(query):
        return quote[0], quote[1], None
    spans = list(quantity_key_spans(query))
    for match in numeric_tokens(query):
        if (any(char in match[0] for char in CODE_DASH + ":./,")
                and not any(start <= match.start() and match.end() <= end for start, end in spans)):
            spans.append(match.span())
    if not spans:
        return None, None, None
    context = _without(query, spans)
    # Never reinterpret an opaque URL, email, filename or a partially quoted
    # expression as remembered prose by dropping its punctuation.
    if re.search(r'[/\\@_#%"“”«»]', context):
        return None, None, None
    words = list(WORD.finditer(context))
    if not words:
        # Other keys (if any) are still checked on the same source.
        start, end = max(spans, key=lambda span: span[1] - span[0])
        return _key_spellings(query[start:end]) if context.strip() == "" else None, None, None
    # Keep ALL surrounding text in the first lexical probe. Keys have their own
    # mandatory source predicates and need not tokenize identically in the index.
    probes = [" ".join(context.split())]
    marked = any(not word[0].isascii() for word in words)
    if re.search(NEGATION if marked else NEGATION_FOLDED, context.casefold()):
        return probes, None, None
    names = _names(context, query)
    remaining = _without(context, names)
    framing = FRAMING if marked else FRAMING_FOLDED
    clues = list(dict.fromkeys(_fold(word) for word in WORD.findall(remaining)
                               if word.casefold() not in framing))
    if names:
        names = [context[start:end] for start, end in names]
        patterns = [r"\m" + "[[:blank:]]+".join(map(_fold, name.split())) + r"\M" for name in names]
        # A request for several entries can name alternatives on one field
        # ("tầng trên và tầng dưới"). An unrelated value of that field must
        # not qualify just because the schedule and location are identical.
        for field, first, second in ALTERNATIVES.findall(context.casefold()):
            patterns.append(r"\m" + _fold(field) + "[[:blank:]]+(?:" + _fold(first) + "|" + _fold(second) + r")\M")
        return probes, None, {
            "fts_probes": [" ".join(names)], "lookup_names": patterns, "lookup_clues": clues,
            "lookup_min": math.ceil(len(clues) / 2),
        }
    if len(clues) >= 2:
        probe = " ".join(clues)
        return probes, None, {"fts_probes": probes if _fold(probes[0]) == probe else [probe],
                              "lookup_names": [], "lookup_clues": [],
                              "lookup_min": 0}
    return probes, None, None


def digit_probes(query):
    # A three-digit suffix survives Vietnamese thousands grouping. For dates
    # choose the four-digit year over the optionally zero-padded day/month.
    # A short or grouped quantity still has to pass the complete source checks.
    runs = re.findall(r"[0-9]+", query)
    if not runs:
        return None, False
    digits = max(runs, key=len)[-3:]
    spellings = product(*((ch, ch.translate(TO_WIDE)) for ch in digits))
    return ["%" + "".join(spelling) + "%" for spelling in spellings], len(digits) == 3
