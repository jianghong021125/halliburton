# Material and testing hierarchy queries

Paste each complete script into a separate Blank Query's Advanced Editor, enable load for tables needed in the model, and use these exact query names:

| Script | Power BI query name |
| --- | --- |
| material-master | Material Master |
| hier-codes | Product Hierarchies |
| material-with-ph | Material w/ PH |
| combined-labour-hours-spec | Testing Hours By PF |
| final-testing-by-pf | Final Testing By PF (last 3 years) |

The final script references Testing Hours By PF with uppercase By, as requested. If your existing query is named Testing Hours by PF, rename it or adjust the final script's Source reference to match exactly.

## Material w/ PH

The material table is the left side of a left outer join to Product Hierarchies, on Product_Hierarch = PRODH_PROD_HIER. All materials remain; unmatched hierarchy descriptions are null. Only the four requested material fields and four hierarchy descriptions are returned. MTRL_DESCRPTION follows the requested spelling exactly.

The lookup key PRODH_PROD_HIER must be unique. Having 2,048 hierarchy rows alone does not establish uniqueness. Material and hierarchy keys are explicitly typed as text to match the text MTRL_NBR in Testing Hours By PF and preserve hierarchy codes. No padding, trimming, or other key normalization is performed.

## Final Testing By PF (last 3 years)

All Testing Hours By PF columns are retained, with material and hierarchy attributes added through a left outer join on MTRL_NBR. The material join key is not expanded a second time.

Testing Hours By PF already has MRP_CNTRLR, so the added controller is named Material.MRP_CNTRLR. The existing MTRL_DESCRIPTION and the newly requested MTRL_DESCRPTION are both retained, allowing their different sources to be compared.

Material w/ PH must have at most one row per MTRL_NBR to preserve the testing row count. A unique hierarchy code does not guarantee unique material numbers in Material Master. Multiple material matches expand testing rows and repeat ACT_TM; resolve conflicting material records at source rather than arbitrarily discarding duplicates.

The final table inherits its date range from Testing Hours By PF. The current Anchor filters ACT_CMPL_DT >= 2024-01-01; no new rolling-three-year filter is added. The requested table name does not automatically update that cutoff as time passes.

## Performance and validation

Material and hierarchy columns are selected before joining. No Table.Buffer or blanket deduplication is added. The scripts reference existing queries, so those dependencies may run again when the final table refreshes. These merges can still be expensive; no refresh-time guarantee is implied.

Both new scripts passed Microsoft's Power Query syntax parser. Database execution and full refresh require validation in your PBIX: check key uniqueness, unmatched materials/hierarchies, and the final row count against Testing Hours By PF.
