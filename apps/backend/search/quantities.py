"""Keep the value, written unit and local context of a measurement together."""

from datetime import date
import re
import unicodedata


# Preserve case in rates: Mb/s and MB/s differ by a factor of eight.
RATE = r"[kKMGTPE]?i?[bB](?:\s*/\s*s|ps)"
WEIGHTED_DB = r"[dD][bB]\s*(?:\(\s*[ACZacz]\s*\)|[ACZ])"
LENGTH = r"(?:[cmunkµμ]?m)"
NUMBER = r"[+−-]?\d+(?:[.,]\d+)?"
UNIT_GAP = r"\s*(?:[-‑]\s*)?"
DASH = r"[-‐‑‒–—−]"
RANGE_SPACE = "[ \t\u00a0\u202f]*"
RANGE_GAP = f"{RANGE_SPACE}{DASH}{RANGE_SPACE}"
NUMBER_START = rf"(?<![\w.,/+−-])(?<!\d{DASH})"
SQL_NUMBER_START = rf"(?<![[:alnum:]_.,/+−-])(?<![[:digit:]]{DASH})"
MEASUREMENT = re.compile(
    rf"{NUMBER_START}(?:(?P<start>{NUMBER}){RANGE_GAP})?"
    rf"(?P<number>{NUMBER}){UNIT_GAP}(?P<unit>{WEIGHTED_DB}|{RATE}|{LENGTH}"
    r"|kg|mg|[kM]?Hz|m[sL]|g|s|°\s*[CF]|%)(?![\w/])"
)
COUNT_NUMBER = r"(?:[0-9]{1,3}(?:[.][0-9]{3})+|[0-9]+)"
COUNT_UNITS = {"tờ": "[tT][ờỜ]", "hộp": "[hH][ộỘ][pP]"}
COUNT = re.compile(rf"{NUMBER_START}(?P<number>{COUNT_NUMBER})"
                   rf"\s+(?P<unit>{'|'.join(COUNT_UNITS.values())})(?!\w)")
DATE = (r"(?:[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}|"
        r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|[0-9]{1,2}[.][0-9]{1,2}[.][0-9]{4}|"
        r"[0-9]{1,2}-[0-9]{1,2}-[0-9]{4})")
DATE_KEY = re.compile(rf"(?<![\w/-])(?<!\d[.]){DATE}(?![\w/-]|[.]\d)")
SQL_DATE_START = r"(?<![[:alnum:]_/-])(?<![[:digit:]][.])"
SQL_DATE_END = r"(?![[:alnum:]_/-]|[.][[:digit:]])"
VERSION = r"(?:[vV]?[0-9]+(?:[.][0-9]+){2,})"
VERSION_KEY = re.compile(rf"(?<![\w/-])(?<!\w[.]){VERSION}(?![\w/-]|[.]\w)")
VERSION_LABEL = re.compile(r"\b(?:bản|ban|ver|version)\s*[:=]?\s*$", re.IGNORECASE)
SQL_VERSION_START = r"(?<![[:alnum:]_/-])(?<![[:alnum:]][.])"
SQL_VERSION_END = r"(?![[:alnum:]_/-]|[.][[:alnum:]])"
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
    magnitude = value.lstrip("+−-")
    decimal = re.fullmatch(r"([0-9]+)[.,]([0-9]+)", magnitude)
    # Three trailing digits can also be a grouping separator. Preserve the
    # written separator when the magnitude has that ambiguity.
    if decimal and len(decimal[2]) != 3:
        return sign + decimal[1] + "[.,]" + decimal[2]
    return sign + re.escape(magnitude)


def _number(value):
    return SQL_NUMBER_START + _written_number(value)


