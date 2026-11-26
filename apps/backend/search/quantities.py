"""Keep the value, written unit and local context of a measurement together."""

import re
import unicodedata


# Preserve case in rates: Mb/s and MB/s differ by a factor of eight.
RATE = r"[kKMGTPE]?i?[bB](?:\s*/\s*s|ps)"
WEIGHTED_DB = r"[dD][bB]\s*(?:\(\s*[ACZacz]\s*\)|[ACZ])"
LENGTH = r"(?:[cmunkµμ]?m)"
NUMBER = r"[+−-]?\d+(?:[.,]\d+)?"
UNIT_GAP = r"\s*(?:[-‑]\s*)?"
MEASUREMENT = re.compile(
    rf"(?<![\w.,+−-])(?P<number>{NUMBER}){UNIT_GAP}(?P<unit>{WEIGHTED_DB}|{RATE}|{LENGTH}"
    r"|kg|mg|[kM]?Hz|m[sL]|g|s|°\s*[CF]|%)(?![\w/])"
)
DATE = r"(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4})"
DATE_KEY = re.compile(rf"(?<![\w/-]){DATE}(?![\w/-])")
DIMENSIONS = {
    "width": ("ngang", "rộng", "rong", "width"),
    "height": ("cao", "height"),
    "length": ("dài", "dai", "length"),
    "depth": ("sâu", "chieu sau", "depth"),
    "thickness": ("dày", "do day", "thickness"),
}
ASSIGNMENT = r"\s*(?:[:=]\s*)?(?:(?:là|la|bằng|bang|khoảng|khoang|đạt|dat)\s+)?"
FIELD = re.compile(r"\b(" + "|".join(a for aliases in DIMENSIONS.values() for a in aliases)
                   + r")" + ASSIGNMENT + "$")
CLAUSE_END = (r"[;!?\n]|[.,](?![[:digit:]])|(?<![[:digit:]])[.,]|"
              r"[[:space:]](?:và|còn|nhưng|and|but|whereas)(?=[[:space:]])")
# A field beginning the next clause can continue the preceding object's size.
AXIS_NAMES = "|".join(a for aliases in DIMENSIONS.values() for a in aliases)
AXIS_CONTINUATION = (r"[[:space:]]*(?:(?:chiều|chieu|bề|be|độ|do|và|còn|and|the|its)[[:space:]]+)*"
                     rf"(?:{AXIS_NAMES})(?=[[:space:]:=])")
NO_READING = (r"\m(?:(?:chua|khong)\s+(?:(?:duoc|co)\s+)?"
              r"(?:ghi|do|xac dinh|biet|cong bo|so lieu|du lieu|ket qua)|"
              r"no\s+(?:reading|measurement|data)|not\s+(?:yet\s+)?(?:recorded|measured|available))\M")
CLUE_STOP = frozenset("ai cac cho cua co da den duoc gi giup hay hoi khi la ma minh nao ngay nho "
                      "o tai theo thi tim toi trong tu va ve voi".split())
ENGLISH_CLUE_STOP = frozenset("a an at by for of on the with".split())


def _fold(text):
    text = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    return "".join(c for c in text if not unicodedata.combining(c))


def _written_number(value):
    # A fragment of a decimal or a negative value cannot satisfy a positive
    # request. The hyphen and the typographic minus are equivalent signs.
    sign = "[-−]" if value.startswith(("-", "−")) else "[+]?"
    return sign + re.escape(value.lstrip("+−-"))


def _number(value):
    return r"(?<![[:alnum:]_.,+−-])" + _written_number(value)


def _unit(value):
    if re.fullmatch(WEIGHTED_DB, value):
        weight = next(char.upper() for char in value[2:] if char.isalpha())
        return rf"[dD][bB]\s*(?:\(\s*[{weight}{weight.lower()}]\s*\)|{weight})"
    if re.fullmatch(RATE, value):
        prefix = re.split(r"/s|ps", "".join(value.split()))[0]
        return re.escape(prefix) + r"(?:\s*/\s*s|ps)"
    if value.startswith("°"):
        return "°" + r"\s*" + value[-1]
    if value in {"µm", "μm"}:
        return "[µμ]m"
    return re.escape(value)


