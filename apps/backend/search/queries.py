from .claims import claim_condition
from .identifiers import identifier_condition
from .passages import evidence_excerpt, quote_text
from .quantities import quantity_condition


# Match the expressions and predicates in search.0001, including the config.
ITEM_TEXT = "public.kt_search_item(i.title, i.description, i.note)"
ITEM_VECTOR = f"to_tsvector('public.kt_vi', {ITEM_TEXT})"
ITEM_FOLD = f"public.kt_search_fold({ITEM_TEXT})"
DERIVED_TEXT = "public.kt_search_text(d.text)"
DERIVED_VECTOR = f"to_tsvector('public.kt_vi', {DERIVED_TEXT})"
CAPTURE_TEXT = "public.kt_search_text(c.raw_text)"
CAPTURE_VECTOR = f"to_tsvector('public.kt_vi', {CAPTURE_TEXT})"

# Keep the indexed text unchanged, but do not construct a sentence out of
# the end of a title and the beginning of a note when verifying a claim.
ITEM_PASSAGE = r"normalize(concat_ws(E'\n', i.title, left(i.description, 20000), left(i.note, 100000)), NFC)"


def source_condition(source):
    passage = ITEM_PASSAGE if source == ITEM_TEXT else source
    # Both width forms have one character per code point. Keep the actual
    # passage for snippets, and use the equivalent ASCII form to check keys.
    key_source = f"translate({source}, %(width_from)s, %(width_to)s)"
    key_passage = f"translate({passage}, %(width_from)s, %(width_to)s)"
    # Use the existing trigram index for a distinctive digit fragment in
    # an Item. Small numeric fragments and the other sources are cheap
    # literal checks on the already scoped candidates.
    digits = "ANY(%(digit_probes)s::text[])"
    if source == ITEM_TEXT:
        digit_check = f"""(%(digit_probes)s::text[] IS NULL
            OR (%(indexed_digits)s AND {ITEM_FOLD} LIKE {digits})
            OR (NOT %(indexed_digits)s AND
                (i.title LIKE {digits} OR i.description LIKE {digits} OR i.note LIKE {digits})))"""
    else:
        digit_check = f"(%(digit_probes)s::text[] IS NULL OR {source} LIKE {digits})"
    return f"""({digit_check} AND {identifier_condition(key_source)} AND {claim_condition(passage)}
        AND {quantity_condition(key_passage)}
        AND (%(quote_pattern)s::text IS NULL OR {quote_text(passage)} ~ %(quote_pattern)s)
        AND (%(lookup_min)s = 0 OR (
            SELECT count(*) FROM unnest(%(lookup_clues)s::text[]) AS clues(word)
            WHERE word = ANY(regexp_split_to_array(public.kt_search_fold({passage}), '[^[:alnum:]]+'))
        ) >= %(lookup_min)s))"""

EVIDENCE_TEXT = f"""CASE e.source WHEN 'item' THEN {ITEM_TEXT}
    WHEN 'derived_content' THEN {DERIVED_TEXT} ELSE {CAPTURE_TEXT} END"""
EVIDENCE_PASSAGE = f"""CASE e.source WHEN 'item' THEN {ITEM_PASSAGE}
    WHEN 'derived_content' THEN {DERIVED_TEXT} ELSE {CAPTURE_TEXT} END"""
HEADLINE_OPTIONS = """'StartSel="", StopSel="", MaxWords=24, MinWords=8, MaxFragments=1, ShortWord=0'"""
STANDARD_EXCERPT = f"""CASE WHEN e.fts THEN left(ts_headline('public.kt_vi', {EVIDENCE_TEXT}, tsq,
    {HEADLINE_OPTIONS}), 320)
    ELSE substring({ITEM_TEXT} FROM greatest(strpos({ITEM_FOLD}, folded) - 60, 1) FOR 320) END"""

VISIBLE_ITEMS = """
visible_items AS NOT MATERIALIZED (
    SELECT i.id, i.owner_id, i.title, i.description, i.note
    FROM catalog_item i
    WHERE i.owner_id = %(owner_id)s AND i.deleted_at IS NULL
      AND (%(exclude_item_id)s::uuid IS NULL OR i.id <> %(exclude_item_id)s)
      AND (%(topic_id)s::bigint IS NULL OR EXISTS (
          SELECT 1 FROM catalog_itemtopic it JOIN catalog_topic t ON t.id = it.topic_id
          WHERE it.item_id = i.id AND t.id = %(topic_id)s AND t.owner_id = i.owner_id
      ))
      AND (%(project_id)s::bigint IS NULL OR EXISTS (
          SELECT 1 FROM catalog_itemproject ip JOIN catalog_project p ON p.id = ip.project_id
          WHERE ip.item_id = i.id AND p.id = %(project_id)s AND p.owner_id = i.owner_id
      ))
      AND (%(tag_id)s::bigint IS NULL OR EXISTS (
          SELECT 1 FROM catalog_itemtag it JOIN catalog_tag t ON t.id = it.tag_id
          WHERE it.item_id = i.id AND t.id = %(tag_id)s AND t.owner_id = i.owner_id
      ))
)
"""

