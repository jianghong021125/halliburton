# Confirmation-to-specification SQL lookup

The Power BI query `Confirmation Number <-> LNG_TXT` now returns a native SQL result only. Paste `confirmation-number-long-text` into its Advanced Editor. Its SQL is kept identical to `cnfrm-to-spec-query`.

## Selection and matching

1. Eligible operations must be completed, have operation `OPR_PLNT_OID = 3`, operation plant code `2088`, and production-order `PLNT_OID = 3`. They must also have an eligible labor-history summary whose earliest `LBR_STRT_DT` is strictly after `2024-01-01`. The query requires matching production order, work center, labor summary, plant, and non-null long-text records.
2. An EXISTS condition limits BOM candidates to those production-order numbers without multiplying BOM rows by their operations. Only null `CMPNT_MTRL_OID` and nonblank document numbers qualify.
3. ROW_NUMBER selects the latest `VLD_FRM_DT` per production-order number/document number. Equal dates retain the original query's unspecified tie selection; the selected output fields are identical for exact-key/date ties.
4. The latest documents join to eligible operations by raw production-order number and `LNG_TXT LIKE '%' + DOC_NBR + '%'`.
5. The six returned fields are `PROD_ORDR_NBR`, `CNFRM_NBR`, `WRK_CNTR_CD`, `LNG_TXT`, `DOC_NBR`, and `VLD_FRM_DT`. Only output confirmation numbers receive Anchor's existing SUBSTRING/PATINDEX leading-zero/space normalization. No BIGINT conversion is used.

The BOM joins are inner joins because the original nonblank-DOC_NBR condition already rejected unmatched BOM rows.

The labor summary groups by confirmation number, using `MIN(LBR_STRT_DT)` after applying the same labor filters as Anchor: plant 3 or 4, nondeleted rows, and labor type other than `I`. The date is aggregated before the cutoff is applied, so labor hours are not truncated by filtering individual history rows. The cutoff is a timestamp comparison: midnight on January 1, 2024 is excluded, while later times that day qualify. No `PROD_ORDR_OPR.ACT_STRT_DT` or `ACT_CMPL_DT` value is used.

Matching uses original text, including brackets and quotes. There is no cleaning, delimiter handling, 13-character limit, or joining words across spaces. A document must exist on the production order's qualifying BOM. Substring matches are intentional: a shorter document number can match within a longer token. SQL collation controls LIKE case/accent behavior, and document characters such as %, _, or [ retain their SQL wildcard meanings. Document numbers are tested for blankness but are not otherwise trimmed or normalized.

Repeated mentions of the same document within one long-text record produce one match, not one row per mention. Multiple long-text records can still produce repeated confirmation/document rows. No deduplication is performed.

## Final table behavior

Anchor no longer depends on this lookup. The final query left-joins it by text `CNFRM_NBR`, expanding only long text, document number as `Specification`, and the pillar calculated on the narrow lookup.

| Specification | Specification Pillar |
| --- | --- |
| ES-T-82 | ES-T |
| ES-T82-REV | ES-T |
| ES-P-123 | ES-P |
| 91K01234 | 91K01234 |
| ABC-123 | ABC-123 |
| es-t-82 | es-t-82 |
| No lookup match | Empty text |

For the literal uppercase prefix `ES-`, the rule is the first segment plus a hyphen plus uppercase A-Z letters from the second segment. All other specifications are unchanged. No extra code-format validation or case normalization is added. SQL excludes null/blank DOC_NBR before pillar calculation, so no repeated null guard is needed.

An unmatched operation has empty text in Specification and Specification Pillar and null LNG_TXT, even if raw long text exists but no BOM document matched. All Anchor operations remain. ACT_TM is copied, not divided, when the join expands rows.

See [installation and migration](README-testing.md) for the final query and validation limitations.