def _count_pattern(match):
    digits = match["number"].replace(".", "")
    group_start = len(digits) % 3 or 3
    if len(digits) > 3 and not digits.startswith("0"):
        grouped = digits[:group_start] + "".join(
            "." + digits[start:start + 3] for start in range(group_start, len(digits), 3))
        digits = rf"(?:{digits}|{re.escape(grouped)})"
    elif "." in match["number"]:
        digits = re.escape(match["number"])
    return SQL_NUMBER_START + digits + _count_unit(match)


def _count_unit(match):
    return r"\s+" + COUNT_UNITS[match["unit"].lower()] + r"(?![[:alnum:]_])"


def _date_pattern(value):
    first, second, third = re.split(r"[./-]", value)
    if len(first) == 4:
        year, month, day = first, second, third
    else:
        day, month, year = first, second, third
    try:
        calendar_date = date(int(year), int(month), int(day))
    except ValueError:
        return None
    month, day = (f"0?{part}" if part < 10 else str(part)
                  for part in (calendar_date.month, calendar_date.day))
    alternatives = [f"{year}{sep}{month}{sep}{day}" for sep in "-/"]
    alternatives.extend(f"{day}{sep}{month}{sep}{year}" for sep in ("-", "/", "[.]"))
    return SQL_DATE_START + "(?:" + "|".join(alternatives) + ")" + SQL_DATE_END


def _calendar_dates(query):
    for match in DATE_KEY.finditer(query):
        if "." in match[0] and VERSION_LABEL.search(query, 0, match.start()):
            continue
        if pattern := _date_pattern(match[0]):
            yield match, pattern


def quantity_key_spans(query):
    """Locate spans already enforced by quantity predicates in an NFC query."""
    yield from (match.span() for match in MEASUREMENT.finditer(query))
    yield from (match.span() for match in COUNT.finditer(query))
    yield from (match.span() for match, _ in _calendar_dates(query))


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
        reading = (_number(match["start"]) + RANGE_GAP + _written_number(value)
                   if match["start"] else _number(value))
        pattern = reading + UNIT_GAP + _unit(unit) + r"(?![[:alnum:]_/²³])"
        required.append(pattern)
        clue_text[match.start():match.end()] = " " * len(match[0])
        if re.fullmatch(RATE, unit):
            contexts.append((pattern, rf"{SQL_NUMBER_START}{NUMBER}{UNIT_GAP}{RATE}(?![[:alnum:]_])"))
        if (not match["start"] and re.fullmatch(LENGTH, unit)
                and (field := FIELD.search(query[:match.start()].casefold()))):
            axis, aliases = next((k, v) for k, v in DIMENSIONS.items() if field[1] in v)
            label = r"\m(?:" + "|".join(aliases) + r")\M" + ASSIGNMENT
            labelled.append(label + pattern)
            family = label + SQL_NUMBER_START + NUMBER + UNIT_GAP + _unit(unit) + r"(?![[:alnum:]_/²³])"
            contexts.append((f"(?i){labelled[-1]}", f"(?i){family}"))
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

    for count in COUNT.finditer(query):
        pattern = _count_pattern(count)
        required.append(pattern)
        contexts.append((pattern, SQL_NUMBER_START + COUNT_NUMBER + _count_unit(count)))
        clue_text[count.start():count.end()] = " " * len(count[0])

    for match, pattern in _calendar_dates(query):
        required.append(pattern)
        contexts.append((pattern, SQL_DATE_START + DATE + SQL_DATE_END))
        clue_text[match.start():match.end()] = " " * len(match[0])

    for match in VERSION_KEY.finditer("".join(clue_text)):
        literal = "[vV]" + re.escape(match[0][1:]) if match[0][0] in "vV" else re.escape(match[0])
        pattern = SQL_VERSION_START + literal + SQL_VERSION_END
        required.append(pattern)
        contexts.append((pattern, SQL_VERSION_START + VERSION + SQL_VERSION_END))
        clue_text[match.start():match.end()] = " " * len(match[0])

    # With several requested dates, rates or versions a single bag of clues cannot say
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
