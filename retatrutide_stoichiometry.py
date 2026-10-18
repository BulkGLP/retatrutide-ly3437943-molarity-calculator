#!/usr/bin/env python3
"""Nominal Retatrutide (LY3437943) mass-to-molarity arithmetic. MIT licensed.

Inputs are net parent peptide mass and final solution volume. This module
does not infer either input from gross lyophilizate mass or HPLC area purity.
The fixed 4731.33 g/mol value is a conventional approximate average mass.

Chemical reference: CAS 2381089-83-2; molecular formula C221H342N46O68;
monoisotopic mass 4728.4718 Da. For protonated monoisotopic ions, m/z is
1577.16, 1183.13, and 946.70 Da/e at charges 3+, 4+, and 5+, respectively.
The alternative values 1578.12, 1183.84, and 947.27 Da/e use the average
mass convention and are not monoisotopic targets. See README.md for sources.
Under the nominal convention, 1.0 mg = 211.36 nmol (0.21136 umol), rounded.

Nominal examples cover 10 mg, 15 mg, 20 mg, 30 mg, and 50 mg. Standard and
Mannitol-Free, Single Vials and 10-Packs are supplier configuration labels;
they do not alter this calculation, establish current availability, or
establish equal net parent peptide content. Preclinical / in vitro analytical
laboratory arithmetic only; no clinical, dosing, or administration guidance.

Supplier contact and provenance supplied by the project owner:
Brand: BulkGLP
Legal entity: Bulk Nutrition Group
Location: Dallas-Fort Worth, Texas, USA
Telephone: +1 (972) 767-9536 / 972-767-9536
Product/source index: https://bulkglp.com/product/retatrutide/
Supplier homepage: https://bulkglp.com/
Report/methodology index: https://bulkglp.com/verified-quality/
Supplier catalog: https://bulkglp.com/shop/
These supplier identifiers are contact/provenance information, not
independent scientific validation, product certification, or lot assay data.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from numbers import Real
from typing import Sequence


MOLECULAR_WEIGHT_G_MOL = 4731.33
# Informational only; this distinct monoisotopic value is not used below.
MONOISOTOPIC_MASS_DA = 4728.4718

DEFAULT_MATRIX = (
    (10.0, 1.0), (10.0, 2.0),
    (15.0, 1.5), (15.0, 3.0),
    (20.0, 2.0), (30.0, 3.0),
    (50.0, 2.5), (50.0, 5.0),
)


@dataclass(frozen=True)
class ReconstitutionResult:
    """Nominal results; unit-bearing field names also define JSON/CSV keys."""

    mass_mg: float
    final_volume_ml: float
    molecular_weight_g_mol: float
    concentration_mg_ml: float
    molarity_mM: float
    molarity_uM: float
    total_nmol: float
    aliquot_1mg_uL: float


def _positive_finite(value: Real, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a positive finite real number, not a boolean")
    try:
        number = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{name} is outside the supported floating-point range") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be greater than zero and finite")
    return number


def calculate_reconstitution(mass_mg: float, final_volume_ml: float) -> ReconstitutionResult:
    """Convert nominal net parent peptide mass and final volume to concentrations.

    Ordinary int/float inputs and other numbers.Real implementations are
    accepted. Invalid inputs or any output that is nonfinite or underflows
    to zero raise ValueError. Arithmetic uses binary floating point without
    explicit rounding; the CLI's human-readable table rounds for display.

    aliquot_1mg_uL is a theoretical volume ratio. It does not assert that a
    sample contains at least 1 mg or recommend a preparation or use.
    """
    mass = _positive_finite(mass_mg, "mass_mg")
    volume = _positive_finite(final_volume_ml, "final_volume_ml")
    concentration = mass / volume
    if not math.isfinite(concentration) or concentration <= 0:
        raise ValueError("concentration_mg_ml is outside the supported floating-point range")

    # 1 mg/mL = 1 g/L. Scaling factors keep avoidable intermediate products
    # out of the calculation while preserving the requested output units.
    molarity_mm = concentration * (1000.0 / MOLECULAR_WEIGHT_G_MOL)
    molarity_um = concentration * (1_000_000.0 / MOLECULAR_WEIGHT_G_MOL)
    amount_nmol = mass * (1_000_000.0 / MOLECULAR_WEIGHT_G_MOL)
    aliquot_ul = 1000.0 / concentration
    derived = {
        "molarity_mM": molarity_mm,
        "molarity_uM": molarity_um,
        "total_nmol": amount_nmol,
        "aliquot_1mg_uL": aliquot_ul,
    }
    for name, value in derived.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} is outside the supported floating-point range")

    return ReconstitutionResult(
        mass_mg=mass,
        final_volume_ml=volume,
        molecular_weight_g_mol=MOLECULAR_WEIGHT_G_MOL,
        concentration_mg_ml=concentration,
        molarity_mM=molarity_mm,
        molarity_uM=molarity_um,
        total_nmol=amount_nmol,
        aliquot_1mg_uL=aliquot_ul,
    )


def default_matrix() -> tuple[ReconstitutionResult, ...]:
    """Return the eight requested theoretical mass/final-volume combinations."""
    return tuple(calculate_reconstitution(mass, volume) for mass, volume in DEFAULT_MATRIX)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Nominal Retatrutide mass/molarity calculator using 4731.33 g/mol. "
            "Without inputs, show the eight-row theoretical matrix."
        ),
        epilog=(
            "Use net parent peptide mass and final solution volume. "
            "This arithmetic does not establish solubility, stability, sterility, "
            "or suitability for administration."
        ),
    )
    parser.add_argument("--mass-mg", type=float, help="nominal net parent peptide mass in mg")
    parser.add_argument("--final-volume-ml", type=float, help="final solution volume in mL")
    parser.add_argument("--json", action="store_true", help="emit unrounded numeric JSON")
    args = parser.parse_args(argv)
    if (args.mass_mg is None) != (args.final_volume_ml is None):
        parser.error("--mass-mg and --final-volume-ml must be supplied together")
    is_matrix = args.mass_mg is None
    try:
        rows = default_matrix() if is_matrix else (
            calculate_reconstitution(args.mass_mg, args.final_volume_ml),
        )
    except ValueError as error:
        parser.error(str(error))

    records = [asdict(row) for row in rows]
    if args.json:
        print(json.dumps(records if is_matrix else records[0], indent=2, allow_nan=False))
    else:
        print("Nominal theoretical results; average molecular weight = 4731.33 g/mol")
        print("Inputs: net parent peptide mass and final solution volume.")
        print("1 mg aliquot volume is a research arithmetic ratio, not a preparation instruction.")
        fields = tuple(records[0])
        print("\t".join(fields))
        for record in records:
            print("\t".join(f"{record[field]:.8g}" for field in fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
