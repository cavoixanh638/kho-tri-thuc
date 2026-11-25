"""Find notes supported by several words of a remembered description."""

import math
import re
import unicodedata

from .queries import ITEM_TEXT, ITEM_VECTOR, VISIBLE_ITEMS


# These words frame a question but usually do not identify a note. Keep marked
# and unmarked Vietnamese distinct when the writer supplied diacritics.
QUESTION_WORDS = frozenset("""
ạ à ai cái các cho chưa chứ có của cũng đã đang đây để đó được đâu gì giúp
hãy hay khi là lại mà mấy mình một nào này nhé nhỉ nhớ những ở ra rằng rồi
sao sẽ sự tại thì thế tìm tôi tớ từ và vào vậy vẫn về vì với
""".split())
ENGLISH_QUESTION_WORDS = frozenset("and does from please what where which with".split())
QUERY_FRAMING = re.compile(r"\b(?:ghi chú|ghi chu|bài viết|bai viet|tài liệu|tai lieu|lúc nào|luc nao)\b")


def _unaccent(word):
    return "".join(char for char in unicodedata.normalize("NFD", word.replace("đ", "d"))
                   if not unicodedata.combining(char))


UNACCENTED_QUESTION_WORDS = frozenset(map(_unaccent, QUESTION_WORDS))
MAX_POSTINGS_PER_TERM = 64


def recall_params(query):
    words = re.findall(r"[^\W_]+", QUERY_FRAMING.sub(" ", query.casefold()))
    # A single token, quoted text, URL, or structured identifier already has a
    # literal/typo search. Do not silently discard pieces of an exact key.
    if len(query.split()) < 2 or any(char in query for char in '/\\@_#%:"“”'):
        return None
    accented = any(not word.isascii() for word in words)
    stop_words = QUESTION_WORDS if accented else UNACCENTED_QUESTION_WORDS | ENGLISH_QUESTION_WORDS
    terms = list(dict.fromkeys(word for word in words if word not in stop_words))
    identifiers = [word for word in terms if len(word) >= 4
                   and any(ch.isdigit() for ch in word) and any(ch.isalpha() for ch in word)]
    if not terms or len(terms) > 24 or (len(terms) < 2 and not identifiers):
        return None
    pairs = list(dict.fromkeys(f"{a} {b}" for a, b in zip(words, words[1:])
                               if a != b and a in terms and b in terms))
    return {
        "terms": terms, "identifiers": identifiers, "pairs": pairs,
        "config": "pg_catalog.simple" if any(not word.isascii() for word in terms) else "public.kt_vi",
        "strong_phrase_count": max(3, math.ceil(0.75 * len(terms))),
        "suggestion_count": max(2, min(3, math.ceil(0.25 * len(terms)))),
        "postings_limit": MAX_POSTINGS_PER_TERM + 1,
    }


RECALL_SQL = f"""
WITH {VISIBLE_ITEMS},
terms AS MATERIALIZED (
    SELECT word, plainto_tsquery('public.kt_vi', word) AS indexed_query,
           plainto_tsquery(%(config)s::regconfig, word) AS term_query
    FROM unnest(%(terms)s::text[]) AS words(word)
),
-- Probe the existing GIN index for each term. Discard a saturated posting
-- list as a candidate source in its entirety, independent of physical order.
postings AS MATERIALIZED (
    SELECT t.word, hit.id, count(*) OVER (PARTITION BY t.word) AS frequency
    FROM terms t CROSS JOIN LATERAL (
        SELECT i.id FROM visible_items i WHERE {ITEM_VECTOR} @@ t.indexed_query
        LIMIT %(postings_limit)s
    ) hit
),
candidate_ids AS (
    SELECT DISTINCT id FROM postings WHERE frequency < %(postings_limit)s
),
documents AS MATERIALIZED (
    SELECT i.id, to_tsvector(%(config)s::regconfig, {ITEM_TEXT}) AS document,
           to_tsvector(%(config)s::regconfig, i.title) AS title_vector
    FROM candidate_ids c CROSS JOIN LATERAL (
        SELECT src.* FROM visible_items src WHERE src.id = c.id LIMIT 1
    ) i
),
weights AS (
    SELECT t.*, coalesce(f.frequency, 0) AS frequency
    FROM terms t LEFT JOIN (SELECT word, max(frequency) AS frequency FROM postings GROUP BY word) f
      ON f.word = t.word
),
scored AS (
    SELECT d.id,
           count(*) FILTER (WHERE d.document @@ t.term_query) AS matched,
           bool_or(t.word = ANY(%(identifiers)s::text[]) AND d.document @@ t.term_query) AS has_identifier,
           sum((1 + 0.25 * (d.title_vector @@ t.term_query)::int) /
               sqrt(greatest(1, t.frequency)::float8)) FILTER (WHERE d.document @@ t.term_query) AS term_score
    FROM documents d CROSS JOIN weights t
    GROUP BY d.id
    HAVING bool_and(t.word !~ '[[:digit:]]' OR d.document @@ t.term_query)
       AND bool_or(t.frequency BETWEEN 1 AND %(postings_limit)s - 1 AND d.document @@ t.term_query)
),
phrase_query AS (
    SELECT string_agg(phraseto_tsquery(%(config)s::regconfig, pair)::text, ' | ')::tsquery AS q
    FROM unnest(%(pairs)s::text[]) AS pairs(pair)
),
supported AS (
    SELECT s.*, coalesce(d.document @@ phrase.q, false) AS has_phrase
    FROM scored s JOIN documents d ON d.id = s.id CROSS JOIN phrase_query phrase
    WHERE s.has_identifier OR s.matched >= %(suggestion_count)s
),
confidence AS (
    SELECT id, term_score + CASE WHEN has_phrase THEN 0.5 ELSE 0 END AS weight,
           (has_identifier OR matched = cardinality(%(terms)s::text[]) OR
            (has_phrase AND matched >= %(strong_phrase_count)s)) AS strong
    FROM supported
),
ranked AS (
    -- Nonoverlapping score intervals keep the existing keyset cursor stable
    -- when a reader explicitly includes weaker suggestions.
    SELECT id, strong, (strong::int + weight / (1 + weight))::real AS score
    FROM confidence
),
page AS (
    SELECT id, score, strong FROM ranked
    WHERE %(cursor_id)s::uuid IS NULL OR (score, id) < (%(cursor_score)s::real, %(cursor_id)s::uuid)
    ORDER BY score DESC, id DESC LIMIT %(page_size)s
),
headline_query AS (
    SELECT string_agg(term_query::text, ' | ')::tsquery AS q FROM terms
)
SELECT i.id, i.title, p.score, 'item', left(ts_headline(
           %(config)s::regconfig, {ITEM_TEXT}, h.q,
           'StartSel="", StopSel="", MaxWords=24, MinWords=8, MaxFragments=1, ShortWord=0'
       ), 320), NULL, '{{}}', p.strong
FROM page p JOIN visible_items i ON i.id = p.id CROSS JOIN headline_query h
ORDER BY p.score DESC, p.id DESC
"""
