"""Behavioral tests for the nominal Retatrutide calculator (MIT licensed)."""

import csv
import dataclasses
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "retatrutide_stoichiometry.py"


class CalculationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Calculator module must be supplied")
        self.calculator = importlib.import_module("retatrutide_stoichiometry")

    def test_one_micromole_in_one_milliliter_is_one_millimolar(self):
        # Independent dimensional anchor: 4.73133 mg is 1 umol at the
        # specified average molecular weight; 1 umol / 1 mL = 1 mM.
        result = self.calculator.calculate_reconstitution(4.73133, 1)
        self.assertAlmostEqual(result.concentration_mg_ml, 4.73133, places=12)
        self.assertAlmostEqual(result.molarity_mM, 1.0, places=12)
        self.assertAlmostEqual(result.molarity_uM, 1000.0, places=9)
        self.assertAlmostEqual(result.total_nmol, 1000.0, places=9)

    def test_five_mg_per_ml_requires_two_hundred_ul_per_mg(self):
        result = self.calculator.calculate_reconstitution(10, 2)
        self.assertEqual(result.concentration_mg_ml, 5.0)
        self.assertEqual(result.aliquot_1mg_uL, 200.0)

    def test_dilution_halves_concentration_and_preserves_amount(self):
        first = self.calculator.calculate_reconstitution(10, 1)
        second = self.calculator.calculate_reconstitution(10, 2)
        self.assertEqual(second.total_nmol, first.total_nmol)
        self.assertEqual(second.molarity_mM, first.molarity_mM / 2)
        self.assertEqual(second.aliquot_1mg_uL, first.aliquot_1mg_uL * 2)

    def test_equal_concentration_different_amounts(self):
        first = self.calculator.calculate_reconstitution(10, 1)
        second = self.calculator.calculate_reconstitution(20, 2)
        self.assertEqual(first.molarity_uM, second.molarity_uM)
        self.assertEqual(second.total_nmol, first.total_nmol * 2)

    def test_computation_does_not_round_to_display_precision(self):
        result = self.calculator.calculate_reconstitution(1, 3)
        self.assertEqual(result.concentration_mg_ml, 0.3333333333333333)

    def test_result_cannot_be_mutated(self):
        result = self.calculator.calculate_reconstitution(10, 2)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.mass_mg = 20

    def test_rejects_boolean_inputs(self):
        for mass, volume in ((True, 2), (False, 2), (10, True), (10, False)):
            with self.subTest(mass=mass, volume=volume), self.assertRaises(ValueError):
                self.calculator.calculate_reconstitution(mass, volume)

    def test_rejects_nonpositive_inputs(self):
        for invalid in (0, -0.0, -1, -1e300):
            for mass, volume in ((invalid, 2), (10, invalid)):
                with self.subTest(mass=mass, volume=volume), self.assertRaises(ValueError):
                    self.calculator.calculate_reconstitution(mass, volume)

    def test_rejects_nonfinite_inputs(self):
        for invalid in (float("nan"), float("inf"), -float("inf")):
            for mass, volume in ((invalid, 2), (10, invalid)):
                with self.subTest(mass=mass, volume=volume), self.assertRaises(ValueError):
                    self.calculator.calculate_reconstitution(mass, volume)

    def test_rejects_nonnumeric_inputs(self):
        for invalid in ("10", None, [], complex(10, 0)):
            for mass, volume in ((invalid, 2), (10, invalid)):
                with self.subTest(mass=mass, volume=volume), self.assertRaises(ValueError):
                    self.calculator.calculate_reconstitution(mass, volume)

    def test_rejects_input_conversion_overflow(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_reconstitution(10**1000, 2)

    def test_rejects_derived_overflow(self):
        for mass, volume in ((1e308, 1e-308), (1e308, 1e308), (1e-308, 1)):
            with self.subTest(mass=mass, volume=volume), self.assertRaises(ValueError):
                self.calculator.calculate_reconstitution(mass, volume)

    def test_rejects_derived_underflow_to_zero(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_reconstitution(1e-308, 1e308)

    def test_default_matrix_has_requested_order_and_arithmetic(self):
        rows = self.calculator.default_matrix()
        expected = [
            (10, 1, 10, 100), (10, 2, 5, 200),
            (15, 1.5, 10, 100), (15, 3, 5, 200),
            (20, 2, 10, 100), (30, 3, 10, 100),
            (50, 2.5, 20, 50), (50, 5, 10, 100),
        ]
        self.assertEqual(len(rows), 8)
        for row, (mass, volume, concentration, aliquot) in zip(rows, expected):
            with self.subTest(mass=mass, volume=volume):
                self.assertEqual((row.mass_mg, row.final_volume_ml), (mass, volume))
                self.assertEqual(row.concentration_mg_ml, concentration)
                self.assertEqual(row.aliquot_1mg_uL, aliquot)


class CommandLineTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, check=False,
        )

    def test_single_calculation_json_preserves_full_precision(self):
        completed = self.invoke("--mass-mg", "1", "--final-volume-ml", "3", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["concentration_mg_ml"], 0.3333333333333333)
        self.assertEqual(result["final_volume_ml"], 3.0)

    def test_default_json_contains_eight_rows(self):
        completed = self.invoke("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        rows = json.loads(completed.stdout)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["mass_mg"], 10.0)
        self.assertEqual(rows[-1]["final_volume_ml"], 5.0)

    def test_default_table_labels_nominal_inputs_and_outputs(self):
        completed = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("final_volume_ml", completed.stdout)
        self.assertIn("Nominal", completed.stdout)
        self.assertIn("4731.33", completed.stdout)
        self.assertIn("aliquot_1mg_uL", completed.stdout)

    def test_missing_paired_argument_exits_with_usage_error(self):
        for args in (("--mass-mg", "10"), ("--final-volume-ml", "2")):
            with self.subTest(args=args):
                completed = self.invoke(*args)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("error:", completed.stderr)
                self.assertEqual(completed.stdout, "")

    def test_invalid_numeric_argument_exits_cleanly(self):
        for invalid in ("0", "-1", "nan", "inf", "1e999", "true"):
            with self.subTest(invalid=invalid):
                completed = self.invoke("--mass-mg", invalid, "--final-volume-ml", "2", "--json")
                self.assertEqual(completed.returncode, 2)
                self.assertIn("error:", completed.stderr)
                self.assertNotIn("Traceback", completed.stderr)
                self.assertEqual(completed.stdout, "")

    def test_derived_overflow_exits_cleanly(self):
        completed = self.invoke("--mass-mg", "1e308", "--final-volume-ml", "1e-308", "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("error:", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(completed.stdout, "")


class PublishedMatrixTests(unittest.TestCase):
    def test_csv_contains_theoretical_eight_row_matrix(self):
        matrix_path = HERE / "nominal_molarity_matrix.csv"
        self.assertTrue(matrix_path.is_file(), "Derived CSV must be supplied")
        with matrix_path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 8)
        self.assertEqual(
            [(float(row["mass_mg"]), float(row["final_volume_ml"])) for row in rows],
            [(10, 1), (10, 2), (15, 1.5), (15, 3), (20, 2), (30, 3), (50, 2.5), (50, 5)],
        )
        self.assertEqual(float(rows[1]["concentration_mg_ml"]), 5.0)
        self.assertEqual(float(rows[1]["aliquot_1mg_uL"]), 200.0)
        # Back-convert each CSV amount to mass, independently of the module.
        for row in rows:
            with self.subTest(mass=row["mass_mg"], volume=row["final_volume_ml"]):
                recovered_mg = float(row["total_nmol"]) * 0.00473133
                self.assertAlmostEqual(recovered_mg, float(row["mass_mg"]), places=10)


if __name__ == "__main__":
    unittest.main()