def quantity_params(query):
    """Prepare source-level predicates only for explicit, recognizable quantities."""
    query = unicodedata.normalize("NFC", query)
    required, labelled, size = [], [], {}
    contexts = []
    clue_text = list(query)
    for match in MEASUREMENT.finditer(query):
        value, unit = match.group("number", "unit")
        pattern = _number(value) + UNIT_GAP + _unit(unit) + r"(?![[:alnum:]_/²³])"
        required.append(pattern)
        clue_text[match.start():match.end()] = " " * len(match[0])
        if re.fullmatch(RATE, unit):
            contexts.append((pattern, rf"(?<![[:alnum:]_.,+−-]){NUMBER}{UNIT_GAP}{RATE}(?![[:alnum:]_])"))
        if re.fullmatch(LENGTH, unit) and (field := FIELD.search(query[:match.start()].casefold())):
            axis, aliases = next((k, v) for k, v in DIMENSIONS.items() if field[1] in v)
            label = r"\m(?:" + "|".join(aliases) + r")\M" + ASSIGNMENT
            labelled.append(label + pattern)
            size[axis] = (value, unit, len(required) - 1, len(labelled) - 1)

    # A compact width × height has one shared unit on many sketches. Either
    # two explicit assignments or the correctly ordered pair support the query.
    paired_labels = None
    if "width" in size and "height" in size:
        paired_labels = [labelled[size[axis][3]] for axis in ("width", "height")]
    if paired_labels and size["width"][1] == size["height"][1]:
        width, unit, *_ = size["width"]
        height = size["height"][0]
        pair = (_number(width) + rf"\s*(?:{_unit(unit)}\s*)?[xX×]\s*"
                + _written_number(height) + UNIT_GAP + _unit(unit) + r"(?![[:alnum:]_])")
        for axis in ("width", "height"):
            _, _, at, field_at = size[axis]
            required[at] = f"(?:{required[at]}|{pair})"
            labelled[field_at] = f"(?:{labelled[field_at]}|{pair})"
        paired_labels = [labelled[size[axis][3]] for axis in ("width", "height")]

    for date in DATE_KEY.finditer(query):
        pattern = r"(?<![[:alnum:]_/-])" + re.escape(date[0]) + r"(?![[:alnum:]_/-])"
        required.append(pattern)
        contexts.append((pattern, r"(?<![[:alnum:]_/-])" + DATE + r"(?![[:alnum:]_/-])"))
        clue_text[date.start():date.end()] = " " * len(date[0])

    # With several requested dates/rates a single bag of clues cannot say
    # which role belongs to which value. Only reject a competing assignment
    # when there is one unambiguous target to compare within the source.
    clues = []
    if len(contexts) == 1:
        # Even an unaccented Vietnamese query can use "in" as the predicate
        # or the distinguishing part of "máy in" (printer).
        stop = CLUE_STOP | ENGLISH_CLUE_STOP if query.isascii() else CLUE_STOP
        clues = sorted(set(re.findall(r"[^\W\d_]+", _fold("".join(clue_text)))) - stop)
    target, family = contexts[0] if clues else (None, None)
    return {
        "quantity_required": required or None, "quantity_labels": labelled or None, "quantity_pair": paired_labels,
        "quantity_target": target, "quantity_family": family, "quantity_clues": clues,
    }


def quantity_condition(source):
    """Run after indexed candidate selection, before evidence and page limits."""
    # Commas/periods inside decimals and dates stay with the number. Split
    # at clause boundaries so a signature date cannot substantiate a reading.
    separators = f"(?i)(?:{CLAUSE_END})"
    object_separators = separators + f"(?!{AXIS_CONTINUATION})"
    return rf"""(
        (%(quantity_required)s::text[] IS NULL OR {source} ~ ALL (%(quantity_required)s::text[]))
        AND (%(quantity_labels)s::text[] IS NULL OR
             {source} ~* ALL (%(quantity_labels)s::text[]))
        AND (%(quantity_pair)s::text[] IS NULL OR EXISTS (
            SELECT 1 FROM regexp_split_to_table({source}, '{object_separators}') AS objects(passage)
            WHERE passage ~* ALL (%(quantity_pair)s::text[])
        ))
        AND (%(quantity_target)s::text IS NULL OR NOT EXISTS (
            SELECT 1 FROM (
                SELECT clause ~ %(quantity_target)s AS wanted,
                       (SELECT count(*) FROM unnest(%(quantity_clues)s::text[]) clues(word)
                        WHERE word = ANY(regexp_split_to_array(public.kt_search_fold(clause),
                                                               '[^[:alnum:]]+'))) AS anchors
                FROM regexp_split_to_table({source}, '{separators}') AS clauses(clause)
                WHERE clause ~ %(quantity_family)s OR public.kt_search_fold(clause) ~ '{NO_READING}'
            ) support
            HAVING max(anchors) FILTER (WHERE NOT wanted) > coalesce(max(anchors) FILTER (WHERE wanted), 0)
        ))
    )"""
