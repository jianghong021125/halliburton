# Testing queries (0929-testing)

This branch starts from main (3fcc89f), whose combined query already references an Anchor query. It also carries the specification/material source from 0928-temp-changes, with material identifiers kept as text.

## Install in Power BI Advanced Editor

| Script | Exact Power BI query name |
| --- | --- |
| `spec-testing-hours` | `Anchor Table Testing` |
| `spec-to-mtrl_nbr` | `Specification <-> Material Number ( AP SPECS )` |
| `combined-labour-hours-spec` | `Testing Hours by PF` |

Update the Anchor and specification lookup first, then the combined query. If the lookup already exists, replace its code too so MTRL_NBR remains text on both sides of the join. No employee query is required. Material descriptions and other material attributes come from the Anchor; the lookup supplies distinct material/specification pairs.

## Rules and editable settings

- Anchor ends with two visible filter steps: exclude the exact description `SNG ICAT REVIEW PROCESS FOR TESTING ORN`, then retain descriptions containing `TEST` (case-insensitive). Null descriptions are excluded. Edit `ExcludedOperation` and `RequiredOperationText` at the top.
- Existing completed-operation, plant 2088, and completion-date-from-2024 filters remain unchanged. ACT_TM still sums labor seconds by confirmation and divides by 3600; this is labor time, not elapsed start-to-completion time.
- The combined query uses `Anchor Table Testing` as Source and retains ACT_TM. It adds no employee, Product Family, or weighted-time fields.
- Specification Pillar retains the original prefix/uppercase-letter rule for hyphenated values: `ES-T-82` and `ES-T82-REV` produce `ES-T`. Without a hyphen, it uses the first three characters: `91K01234` produces `91K`. Specifications must be non-null text. Edit `RequiredPillar` at the top of the combined query to change the filter; the current ES-T filter still excludes pillars such as 91K.
- Only materials with qualifying ES-T specifications survive the inner join. An operation with several distinct ES-T specifications produces several rows; ACT_TM repeats on those rows. This is not a one-row-per-confirmation output.
- In Testing Hours by PF, ACT_STRT_DT and ACT_CMPL_DT are formatted as text using `M/dd/yyyy` (for example, `9/05/2026`), without timestamps. Formatting runs before specification expansion. Anchor Table Testing retains the original date/time columns for date relationships or time intelligence. Identifier fields are text; check existing relationships if your model previously used numeric identifiers.

## Performance and validation

Unused SQL output expressions and the unused setup-hours aggregation were removed from Anchor. The full-table sort was removed. The specification lookup returns only distinct material/specification pairs in SQL and is filtered before the merge, so pillar parsing is performed on the lookup instead of the expanded fact rows. Redundant M selection, deduplication, and identifier text casts were removed. SQL SUBSTRING already supplies text join keys. No Table.Buffer is used.

The final Anchor filters are M steps as requested. With the existing Sql.Database native-query source, do not assume these steps or the merge fold to SQL. The source may still transfer all qualifying operations before the description filters execute. A referenced query also does not guarantee a shared cache or a single SQL execution during refresh. Measure actual refresh time with Power Query diagnostics; further SQL pushdown can be considered separately.

All three scripts passed syntax parsing with Microsoft's @microsoft/powerquery-parser. This checks M syntax, not SQL execution or runtime data types.

Validate in Power BI using the actual database: confirm all Anchor descriptions pass both rules, all final pillars equal ES-T, ACT_TM matches Anchor for each confirmation, and material keys match across both sources. Local checks do not replace a Power BI refresh against SCGReporting, which is not available in this workspace.
