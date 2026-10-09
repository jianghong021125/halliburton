# Material and testing hierarchy queries

Use the installation order and exact query names in [README-testing.md](README-testing.md).

## Material w/ PH

`material-master` supplies `Material Master`; `hier-codes` supplies `Product Hierarchies`. `material-with-ph` selects four material fields and left-joins product hierarchy on `Product_Hierarch = PRODH_PROD_HIER`, expanding descriptions for levels 2, 4, 5, and 6.

The output material fields are `MTRL_NBR`, `MRP_CNTRLR`, `MTRL_DESCRIPTION`, and `Product Hierarchy`. All materials remain; unmatched hierarchy descriptions are null. Material and hierarchy join keys are text, with no additional padding or trimming.

`PRODH_PROD_HIER` must be unique to avoid multiplying materials. The number of hierarchy rows alone does not establish uniqueness.

## Final Testing By PF (Since 2024)

The final query sources `Anchor Table Testing` directly and left-joins `Material w/ PH` on `MTRL_NBR` before joining the specification lookup. It expands only `Material.MRP_CNTRLR`, `Product Hierarchy`, and the four hierarchy descriptions. The added controller is aliased because Anchor already supplies `MRP_CNTRLR`; the original Anchor material description is retained without expanding a second description.

`Material w/ PH` must have at most one row per `MTRL_NBR` to preserve the Anchor row count at the material merge. Multiple material matches multiply rows and repeat ACT_TM. Check keys in the actual data and resolve conflicting source records rather than arbitrarily dropping duplicates.

The later specification join can legitimately expand rows further. Compare the material-merge row count with Anchor separately from the final specification-expanded count. Unmatched materials remain with null attributes; only unmatched specification/pillar values are replaced with empty text.

No material-source or hierarchy filtering rules have changed. The final table inherits Anchor's strict `LBR_STRT_DT > '2024-01-01'` cutoff and operation `OPR_PLNT_OID = 3`. Native `LBR_STRT_DT`/`LBR_END_DT` values remain in Anchor; the final table formats those labor-history dates as text.
