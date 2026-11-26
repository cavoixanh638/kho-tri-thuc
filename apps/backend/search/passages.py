"""Display the passage witnessing an explicit constraint on a ranked source."""


def evidence_excerpt(source, fallback):
    # Work on paged rows only. Keep the original spelling and unit case in
    # the excerpt. Vietnamese folding preserves NFC character offsets.
    last_claim = "coalesce(%(claim_action)s, (%(claim_patterns)s::text[])[cardinality(%(claim_patterns)s::text[])])"
    return rf"""CASE WHEN %(claim_patterns)s::text[] IS NULL AND %(claim_action)s::text IS NULL
                     AND %(quantity_required)s::text[] IS NULL
        THEN {fallback}
        ELSE coalesce((
            SELECT CASE WHEN length(piece) <= 320 THEN btrim(piece) ELSE
                substring(piece FROM greatest(1, coalesce(
                    regexp_instr(public.kt_search_fold(piece), {last_claim}),
                    regexp_instr(piece, (%(quantity_required)s::text[])[1]), 1) - 32) FOR 320) END
            FROM regexp_split_to_table({source}, '[!?\n;]+|[.](?![[:digit:]])')
                 WITH ORDINALITY AS passages(piece, ord)
            WHERE (%(claim_patterns)s::text[] IS NULL OR
                   public.kt_search_fold(piece) ~ ALL (%(claim_patterns)s::text[]))
              AND (%(quantity_required)s::text[] IS NULL OR piece ~ ALL (%(quantity_required)s::text[]))
              AND (%(quantity_labels)s::text[] IS NULL OR piece ~* ALL (%(quantity_labels)s::text[]))
              AND (%(claim_action)s::text IS NULL OR public.kt_search_fold(piece) ~ %(claim_action)s)
            ORDER BY CASE WHEN %(quantity_target)s::text IS NOT NULL THEN (
                SELECT count(*) FROM unnest(%(quantity_clues)s::text[]) AS clues(word)
                WHERE word = ANY(regexp_split_to_array(public.kt_search_fold(piece), '[^[:alnum:]]+'))
            ) END DESC, ord
            LIMIT 1
        ), {fallback}) END"""
