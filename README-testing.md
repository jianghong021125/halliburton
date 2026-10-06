# Consolidated testing-hours reporting

## Install in Power BI Advanced Editor

Use these exact query names. The final query depends directly on Anchor, materials, and the SQL specification lookup; no intermediate testing-hours query is required.

| Script | Power BI query name |
| --- | --- |
| `material-master` | `Material Master` |
| `hier-codes` | `Product Hierarchies` |
| `material-with-ph` | `Material w/ PH` |
| `confirmation-number-long-text` | `Confirmation Number <-> LNG_TXT` |
| `spec-testing-hours` | `Anchor Table Testing` |
| `final-testing-by-pf` | `Final Testing By PF (Since 2024)` |

Update the dependencies first and the final query last, without refreshing the old intermediate query between changes. `cnfrm-to-spec-query` is the SQL reference embedded in the confirmation lookup, not another Power BI query. The legacy `spec-to-mtrl_nbr` script remains available for unrelated uses but is not part of this workflow.

## Scope and output

- Anchor selects completed operations with `OPR_PLNT_OID = 3`, operation plant code `2088`, and `ACT_CMPL_DT >= '2024-01-01'`. This is a fixed cutoff, not a rolling three-year window.
- The specification lookup applies the same operation conditions, additionally requiring production-order `PLNT_OID = 3`, a matching work center, and non-null long text. An Anchor operation failing those extra conditions still survives the final left join, with blank specifications.
- Anchor has no long-text join. Its existing labor-history aggregation is unchanged: `PLNT_OID IN (3,4)`, nondeleted labor, and labor type other than `I`. This is a separate labor-history filter, not the operation-plant filter.
- The final query retains the previous 15 selected operation columns and formats `ACT_STRT_DT`/`ACT_CMPL_DT` as text using `M/dd/yyyy`. Anchor retains its original date/time columns.
- Materials are left-joined before specification expansion. The six added material attributes are `Material.MRP_CNTRLR`, `Product Hierarchy`, and hierarchy descriptions for levels 2, 4, 5, and 6. The original Anchor `MTRL_DESCRIPTION` is retained; no duplicate material description is expanded.
- The lookup adds `LNG_TXT`, `Specification` (from `DOC_NBR`), and `Specification Pillar`, for 24 final columns. Only unmatched specification/pillar nulls become empty text (`""`); unmatched long text and material attributes remain null.
- Every Anchor row survives, even without a specification. This includes operations not identified as testing. There is no operation-description TEST filter and no ES-T-only filter.
- `ACT_TM` is unchanged labor hours, not elapsed time. It repeats for multiple matching specifications, long-text records, or material records. No weighted-hours measure is introduced; a plain sum of expanded rows can overcount confirmation totals.

See [lookup rules](README-long-text.md) and [material hierarchy rules](README-material-hierarchy.md).

## Migrate an existing PBIX

1. Save a backup copy. Keep the final table's exact existing name.
2. Move measures whose home table is `Testing Hours` (or its former name `Testing Hours By PF`) to the final table or an existing measures table before deleting the old query.
3. Update DAX, visuals, filters, calculated tables, and relationships to use the final table. Replace `ES SPECS` references with `Specification`. `P_LNG_TXT` no longer exists: use original `LNG_TXT` only where the changed meaning is appropriate.
4. Replace the query definitions above. Delete the obsolete intermediate query, including any copy using the former name, and any remaining Power Query references to it. Its repository script `combined-labour-hours-spec` has been removed; do not create an alias for it.
5. Disable Enable load only for staging queries confirmed unused directly by model relationships, measures, or visuals. Referenced queries still evaluate when the final query refreshes; disabling load is not a cache.
6. Apply and refresh the backup PBIX. Check blank-specification behavior in visuals, date relationships, key uniqueness, row counts, and totals before replacing the working report.

No PBIX/model file is included in this repository. Repository edits do not automatically change installed query definitions, measures, visual bindings, relationships, or load settings.

## Efficiency and validation

The lookup filters operations and restricts BOM ranking in SQL. The final query selects narrow inputs, formats dates before expansion, and calculates pillars on the lookup before joining. No large-table buffering, full-table sorting, blanket deduplication, or error-swallowing fallback is added. CTEs do not guarantee materialization or physical execution order. Do not assume downstream M joins fold into these native SQL statements or that references share a cache; measure actual refresh time and database execution plans.

Run the local regression suite:

```sh
python3 -B -m unittest discover -s tests -v
node tests/parse-power-query.cjs /absolute/path/to/@microsoft/powerquery-parser
```

The Python suite runs adapted SQL on synthetic SQLite data and independent final-join/pillar reference models; it does not execute SQL Server or the M engine. The Node check uses Microsoft's M syntax parser, not a Power Query runtime.

Live acceptance checks: compare lookup results with the original SQL restricted to the same eligible operations; verify lookup keys and material/hierarchy uniqueness; verify all current Anchor operations survive and each expanded row retains its source ACT_TM. Expect differences from the old ES-occurrence extractor and from excluding operation plant 4. Investigate unexpected multiplicity rather than silently deduplicating. SQL Server execution, collation behavior, runtime types, and full PBIX refresh must still be checked against the actual database.
