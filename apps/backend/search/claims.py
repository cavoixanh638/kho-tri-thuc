"""Lexical witnesses for explicit constraints in a Vietnamese lookup.

The index finds candidate sources. A named value or an asserted relation
must also have a witness inside that source before it can enter a page.
Open questions and ordinary remembered keywords keep the usual ranking.
"""

import re
import unicodedata


def _fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
                   if not unicodedata.combining(c))


WORD = r"[^\W\d_]+"
# PostgreSQL ARE. Stay in one clause while identifying an action and its
# arguments. A condition can have a comma before its consequence.
NEAR = r"[^,.:!?;\n]{0,120}"
JOIN = r"[^.!?;\n]{0,140}"
SPACE = r"[[:blank:]]+"
AFFIRMATIVE = r"(?<!\m(?:khong(?:\s+(?:duoc|nen|the|he))?|chua(?:\s+duoc)?|dung|cam)\s+)"
OPEN_SLOT = re.compile(r"\b(?:ai|gì|đâu|nào|sao|mấy|bao nhiêu|thế nào)\b")
FRAMING = re.compile(r"^.*?\b(?:ghi chú|tài liệu|bài viết|hướng dẫn|biên bản|tờ|phiếu)\b.*?"
                     r"\b(?:bảo|ghi rằng|ghi là|nói(?: rằng| là)?|xác nhận rằng)\s+")
FILLER = frozenset("ở là được đã một những các của thì mà ra theo để cho tới".split())


def _words(text):
    return re.findall(WORD, text.lower())


def _literal(words):
    return r"\m" + SPACE.join(map(_fold, words)) + r"\M"


def _one_of(words):
    return "(?:" + "|".join(_literal([word]) for word in dict.fromkeys(words)) + ")"


def _clues(text):
    """Require ordered clues from both ends of the supplied description."""
    words = [word for word in _words(text) if word not in FILLER]
    if len(words) < 2:
        return _literal(words) if words else ""
    mid = (len(words) + 1) // 2
    return _one_of(words[:mid]) + NEAR + _one_of(words[mid:])


def _either(*patterns):
    return "(?:" + "|".join(patterns) + ")"


def _named_values(query):
    # Ignore acronyms, which can be field labels (e.g. NXB before a name).
    for match in re.finditer(rf"\b{WORD}\b(?:[ \t]+{WORD}\b)*", query):
        run = []
        for word in [*match[0].split(), ""]:
            if word.istitle():
                run.append(word)
            else:
                if len(run) >= 3:
                    yield _literal(run)
                run = []
    # The publisher label also supplies a value boundary when a reader types
    # the name in lower case or without accents.
    folded = _fold(query)
    publisher = re.search(r"\b(?:nha xuat ban|nxb) +([^,.;:!?\n]+)", folded)
    if publisher:
        name = re.split(r"\b(?:co|cua|nam(?= +\d{4})|duoc|kem|tai|voi|hay|hoac|nao)\b", publisher[1])[0]
        words = _words(name)
        if 2 <= len(words) <= 6:
            yield _literal(words)

    weekdays = {"hai": "2", "ba": "3", "tu": "4", "nam": "5", "sau": "6", "bay": "7"}
    days = []
    for day in re.findall(r"\b(?:chu nhat|thu (?:hai|ba|tu|nam|sau|bay))\b", folded):
        alt = ["CN"] if day == "chu nhat" else ["thu", weekdays[day.split()[1]]]
        days.append(_either(_literal(day.split()), _literal(alt)))
    if len(days) > 1 and re.search(r"\b(?:hay|hoac)\b", folded):
        yield _either(*days)
    else:
        yield from days


