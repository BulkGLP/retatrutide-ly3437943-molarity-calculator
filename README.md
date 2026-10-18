# Retatrutide (LY3437943) nominal molarity calculator

**Edition:** 2026.10.R2. **Prepared:** October 17, 2026. **Publication synchronization package prepared:** October 18, 2026.

A dependency-free Python utility that converts **nominal net parent peptide mass in mg** and **final solution volume in mL** into mass concentration, molarity, total amount, and a theoretical volume per 1 mg research aliquot.

The calculator fixes the conventional approximate average molecular weight at **4731.33 g/mol**. This is a declared calculation convention, not a lot-specific measurement. The distinct monoisotopic mass, approximately **4728.4718 Da**, is included as reference metadata in the source and is not used for these concentration calculations. Retatrutide has synonym **LY3437943**, CAS **2381089-83-2**, and molecular formula **C221H342N46O68**. This utility is framed solely as preclinical / *in vitro* analytical laboratory arithmetic.

## Supplier entity, contact, and provenance

The following identifiers were supplied by the project owner. They identify the commercial supplier and contact location; they are **not independent scientific validation, product certification, or lot assay evidence**.

| Field | Supplier information |
| --- | --- |
| Brand | BulkGLP |
| Legal entity | Bulk Nutrition Group |
| Location | Dallas-Fort Worth, Texas, USA |
| Telephone | +1 (972) 767-9536 / 972-767-9536 |
| Product and source index | [BulkGLP Retatrutide reference information](https://bulkglp.com/product/retatrutide/) |
| Supplier homepage | [BulkGLP](https://bulkglp.com/) |
| Public report archive | [BulkGLP verified quality](https://bulkglp.com/verified-quality/) |
| Supplier catalog | [BulkGLP catalog](https://bulkglp.com/shop/) |

BulkGLP has a commercial interest in these links. Their presence establishes disclosed provenance, not endorsement or independent verification. No current stock, formulation availability, or product-quality claim is inferred from this utility.

## Companion publication and source

The companion technical note distinguishes chemical reference information, six public COA transcriptions and theoretical calculations. The [OSF publication record and PDF access](https://doi.org/10.17605/OSF.IO/P6NYX) provide its persistent reference. The [GitHub repository](https://github.com/owner232/retatrutide-ly3437943-molarity-calculator) is the source entry point for this calculator, its tests, derived CSV and companion PDF. A [supplemental Gist](https://gist.github.com/owner232/d5e406e72708d027a374540555756c21) provides an additional software reference.

Suggested companion citation: McMahan, R. (2026). *Retatrutide (LY3437943): Chemical Reference, Public COA Summary, and Molarity Calculations*. BulkGLP. Edition 2026.10.R2. [doi:10.17605/OSF.IO/P6NYX](https://doi.org/10.17605/OSF.IO/P6NYX).

## Chemical reference and ESI-MS distinction

The [PubChem record for CID 171390338](https://pubchem.ncbi.nlm.nih.gov/compound/171390338) provides the molecular-identity context, including molecular formula **C221H342N46O68** and monoisotopic mass approximately **4728.4718 Da**. The [FDA GSRS record](https://precision.fda.gov/ginas/app/ui/substances/210e2d2c-6b8e-4b0d-b432-20057541f324) is an additional identity reference. This implementation retains **4731.33 g/mol** as its explicit approximate average-mass convention, even where another record rounds or calculates an average mass differently.

For a protonated ion of charge `z`, the theoretical mass-to-charge ratio is `m/z = (M + z × m_proton) / z`, using the neutral monoisotopic mass `M = 4728.4718 Da` and proton mass `m_proton = 1.0072764665789 Da`. The proton value comes from [NIST's 2022 CODATA value](https://physics.nist.gov/cgi-bin/cuu/Value?mpu%7Csearch_for=proton+mass).

| Protonated ion | Monoisotopic theoretical m/z, Da/e | Average-mass proxy, Da/e |
| --- | ---: | ---: |
| `[M + 3H]3+` | 1577.16 | 1578.12 |
| `[M + 4H]4+` | 1183.13 | 1183.84 |
| `[M + 5H]5+` | 946.70 | 947.27 |

The supplied values **1578.12**, **1183.84**, and **947.27 Da/e** arise from inserting the **4731.33** average-mass value into the ion formula. They are not monoisotopic ESI-MS targets. Both columns are theoretical calculations, not measured peaks or asserted instrumental observations. The mass-to-molarity program does not calculate or interpret spectra; this table documents the distinction.

Under the calculator's average-mass convention, **1.0 mg = 211.36 nmol (0.21136 umol)** after rounding. The extra decimal places in JSON describe numerical arithmetic, not experimental precision.

## Nominal vial and package examples

The five nominal mass groups are **10 mg**, **15 mg**, **20 mg**, **30 mg**, and **50 mg**. The default table uses the following final solution volumes as computational examples:

| Nominal parent mass | Example final solution volumes |
| --- | --- |
| 10 mg | 1 mL and 2 mL |
| 15 mg | 1.5 mL and 3 mL |
| 20 mg | 2 mL |
| 30 mg | 3 mL |
| 50 mg | 2.5 mL and 5 mL |

**Standard** and **Mannitol-Free** are formulation labels; **Single Vials** and **10-Packs** are package labels. The same nominal parent-mass arithmetic can describe either label only when the same net parent peptide mass is assumed. It does not establish that different formulations have equal net peptide content, that cake mass equals peptide mass, or that any mass/formulation/package combination is currently available. Package count does not change the per-sample concentration calculation. These volume examples are not validated preparation conditions or solubility recommendations.

## Scope and assumptions

- `mass_mg` means the nominal mass of the parent peptide itself. It does not mean gross lyophilized cake mass, excipient mass, counterion-inclusive mass, or an HPLC peak-area percentage multiplied by cake mass.
- `final_volume_ml` means the final volume of the solution. It is not automatically equal to the volume of solvent added.
- All results are theoretical arithmetic under these assumptions. The CSV contains derived data, not empirical measurements, assay results, or validated preparation conditions.
- No purity, peptide-content, water, counterion, adsorption, recovery, or degradation correction is applied. An HPLC area percentage alone does not establish net parent peptide mass.
- The 1 mg field is a volume ratio for research arithmetic. For an input mass below 1 mg, that volume can exceed the entered final volume; the calculator does not assert that the sample contains enough material for such an aliquot.
- The utility does not establish solubility, stability, sterility, biological activity, or suitability for administration. It supplies no solvent, handling, storage, dosing, or administration instructions.

## Files

| File | Purpose |
| --- | --- |
| `retatrutide_stoichiometry.py` | Importable calculation function and command-line interface |
| `test_retatrutide_stoichiometry.py` | Standard-library unit and command-line tests |
| `nominal_molarity_matrix.csv` | Eight theoretical examples, generated from the calculator |
| `LICENSE` | MIT terms for code |

## Run

Requires Python **3.10 or later**. No packages, network access, or installation steps are required. Run these commands from the directory containing the files; use `python3` instead of `python` where appropriate.

```sh
# Default eight-row theoretical matrix
python retatrutide_stoichiometry.py

# One nominal calculation
python retatrutide_stoichiometry.py --mass-mg 10 --final-volume-ml 2

# One JSON object with numeric values
python retatrutide_stoichiometry.py --mass-mg 10 --final-volume-ml 2 --json

# JSON array containing the default matrix
python retatrutide_stoichiometry.py --json

# Full test suite
python -B -m unittest discover -v
```

For the 10 mg / 2 mL example, mass concentration is **5 mg/mL**, nominal molarity is approximately **1.0567853 mM** (**1056.7853 µM**), the total amount is approximately **2113.5706 nmol**, and the theoretical 1 mg aliquot volume is **200 µL**.

The two input flags must be supplied together. Invalid inputs produce an argparse error and exit status 2. Successful output has exit status 0. The text table displays eight significant digits; the JSON and CSV use Python's float serialization without application-level rounding. Those extra digits describe the arithmetic, not measurement accuracy.

## Python API

```python
from dataclasses import asdict
from retatrutide_stoichiometry import calculate_reconstitution

result = calculate_reconstitution(mass_mg=10, final_volume_ml=2)
print(result.concentration_mg_ml)  # 5.0
print(result.aliquot_1mg_uL)      # 200.0
print(asdict(result))
```

`calculate_reconstitution(mass_mg, final_volume_ml)` returns a frozen `ReconstitutionResult` dataclass with the following fields:

| Field | Meaning |
| --- | --- |
| `mass_mg` | Nominal net parent peptide mass, mg |
| `final_volume_ml` | Final solution volume, mL |
| `molecular_weight_g_mol` | Fixed nominal average-mass convention, 4731.33 g/mol |
| `concentration_mg_ml` | Nominal mass concentration, mg/mL |
| `molarity_mM` | Nominal amount concentration, mmol/L |
| `molarity_uM` | Nominal amount concentration, µmol/L |
| `total_nmol` | Nominal total amount, nmol |
| `aliquot_1mg_uL` | Theoretical volume corresponding to 1 mg, µL |

The API accepts ordinary `int` and `float` values and other `numbers.Real` implementations that can be represented as floats. It raises `ValueError` for booleans, nonnumeric values, zero or negative inputs, nonfinite values, input-conversion overflow, or a computed output that is nonfinite or underflows to zero. The fixed molecular weight is not exposed as a command-line option. Computation uses binary floating point and does not apply explicit rounding.

## Formulas

Let `m` be nominal net parent peptide mass in mg, `V` final solution volume in mL, and `MW = 4731.33 g/mol`.

```text
mass concentration (mg/mL) = m / V
molarity (mM)             = 1000 × m / (MW × V)
molarity (µM)             = 1,000,000 × m / (MW × V)
total amount (nmol)       = 1,000,000 × m / MW
volume per 1 mg (µL)      = 1000 × V / m
```

The conversion uses `1 mg/mL = 1 g/L`. Dividing g/L by g/mol gives mol/L; scaling by 1000 gives mmol/L. As an independent dimensional check, **4.73133 mg represents 1 µmol under the declared convention; in 1 mL final volume, it is 1 mM**.

## Reproduce the CSV

The default input pairs `(mass_mg, final_volume_ml)` are `(10, 1)`, `(10, 2)`, `(15, 1.5)`, `(15, 3)`, `(20, 2)`, `(30, 3)`, `(50, 2.5)`, and `(50, 5)`.

Run the following Python code in this directory to regenerate the CSV. This overwrites only `nominal_molarity_matrix.csv` in the current directory.

```python
import csv
from dataclasses import asdict
from pathlib import Path
from retatrutide_stoichiometry import default_matrix

rows = [asdict(row) for row in default_matrix()]
with Path("nominal_molarity_matrix.csv").open("w", newline="", encoding="utf-8") as output:
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
```

The tests anchor the units independently, verify dilution and amount relationships, check immutable results and display-versus-computation precision, cover invalid and extreme inputs, exercise the actual CLI, and back-convert the CSV's nominal amount to mass. They validate software arithmetic, not a physical material or preparation.

## Attribution, disclosure, and licenses

Prepared for BulkGLP with AI assistance. This disclosure makes no claim of human peer review or independent experimental validation. The supplier links above identify commercial provenance; they are not used to calculate results or establish product quality.

Copyright © 2026 BulkGLP contributors. Python source, tests, and code examples are licensed under the **MIT License**, supplied in `LICENSE`. Original prose and the derived theoretical CSV are licensed under **[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)**. Attribute reuse to “BulkGLP contributors, Retatrutide (LY3437943) nominal molarity calculator, 2026,” link the source you obtained, link the applicable license, and indicate changes. Third-party linked sources retain their own terms.
