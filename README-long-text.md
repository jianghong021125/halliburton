# Testing specifications from operation long text

This workflow replaces the earlier material/specification lookup and operation-description filters documented in README-testing.md.

## Install

Paste the scripts into Power BI Advanced Editor in this order:

| Script | Power BI query name |
| --- | --- |
| confirmation-number-long-text | Confirmation Number <-> LNG_TXT |
| spec-testing-hours | Anchor Table Testing |
| combined-labour-hours-spec | Testing Hours By PF |

Use the exact existing query name if your PBIX spells "by" differently. Other scripts have not changed.

The lookup connects to SCGReporting / AP101_MPM. It inner-joins dbo.PROD_ORDR_OPR to dbo.PROD_ORDR on PROD_ORDR.OID = PROD_ORDR_OPR.PROD_ORDR_OID, to dbo.PROD_ORDR_OPR_LNG on PROD_ORDR_OPR_LNG.PROD_ORDR_OPR_OID = PROD_ORDR_OPR.OID, and to dbo.WRK_CNTR on WRK_CNTR.OID = PROD_ORDR_OPR.WRK_CNTR_OID. It returns LNG_TXT and CNFRM_NBR, then adds P_LNG_TXT; OID is no longer an output column. Confirmation numbers use the same leading-zero/space removal as Anchor and remain text.

Anchor left-joins this lookup by CNFRM_NBR and expands LNG_TXT and P_LNG_TXT only. OID is not expanded. The description exclusion and TEST requirement are removed; existing plant, status, and completion-date SQL filters remain.

## Text rules

- Balanced round, square, and curly bracket sections are removed, including their delimiters and nested sections. Unmatched delimiters remain.
- After bracket removal, double quotes immediately adjacent to an ASCII digit on either side are treated as literal characters, not quote delimiters. Remaining quote marks are paired in order and their enclosed text and delimiters removed. An unmatched quote remains.
- Null long text produces null processed text.
- ES matching is case-sensitive: each literal ES- begins a candidate.
- A candidate contains ES- plus up to 13 following characters, including spaces in that limit. It stops earlier at the next ES- or a character in SpecDelimiters at the top of the combined script.
- SpecDelimiters includes commas, semicolons, colons, periods, slashes, backslashes, pipes, brackets, quotes, exclamation/question marks, equals, plus, ampersand, asterisks, tabs, and line breaks. Hyphens remain part of a specification.
- A space ends the specification unless the word collected so far ends with a hyphen. Spaces following a hyphen are skipped and the next word is joined: ES-T- 82 becomes ES-T-82, but ES-T-82 TEST stops at ES-T-82. Repeated spaces after a hyphen are allowed. Spaces still count toward the 13-character limit before joining. No further code-format validation is performed.
- Each occurrence becomes a separate ES SPECS row. Repeated codes remain repeated. Null text, no matches, or a bare ES- produce no output rows.
- Specification Pillar uses the existing rule: prefix before the first hyphen plus the uppercase letters in the next segment. ES-T-82 and ES-T82-REV produce ES-T.
- There is no ES-T-only filter in the combined query now. All extracted pillars remain.

| Input long text | Extracted ES SPECS |
| --- | --- |
| (ES-T-99) ES-T-82 | ES-T-82 |
| "obsolete ES-T-99 text" ES-T-82 | ES-T-82 |
| 5" DIA; ES-T-82 | ES-T-82 |
| ES-T- 82,ES-P-12 | ES-T-82; ES-P-12 (two rows) |
| ES-T-82 TEST | ES-T-82 |
| ES-T - 82 | ES-T |
| ES-T-82*ES-P-12 | ES-T-82; ES-P-12 (two rows) |
| ES-12345678901234567 | ES-1234567890123 |

## Model and performance

Existing measures referencing Specification must switch to ES SPECS. ACT_TM is copied to every expanded occurrence; continue counting it once per confirmation for full-confirmation totals.

Cleanup runs in the narrow long-text query before the Anchor merge. The cleaner scans bracket/quote positions rather than accumulating every character. ES extraction searches match positions and examines at most 16 characters per candidate. No large-table buffer or deduplication is introduced.

The SQL lookup filters LNG_TXT IS NOT NULL and dbo.PROD_ORDR.PLNT_OID = 3 before transferring or cleaning text. The inner work-center join also requires a matching WRK_CNTR record. It does not filter the operation's OPR_PLNT_OID and has no date restriction. More than one matching long-text record per confirmation can expand Anchor rows. Referenced queries may execute independently, so refresh speed still depends on the database, text volume, merge size, and Power BI memory.

The three changed/new M scripts passed Microsoft's Power Query parser. Twenty independent reference-model cases passed for cleanup and extraction rules. These were not executed in the Power Query engine; refresh and sample-value validation against the actual SQL Server remain necessary.
