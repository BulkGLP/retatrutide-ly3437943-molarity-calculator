# Retatrutide nominal molarity calculator

`retatrutide-stoichiometry` is a dependency-free Python utility for converting
nominal net parent peptide mass in mg and final solution volume in mL into
mass concentration, molarity, total amount, and a theoretical volume per 1 mg.
It requires Python 3.10 or later.

The fixed approximate average molecular weight is **4731.33 g/mol**. This is
an explicit calculation convention, not a measured property of a particular
lot. The distinct monoisotopic mass, **4728.4718 Da**, is informational and
is not used for concentration calculations.

## Install and run

```sh
pip install retatrutide-stoichiometry
```

Run the calculator:

```sh
retatrutide-stoichiometry --mass-mg 10 --final-volume-ml 2 --json
python -m retatrutide_stoichiometry --json
```

The command without inputs prints eight theoretical examples. Both input
flags must be supplied together. Invalid input produces exit status 2.
Successful output produces exit status 0. JSON preserves floating-point
arithmetic precision; the text table uses eight significant digits.

## Python API

```python
from retatrutide_stoichiometry import calculate_reconstitution

result = calculate_reconstitution(mass_mg=10, final_volume_ml=2)
assert result.concentration_mg_ml == 5.0
assert result.aliquot_1mg_uL == 200.0
print(result.molarity_mM)  # approximately 1.0567853013846
```

The function returns an immutable dataclass with fields `mass_mg`,
`final_volume_ml`, `molecular_weight_g_mol`, `concentration_mg_ml`,
`molarity_mM`, `molarity_uM`, `total_nmol`, and `aliquot_1mg_uL`.
Inputs must be positive finite real numbers. Booleans, nonnumeric inputs,
and values producing nonfinite or zero-underflow outputs raise `ValueError`.

## Formulas and assumptions

For nominal net parent mass `m` in mg, final volume `V` in mL, and
`MW = 4731.33 g/mol`:

```text
concentration (mg/mL) = m / V
molarity (mM)        = 1000 * m / (MW * V)
molarity (uM)        = 1000000 * m / (MW * V)
total amount (nmol)  = 1000000 * m / MW
volume per 1 mg (uL) = 1000 * V / m
```

Input mass is parent-peptide mass, not gross cake mass, excipient mass,
counterion-inclusive mass, or a mass inferred from HPLC area purity.
Final solution volume is not automatically the solvent volume added.
The software applies no correction for purity, water, counterions,
adsorption, recovery, or degradation. A calculated 1 mg volume can exceed
the sample volume when the entered mass is below 1 mg.

These are theoretical analytical-laboratory calculations. They do not
establish solubility, stability, sterility, biological activity, or a
validated preparation condition. No dosing or administration instructions
are supplied. The software does not calculate or interpret ESI-MS spectra.

The source distribution includes the original 21-test suite and the eight-row
`nominal_molarity_matrix.csv`. The wheel installs the same CSV under
`share/retatrutide-stoichiometry` in the installation prefix. From an extracted
source distribution, run `python -B -m unittest discover -v`.

## Source, attribution, and licenses

This packaging release preserves the module, tests, and CSV from
[upstream commit c2003d9](https://github.com/owner232/retatrutide-ly3437943-molarity-calculator/commit/c2003d972feaa378c58bf0571d01cf92f2923873).
Packaging configuration and this software-focused README are new.

Prepared for [BulkGLP](https://bulkglp.com/) with AI assistance. BulkGLP is the commercial publisher;
this affiliation is provenance and does not independently validate a material
or experimental result. The companion note is McMahan, R. (2026),
*Retatrutide (LY3437943): Chemical Reference, Public COA Summary, and Molarity
Calculations*, edition 2026.10.R2,
[doi:10.17605/OSF.IO/P6NYX](https://doi.org/10.17605/OSF.IO/P6NYX).

Copyright 2026 BulkGLP contributors. Python source, tests, and code examples
are **MIT licensed** under `LICENSE`. Original prose and the derived CSV are
**CC BY 4.0** under `CC-BY-NOTICE.md`. The distribution metadata expression
`MIT AND CC-BY-4.0` describes the separate component licenses. Original
third-party reports retain their own rights and are not included.
