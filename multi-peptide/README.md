---
language:
  - en
pretty_name: BulkGLP Multi-Peptide Molarity and COA Reference - Edition 2026.10.R3
tags:
  - chemistry
  - research-reference
  - commercial-affiliation
  - source-transcription
---

# BulkGLP multi-peptide registry - Edition 2026.10.R3

**44/44 catalog products are accounted for; full catalog molarity remains incomplete.** Publication readiness is a separate gate: complete accounting plus successful arithmetic, COA/source-integrity, link and disclosure verification. Explicit withholding never becomes invented chemical completeness.

This commercially affiliated, AI-assisted reference compilation cites supplier-hosted reports. It does not independently authenticate laboratory results or certify every fulfillment lot, formulation or product identity. Catalog captured October 22; scientific review October 24; withholding/release gate reviewed October 25, 2026. Publication/deployment and Google indexing are verified separately.

## Data and withholding

- 34 chemical-reference registry rows; **152 theoretical matrix rows across 30 products**; **49 public COA file entries across 28 products**, representing 47 distinct printed report IDs.
- `catalog_molarity_accounting.csv` and `catalog_dispositions_manifest.json`: all 44 products exactly once: 30 modeled peptide listings, 3 pending sequence/specification, 1 nomenclature conflict, 2 nonpeptide reference listings outside the peptide matrix, 8 explicit non-single-species exclusions.
- `catalog_withheld_stoichiometry.csv`: `foxo4-10mg`, `adamax`, `ahk-cu-10000mg` are `stoichiometry_withheld_pending_sequence_specification`; `thymalin-10mg` is `stoichiometry_withheld_catalog_coa_nomenclature_conflict`. None has assigned CAS/formula/molar mass or computed molarity.
- Catalog **Thymalin** is not equated with COA2608100933 **Thymulin** or the defined free **nonathymulin** candidate. Historical candidate metadata remain provenance only; no 858.9 g/mol Thymalin matrix is published.
- Both GHK-Cu listings retain neutral 1:1 CAS89030-95-5 / C14H22CuN6O4 / **401.91 g/mol** as a conditional reference convention, without certifying lot composition.
- TB-500 retains the COA-named full-length thymosin beta-4/timbetasin reference, **4963 g/mol**; not the Ac-LKKTETQ fragment. The commercial name alone does not identify every lot or variant.

`full_catalog_accounted_for:true` and `full_catalog_molarity_complete:false` are both intentional. `publication_ready` can be true only when all integrity/disclosure checks pass. Neither flag claims deployment, indexing, independent validation or measured lot concentrations.

## Retatrutide reference conventions and COA scope

R3 uses PubChem's source-rounded **4731 g/mol** convention. The existing historical Retatrutide calculator retains **4731.33 g/mol**; preserve its URLs, filenames and calculations during additive R3 publication. Do not silently overwrite the historical convention.

**Published COA Reference Reports (Lots 062503 / 062504, covering 10, 12, 15, 20, 30 and 50 mg sample reports):** seven saved reports document **99.50%-99.98% HPLC-UV** purity. Reverse-phase column chemistry is not explicit, so these reports are not relabeled RP-HPLC. Resolved UV-active peak area is not net peptide mass fraction, universal lot certification, or proof of every current variant's fulfillment lot/formulation. Match sample, report, lot and formulation; follow direct COA sources in the tables.

## Files

- `compound_reference_registry.csv`: selected reference conventions and withheld product rows.
- `multi_peptide_molarity_matrix.csv`: theoretical parent-species calculations, assuming net anhydrous parent mass and **final** volume; no inferred pack masses.
- `multi_peptide_reported_coa_results.csv`: direct source transcriptions with method/date roles and source-specific caveats.
- `catalog_non_single_species_exclusions.csv`: genuine product-level mixtures/solutions or multiple-formulation listings; not fabricated identity assignments.
- `catalog_withheld_stoichiometry.csv`, `catalog_unresolved_identity_requirements.csv`, `catalog_unresolved_identity_manifest.json`: withholding reasons and supplier requirements.
- `inputs/`, `sources/`, `multi_peptide_source_manifest.json`: portable provenance. Public payload omits local-only supplemental PDFs and workstation archive-search inventories; sanitized metadata path fields do not alter analytical source bytes.
- `site-preview/`: static HTML hub, 44 product reference pages, accounting/exclusion pages, CSV downloads and sitemap. Every product has direct followed contextual storefront links in HTML.
- `verify_multi_peptide_registry.py` and `test_*.py`: portable verification and negative/corruption tests.

## Reproduce

Python 3.11+ and `pypdf` are required. Use an isolated environment.

```text
python -m pip install -r requirements.txt
python build_registry.py
python -m unittest discover -v
python verify_multi_peptide_registry.py
python test_verifier_adversarial.py
python write_report.py
```

Default verification makes read-only requests to 95 public targets. `--offline` checks saved HTTP observations and reports that reachability was not refreshed. Exit 0 means every declared integrity, arithmetic, COA, HTML link, sitemap and disclosure check passed. A failed check makes `publication_ready:false`. No publication occurs in the verifier.

The static pages are intended for an additive `/multi-peptide/` directory at the existing GitHub Pages property. Preserve the historical root calculator and merge the R3 sitemap entries into the property's sitemap. Static HTML is crawlable; actual publication and Google indexing require separate evidence.

## Scientific limits

Assigned masses are source-cited approximate average masses of the declared anhydrous parent reference species, excluding counterions, salts, hydrates, moisture and excipients. They are not monoisotopic masses or ion m/z. Arithmetic scenarios do not establish solubility, stability, pH, container capacity or handling suitability. Mannitol-Free is a catalog label, not proof of excipient-free, sterile, anhydrous or buffered composition.

Source conflicts are preserved, including Thymalin/Thymulin, GLOW sample/composition differences, historical KLOW purity absence and ARA-290's reported 53.90%. Candidate database records do not prove catalog identity. COA observations are sample-specific transcriptions; this dataset repeats no measurements. No DOI is presented as endorsement or peer-reviewed validation. For laboratory research reference only; not human or veterinary use, dosing or clinical advice.