SEARCH_SQL = rf"""
WITH input AS NOT MATERIALIZED (
    SELECT CASE WHEN %(fts_probes)s::text[] IS NULL THEN plainto_tsquery('public.kt_vi', %(query)s)
                ELSE (SELECT string_agg(nullif(plainto_tsquery('public.kt_vi', probe)::text, ''), ' | ')::tsquery
                      FROM unnest(%(fts_probes)s::text[]) probes(probe)) END AS tsq,
           public.kt_search_fold(%(query)s) AS folded
),
{VISIBLE_ITEMS},
-- For the FIRST result page only, six (limit+1) or more visible FTS Item
-- matches already outrank every substring/typo score (which is <=1.0).
-- A bounded FTS probe lets PostgreSQL skip the costly fuzzy branch entirely
-- without changing the first-page Item ranking or next_cursor. Keep fuzzy
-- enabled on cursor pages so results below the FTS tier remain reachable.
-- Structured probes can share very common context words. In that case test
-- the value once and let the original literal substring use its own index.
fts_first_page AS MATERIALIZED (
    SELECT count(*) >= %(page_size)s AS enough
    FROM (
        SELECT i.id
        FROM visible_items i CROSS JOIN input
        WHERE %(fts_probes)s::text[] IS NULL AND {ITEM_VECTOR} @@ tsq AND {source_condition(ITEM_TEXT)}
        LIMIT %(page_size)s
    ) qualified
),
recent_captures AS MATERIALIZED (
    SELECT c.id, c.item_id, c.server_received_at
    FROM ingestion_captureevent c
    JOIN visible_items i ON i.id = c.item_id
    WHERE c.owner_id = %(owner_id)s AND c.raw_kind = 'link' AND c.raw_text <> ''
    ORDER BY c.server_received_at DESC, c.id
    LIMIT %(capture_limit)s
),
matches AS (
    SELECT i.id AS item_id, 'item' AS source, NULL::bigint AS derived_id,
           NULL::uuid AS capture_id, true AS fts, 1::real + ts_rank({ITEM_VECTOR}, tsq, 32) AS score,
           NULL::timestamptz AS received_at
    FROM visible_items i CROSS JOIN input
    WHERE {ITEM_VECTOR} @@ tsq AND {source_condition(ITEM_TEXT)}

    UNION ALL
    SELECT d.item_id, 'derived_content', d.id, NULL, true,
           1::real + ts_rank({DERIVED_VECTOR}, tsq, 32), NULL
    FROM processing_derivedcontent d
    JOIN visible_items i ON i.id = d.item_id CROSS JOIN input
    WHERE d.status = 'active' AND {DERIVED_VECTOR} @@ tsq AND {source_condition(DERIVED_TEXT)}

    UNION ALL
    SELECT i.id, 'item', NULL, NULL, false,
           -- A literal substring already is a direct match. Avoid invoking
           -- costly word_similarity across all matching Item bodies (10k
           -- candidates in the synthetic scale corpus); preserve the
           -- original fuzzy similarity for *non-substring* typo candidates.
           CASE WHEN %(substring)s AND strpos({ITEM_FOLD}, folded) > 0
                THEN 1.0::real
                ELSE word_similarity(folded, {ITEM_FOLD})
           END, NULL
    FROM visible_items i CROSS JOIN input CROSS JOIN fts_first_page fts_page
    WHERE (%(cursor_id)s::uuid IS NOT NULL OR NOT fts_page.enough)
      AND {source_condition(ITEM_TEXT)}
      AND ((%(substring)s AND {ITEM_FOLD} LIKE
               ('%%' || replace(replace(replace(folded, '!', '!!'), '%%', '!%%'), '_', '!_') || '%%')
               ESCAPE '!')
       OR (%(typo)s AND {ITEM_FOLD} OPERATOR(public.%%>) folded))

    UNION ALL
    SELECT c.item_id, 'capture_event', NULL, c.id, true,
           1::real + ts_rank({CAPTURE_VECTOR}, tsq, 32), r.server_received_at
    FROM recent_captures r JOIN ingestion_captureevent c ON c.id = r.id CROSS JOIN input
    WHERE {CAPTURE_VECTOR} @@ tsq AND {source_condition(CAPTURE_TEXT)}
),
evidence AS MATERIALIZED (
    SELECT DISTINCT ON (item_id, source) item_id, source, derived_id, capture_id, fts, score
    FROM matches
    ORDER BY item_id, source, score DESC, derived_id DESC, received_at DESC, capture_id DESC
),
page AS (
    SELECT item_id, max(score) AS score
    FROM evidence
    GROUP BY item_id
    HAVING %(cursor_id)s::uuid IS NULL
        OR (max(score), item_id) < (%(cursor_score)s::real, %(cursor_id)s::uuid)
    ORDER BY score DESC, item_id DESC
    LIMIT %(page_size)s
)
SELECT p.item_id, i.title, p.score, e.source,
       {evidence_excerpt(EVIDENCE_PASSAGE, STANDARD_EXCERPT)} AS snippet,
       d.source_locator::text,
       CASE e.source
            WHEN 'derived_content' THEN jsonb_build_object(
                'derived_content_id', d.id, 'asset_id', d.asset_id, 'kind', d.kind,
                'processor', d.processor, 'processor_version', d.processor_version,
                'input_hash', d.input_hash
            )
            WHEN 'capture_event' THEN jsonb_build_object(
                'capture_event_id', c.id, 'server_received_at', c.server_received_at
            )
            ELSE '{{}}'::jsonb
       END::text AS provenance
FROM page p JOIN visible_items i ON i.id = p.item_id
JOIN evidence e ON e.item_id = p.item_id
LEFT JOIN processing_derivedcontent d ON d.id = e.derived_id
LEFT JOIN ingestion_captureevent c ON c.id = e.capture_id
CROSS JOIN input
ORDER BY p.score DESC, p.item_id DESC, e.score DESC, e.source
"""
