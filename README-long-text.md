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

The new lookup connects to SCGReporting / AP101_MPM and joins dbo.PROD_ORDR_OPR to dbo.PROD_ORDR_OPR_LNG on OID, as requested. One OID column is returned because both joined OIDs are equal, along with CNFRM_NBR, LNG_TXT, and P_LNG_TXT. Confirmation numbers use the same leading-zero/space removal as Anchor and remain text.

Anchor left-joins this lookup by CNFRM_NBR and expands LNG_TXT and P_LNG_TXT only. OID is not expanded. The description exclusion and TEST requirement are removed; existing plant, status, and completion-date SQL filters remain.

## Text rules

- Balanced round, square, and curly bracket sections are removed, including their delimiters and nested sections. Unmatched delimiters remain.
- After bracket removal, double quotes immediately adjacent to an ASCII digit on either side are treated as literal characters, not quote delimiters. Remaining quote marks are paired in order and their enclosed text and delimiters removed. An unmatched quote remains.
- Null long text produces null processed text.
- ES matching is case-sensitive: each literal ES- begins a candidate.
- A candidate contains ES- plus up to 13 following characters, including spaces in that limit. It stops earlier at the next ES- or a character in SpecDelimiters at the top of the combined script.
- SpecDelimiters includes commas, semicolons, colons, periods, slashes, backslashes, pipes, brackets, quotes, exclamation/question marks, equals, plus, ampersand, tabs, and line breaks. Ordinary spaces and hyphens are allowed.
- Spaces are removed after extraction. No further validation of the code format is performed; following prose without a delimiter can be included up to the length limit.
- Each occurrence becomes a separate ES SPECS row. Repeated codes remain repeated. Null text, no matches, or a bare ES- produce no output rows.
- Specification Pillar uses the existing rule: prefix before the first hyphen plus the uppercase letters in the next segment. ES-T-82 and ES-T82-REV produce ES-T.
- There is no ES-T-only filter in the combined query now. All extracted pillars remain.

| Input long text | Extracted ES SPECS |
| --- | --- |
| (ES-T-99) ES-T-82 | ES-T-82 |
| "obsolete ES-T-99 text" ES-T-82 | ES-T-82 |
| 5" DIA; ES-T-82 | ES-T-82 |
| ES-T - 82,ES-P-12 | ES-T-82; ES-P-12 (two rows) |
| ES-12345678901234567 | ES-1234567890123 |

## Model and performance

Existing measures referencing Specification must switch to ES SPECS. ACT_TM is copied to every expanded occurrence; continue counting it once per confirmation for full-confirmation totals.

Cleanup runs in the narrow long-text query before the Anchor merge. The cleaner scans bracket/quote positions rather than accumulating every character. ES extraction searches match positions and examines at most 16 characters per candidate. No large-table buffer or deduplication is introduced.

The SQL lookup has no extra plant/date restrictions. More than one matching long-text record per confirmation can expand Anchor rows. Referenced queries may execute independently, so refresh speed still depends on the database, text volume, merge size, and Power BI memory.

The three changed/new M scripts passed Microsoft's Power Query parser. Twenty independent reference-model cases passed for cleanup and extraction rules. These were not executed in the Power Query engine; refresh and sample-value validation against the actual SQL Server remain necessary.