def _condition(text):
    # Drop an outer "ghi chú nào bảo ..." without dropping an unknown inside
    # the actual condition (e.g. "thiếu dụng cụ nào thì ...").
    statement = FRAMING.sub("", text)
    if OPEN_SLOT.search(statement):
        return
    if " thì " in statement:
        premise, effect = statement.split(" thì ", 1)
        # A narrative with several events may legitimately span sentences.
        if re.search(r"\b(?:và|rồi|sau đó)\b", premise):
            return
        before, result = _clues(premise), [w for w in _words(effect) if w not in FILLER]
        if before and result:
            # In a short command the first word distinguishes opposite actions
            # performed on the same object (e.g. raise or lower a door).
            negated = result[0] in {"không", "chưa", "đừng", "cấm"}
            after = ("" if negated else AFFIRMATIVE) + _literal(result[:2] if negated else result[:1])
            if len(result) > (2 if negated else 1):
                after += NEAR + _one_of(result[(len(result) + 1) // 2:])
            return _either(before + JOIN + after, after + JOIN + r"\m(?:khi|neu)\M" + NEAR + before), None
        return
    # Verify short, self-contained instructions with an explicit time
    # connector. Preserve the polarity of the action in either word order.
    match = re.fullmatch(r"([^,.!?;]+?) (trước khi|sau khi|khi) ([^,.!?;]+)[.!?]?", statement)
    if match and len(statement.split()) <= 15:
        action, connector, event = match.groups()
        first = _words(action)
        if not first or not (trigger := _clues(event)):
            return
        negative = first[0] in {"không", "chưa", "đừng", "cấm"}
        act = ("" if negative else AFFIRMATIVE) + _literal(first)
        joint = _literal(connector.split())
        if connector == "khi":
            def when(action):
                return _either(action + NEAR + joint + NEAR + trigger, joint + NEAR + trigger + JOIN + action)

            # "When" alone is also a loose retrieval clue. Demand an exact
            # affirmative witness only if the source actually forbids it.
            negation = r"\m(?:khong(?:\s+(?:duoc|nen|the|he))?|chua(?:\s+duoc)?|dung|cam)\s+"
            return when(act), None if negative else when(negation + _literal(first))
        else:
            other = _literal(("sau khi" if connector == "trước khi" else "trước khi").split())
            return _either(act + NEAR + joint + NEAR + trigger, trigger + NEAR + other + NEAR + act,
                           joint + NEAR + trigger + JOIN + act), None


def _cause(text):
    # An explicit causal assertion ("vì A làm B") supplies both an agent and
    # an outcome. A question asking why supplies neither.
    parts = re.search(r"(?<!thay )\b(?:vì|do|bởi) (.+?) (?:làm|khiến|gây(?: ra)?) ([^,.!?;]+)", text)
    if parts and not OPEN_SLOT.search(parts[0]):
        agent, outcome = _clues(parts[1]), _words(parts[2])
        if agent and outcome:
            event = _literal(outcome[:1])
            yield _either(agent + NEAR + event, event + NEAR + r"\m(?:do|vi|boi)\M" + NEAR + agent)


def _sufficiency(text):
    cues = (
        (r"\b(?:khỏi cần|không cần phải|không cần đến) ",
         r"\m(?:khoi\s+can|khong\s+(?:can|phai|bat\s+buoc)|duoc\s+mien)\M"),
        (r"\b(?:chỉ bằng|chỉ cần có|chỉ cần dùng) ",
         r"\m(?:chi\s+(?:bang|can|voi)|mien\s+(?:la|co))\M"),
    )
    for cue, witness in cues:
        if match := re.search(cue + r"([^,.!?;]+)", text):
            # "ở đâu" is often the request to locate the whole note.
            complement = re.split(r"\b(?:ở đâu|là đủ|cũng được)\b", match[1])[0]
            if not OPEN_SLOT.search(complement) and (value := _clues(complement)):
                yield _either(witness + NEAR + value, value + NEAR + r"\m(?:la\s+du|khong\s+bat\s+buoc)\M")


TRANSFER = r"(?:giao|trao|tặng|biếu|gửi|chuyển)"
GIVING = r"\m(?:giao|trao|tang|bieu|gui|chuyen)\M"
PAYING = r"\m(?:tra|thanh\s+toan|chi\s+tra|tai\s+tro|ho\s+tro)\M"


def _transfer(text):
    # Only bind named roles. "Tìm lần được biếu đồ" leaves the roles open.
    for clause in re.split(r"[,;.!?]", text):
        verbs = list(re.finditer(rf"\b({TRANSFER}|trả|thanh toán) ", clause))
        if not verbs:
            continue
        verb = verbs[-1]
        left, right = clause[:verb.start()].strip(), clause[verb.end():].strip()
        paying = verb[1] in {"trả", "thanh toán"}
        indirect = re.search(r"\b(?:cho|tới|đến) ", right)
        if paying and not re.match(r"(?:luôn cả|cả|hộ|thay|toàn bộ)\b", right):
            continue
        if not indirect and not re.search(r"\b(?:sang|đến|tới)$", left):
            continue
        subject = re.split(r"\b(?:đem|mang|đã|sẽ|sang|phải)\b", left)[0]
        subject_words = _words(subject)[-2:]
        recipient = right[indirect.end():] if indirect else right
        if not subject_words or not recipient or OPEN_SLOT.search(recipient):
            continue
        destination = _literal(_words(recipient)[:2]) if _words(recipient) else ""
        if not destination:
            continue
        sender = _literal(subject_words)
        predicate = PAYING if paying else GIVING
        sent = re.sub(r"^(?:luôn cả|cả|hộ|thay|toàn bộ)\s+", "", right[:indirect.start()]).strip() if indirect else ""
        content = _clues(sent)
        action = predicate + (NEAR + content if content else "")
        yield _either(sender + NEAR + action + NEAR + destination,
                      destination + NEAR + r"\mduoc\M" + NEAR + sender + NEAR + action,
                      destination + NEAR + action + NEAR + r"\mboi\M" + NEAR + sender)


def _color_attribute(text):
    colors = r"(?:xanh|đỏ|vàng|tím|cam|lục|lam|nâu|đen|trắng|hồng|xám|bạc)"
    pattern = rf"\b((?:{WORD} )?{WORD}) (?:ra|lên|thành|viền|nền|ngả|chuyển sang) ({colors}(?: (?:{colors}|đậm|nhạt|sẫm|thẫm))?)\b"
    for match in re.finditer(pattern, text):
        subject, value = match.groups()
        words = [w for w in _words(subject) if w not in FILLER]
        if words:
            yield _literal(words) + NEAR + _literal(value.split())


def claim_params(query):
    text = query.lower()
    tests = [*_named_values(query), *_cause(text), *_sufficiency(text), *_transfer(text), *_color_attribute(text)]
    action, opposite = _condition(text) or (None, None)
    if action and not opposite:
        tests.append(action)
    return {"claim_patterns": list(dict.fromkeys(tests)) or None,
            "claim_opposite": opposite, "claim_action": action if opposite else None}


def claim_condition(source):
    folded = f"public.kt_search_fold({source})"
    return f"""((%(claim_patterns)s::text[] IS NULL OR {folded} ~ ALL (%(claim_patterns)s::text[]))
            AND (%(claim_opposite)s::text IS NULL OR {folded} !~ %(claim_opposite)s OR {folded} ~ %(claim_action)s))"""
