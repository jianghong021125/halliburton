"""Synthetic SQL and reference-model checks, not SQL Server/M runtime tests."""

from collections import Counter
from pathlib import Path
import re
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "cnfrm-to-spec-query").read_text()


def patindex(pattern, value):
    assert pattern == "%[^0 ]%"
    return next((i + 1 for i, char in enumerate(value) if char not in "0 "), 0)


def substring(value, start, length):
    # SQL Server SUBSTRING is one-based; starts below one shorten the result.
    return value[max(start - 1, 0):max(start - 1 + length, 0)]


def normalize(value):
    return substring(value, patindex("%[^0 ]%", value + " "), len(value.rstrip(" ")))


def sqlite_sql(sql):
    # The fixture uses a small T-SQL subset. Keep SQL structure/joins/windows intact.
    return sql.replace("AP101_MPM.dbo.", "").replace(" + ", " || ")


def pillar(specification):
    """Independent reference model of the final query's pillar expression."""
    if specification.startswith("ES-"):
        parts = specification.split("-")
        return parts[0] + "-" + "".join(c for c in parts[1] if "A" <= c <= "Z")
    return specification


def final_rows(anchor, materials, lookup):
    """Reference model of the two M left joins; deliberately preserves duplicates."""
    output = []
    for operation in anchor:
        material_matches = [m for m in materials if m["MTRL_NBR"] == operation["MTRL_NBR"]]
        spec_matches = [s for s in lookup if s[1] == operation["CNFRM_NBR"]]
        for material in material_matches or [None]:
            for spec in spec_matches or [None]:
                output.append({
                    **operation,
                    "Product Hierarchy": material["Product Hierarchy"] if material else None,
                    "LNG_TXT": spec[3] if spec else None,
                    "Specification": spec[4] if spec else "",
                    "Specification Pillar": pillar(spec[4]) if spec else "",
                })
    return output


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.create_function("PATINDEX", 2, patindex)
        self.db.create_function("LEN", 1, lambda s: len(s.rstrip(" ")))
        self.db.create_function("SUBSTRING", 3, substring)
        self.db.executescript("""
            CREATE TABLE PROD_ORDR (OID INTEGER, PROD_ORDR_NBR TEXT, PLNT_OID INTEGER);
            CREATE TABLE PROD_ORDR_OPR (
                OID INTEGER, PROD_ORDR_OID INTEGER, CNFRM_NBR TEXT,
                WRK_CNTR_OID INTEGER, OPR_PLNT_OID INTEGER,
                MPM_ORDR_OPR_STAT_CD TEXT, ACT_CMPL_DT TEXT);
            CREATE TABLE PROD_ORDR_OPR_LNG (PROD_ORDR_OPR_OID INTEGER, LNG_TXT TEXT);
            CREATE TABLE WRK_CNTR (OID INTEGER, WRK_CNTR_CD TEXT);
            CREATE TABLE PLNT (OID INTEGER, PLNT_CD TEXT);
            CREATE TABLE PROD_ORDR_BOM (OID INTEGER, PROD_ORDR_OID INTEGER);
            CREATE TABLE PROD_ORDR_BOM_DTL (
                PROD_ORDR_BOM_OID INTEGER, DOC_NBR TEXT,
                CMPNT_MTRL_OID INTEGER, VLD_FRM_DT TEXT);
            INSERT INTO PROD_ORDR VALUES (1, '000500', 3), (2, '000600', 4), (3, '000700', 3);
            INSERT INTO WRK_CNTR VALUES (1, 'TEST-WC');
            INSERT INTO PLNT VALUES (3, '2088'), (4, '2088');
            INSERT INTO PROD_ORDR_BOM VALUES (1, 1), (2, 2);
        """)
        documents = [
            (1, "ES-T-82", None, "2024-01-01"),
            (1, "ES-T-82", None, "2025-02-01"),
            (1, "ES-T-82", 99, "2026-01-01"),
            (1, "ES-P-12", None, "2024-02-01"),
            (1, "91K01234", None, "2024-03-01"),
            (1, "ABC-123", None, "2024-04-01"),
            (1, "ES-T-99", None, "2024-05-01"),
            (1, "ES-T-77", None, "2024-06-01"),
            (1, "ES-T82-REV", None, "2024-07-01"),
            (1, "DOC_A1", None, "2024-08-01"),
            (1, "WILD%Z", None, "2024-09-01"),
            (1, None, None, "2026-01-01"),
            (1, "   ", None, "2026-01-01"),
            (1, "COMPONENT-DOC", 99, "2026-01-01"),
            (2, "ES-T-82", None, "2025-01-01"),
        ]
        self.db.executemany("INSERT INTO PROD_ORDR_BOM_DTL VALUES (?, ?, ?, ?)", documents)
        self.operation(1, " 000123", text='ES-T-82 ES-T-82 ES-P-12 91K01234 ABC-123 (ES-T-99) "ES-T-77" DOC-A1 WILDxyzZ COMPONENT-DOC')
        self.operation(2, "000124")
        self.operation(3, "000125", plant=4)
        self.operation(4, "000126", date="2023-12-31")
        self.operation(5, "000127", status="O")
        self.operation(6, "000128", order=2)
        self.operation(7, "000129", work_center=99)
        self.operation(8, "000130", text=None)
        self.operation(9, "000131", has_long_text=False)
        self.operation(10, "000132", text="No matching document")
        self.operation(11, "000133", date="2024-01-01", text="ES-T82-REV")
        self.operation(12, "000134", order=3)
        self.db.execute("INSERT INTO PROD_ORDR_OPR_LNG VALUES (1, 'ES-T-82')")

    def operation(self, oid, confirmation, *, order=1, plant=3, date="2025-06-01",
                  status="C", work_center=1, text="ES-T-82", has_long_text=True):
        self.db.execute("INSERT INTO PROD_ORDR_OPR VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (oid, order, confirmation, work_center, plant, status, date))
        if has_long_text:
            self.db.execute("INSERT INTO PROD_ORDR_OPR_LNG VALUES (?, ?)", (oid, text))

    def lookup(self):
        return self.db.execute(sqlite_sql(SQL)).fetchall()

    def test_six_columns_and_text_key_normalization(self):
        cursor = self.db.execute(sqlite_sql(SQL))
        self.assertEqual([c[0] for c in cursor.description],
                         ["PROD_ORDR_NBR", "CNFRM_NBR", "WRK_CNTR_CD", "LNG_TXT", "DOC_NBR", "VLD_FRM_DT"])
        self.assertEqual({r[1] for r in cursor}, {"123", "124", "133"})

    def test_scope_excludes_each_ineligible_operation(self):
        confirmations = {r[1] for r in self.lookup()}
        for excluded in ("125", "126", "127", "128", "129", "130", "131", "132", "134"):
            with self.subTest(confirmation=excluded):
                self.assertNotIn(excluded, confirmations)
        self.assertIn("133", confirmations)  # Includes the exact start-date boundary.

    def test_operation_plant_code_is_required(self):
        self.db.execute("UPDATE PLNT SET PLNT_CD = '9999' WHERE OID = 3")
        self.assertEqual(self.lookup(), [])

    def test_latest_qualifying_bom_date(self):
        self.assertEqual({r[5] for r in self.lookup() if r[4] == "ES-T-82"}, {"2025-02-01"})

    def test_non_es_brackets_quotes_and_sql_wildcards(self):
        specs = {r[4] for r in self.lookup() if r[1] == "123"}
        self.assertTrue({"91K01234", "ABC-123", "ES-T-99", "ES-T-77", "DOC_A1", "WILD%Z"} <= specs)
        self.assertNotIn("COMPONENT-DOC", specs)
        self.assertNotIn("   ", specs)
        self.assertNotIn(None, specs)

    def test_mentions_do_not_multiply_but_long_text_rows_do(self):
        matches = [r for r in self.lookup() if r[1] == "123" and r[4] == "ES-T-82"]
        self.assertEqual(len(matches), 2)  # Three mentions in two long-text records.

    def test_equivalent_to_scoped_original_query(self):
        baseline = (ROOT / "tests/fixtures/original-cnfrm-to-spec.sql").read_text()
        baseline = baseline.replace("WHERE L.LNG_TXT IS NOT NULL", """
            WHERE L.LNG_TXT IS NOT NULL
              AND O.OPR_PLNT_OID = 3
              AND O.MPM_ORDR_OPR_STAT_CD = 'C'
              AND O.ACT_CMPL_DT >= '2024-01-01'
              AND EXISTS (SELECT 1 FROM AP101_MPM.dbo.PLNT G
                          WHERE G.OID = O.OPR_PLNT_OID AND G.PLNT_CD = '2088')
        """)
        expected = [(r[0], normalize(r[1]), *r[2:])
                    for r in self.db.execute(sqlite_sql(baseline))]
        self.assertEqual(Counter(self.lookup()), Counter(expected))

    def test_reference_final_left_joins_keep_all_anchor_rows(self):
        anchor = [
            {"CNFRM_NBR": "123", "MTRL_NBR": "M1", "ACT_TM": 5},
            {"CNFRM_NBR": "124", "MTRL_NBR": "MISSING", "ACT_TM": 3},
            {"CNFRM_NBR": "999", "MTRL_NBR": "MISSING", "ACT_TM": 2},
        ]
        materials = [{"MTRL_NBR": "M1", "Product Hierarchy": "PACKERS"}]
        actual = final_rows(anchor, materials, self.lookup())
        self.assertEqual({r["CNFRM_NBR"] for r in actual}, {"123", "124", "999"})
        self.assertTrue(all(r["ACT_TM"] == {"123": 5, "124": 3, "999": 2}[r["CNFRM_NBR"]] for r in actual))
        self.assertTrue(all(r["Product Hierarchy"] is None for r in actual if r["CNFRM_NBR"] == "124"))
        unmatched = next(r for r in actual if r["CNFRM_NBR"] == "999")
        self.assertEqual((unmatched["Specification"], unmatched["Specification Pillar"]), ("", ""))
        self.assertIsNone(unmatched["LNG_TXT"])
        self.assertIsNone(unmatched["Product Hierarchy"])

    def test_reference_model_does_not_hide_duplicate_materials(self):
        anchor = [{"CNFRM_NBR": "124", "MTRL_NBR": "M1", "ACT_TM": 3}]
        materials = [{"MTRL_NBR": "M1", "Product Hierarchy": "PACKERS"}] * 2
        self.assertEqual(len(final_rows(anchor, materials, self.lookup())), 2)


class ScriptContractTests(unittest.TestCase):
    def test_embedded_sql_matches_reference(self):
        source = (ROOT / "confirmation-number-long-text").read_text()
        embedded = re.search(r'Query\s*=\s*"(.*?)"\s*\]', source, re.S).group(1)
        self.assertEqual(embedded.strip(), SQL.strip())
        self.assertTrue(source.rstrip().endswith("in\n    Source"))

    def test_anchor_scope_and_removed_dependency(self):
        source = (ROOT / "spec-testing-hours").read_text()
        self.assertIn("A1.[OPR_PLNT_OID] = 3", source)
        self.assertIn("WHERE PLNT_OID IN (3,4)", source)  # Labor-history scope stays unchanged.
        self.assertNotIn("LNG_TXT", source)
        self.assertNotIn("Table.NestedJoin", source)

    def test_final_query_contract(self):
        source = (ROOT / "final-testing-by-pf").read_text()
        self.assertIn('Source = #"Anchor Table Testing"', source)
        self.assertEqual(source.count("JoinKind.LeftOuter"), 2)
        self.assertLess(source.index('#"Merged Materials" ='), source.index('#"Merged Specifications" ='))
        self.assertLess(source.index('#"Added Specification Pillar" ='), source.index('#"Merged Specifications" ='))
        self.assertIn('if Text.StartsWith([DOC_NBR], "ES-") then', source)
        self.assertIn('Parts{0} & "-" & Text.Select(Parts{1}, {"A".."Z"})', source)
        self.assertRegex(source, r'else\s+\[DOC_NBR\]')
        self.assertIn('Format = "M/dd/yyyy"', source)
        self.assertRegex(source, r'Table.ReplaceValue\(\s*#"Expanded Specifications",\s*null,\s*"",\s*Replacer.ReplaceValue,\s*\{"Specification", "Specification Pillar"\}')
        for forbidden in ('#"Testing Hours"', '#"Testing Hours By PF"', "ES SPECS", "P_LNG_TXT", "Table.Buffer", "Table.Distinct", "Table.Sort", "Table.SelectRows", "ACT_TM_WEIGHTED"):
            self.assertNotIn(forbidden, source)
        self.assertFalse((ROOT / "combined-labour-hours-spec").exists())

    def test_no_numeric_conversion_in_lookup(self):
        self.assertNotRegex(SQL.upper(), r"\b(?:BIGINT|CAST|CONVERT)\b")

    def test_reference_pillar_cases(self):
        cases = {"ES-T-82": "ES-T", "ES-T82-REV": "ES-T", "ES-P-123": "ES-P",
                 "91K01234": "91K01234", "ABC-123": "ABC-123", "es-t-82": "es-t-82",
                 "ES-123": "ES-", "ES-": "ES-"}
        for value, expected in cases.items():
            with self.subTest(specification=value):
                self.assertEqual(pillar(value), expected)


if __name__ == "__main__":
    unittest.main()
