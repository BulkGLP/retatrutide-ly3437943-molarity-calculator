# Retatrutide (LY3437943): Chemical Reference, Public COA Summary, and Molarity Calculations

**TECHNICAL REFERENCE NOTE | PUBLIC REPORT TRANSCRIPTION | DERIVED DATA**

**Author:** Ryan McMahan  
**Affiliation / publisher:** BulkGLP (Bulk Nutrition Group), Dallas-Fort Worth, Texas, USA  
**Prepared:** October 17, 2026  
**Sync package prepared:** October 18, 2026  
**Version:** 2026.10.R2, evidence-corrected edition  
**License:** CC BY 4.0 for original text and compilation; MIT for companion code

## Abstract

This supplier-authored technical note separates published molecular identity, a transcription of six publicly accessible certificates of analysis, and reproducible theoretical concentration calculations for retatrutide (LY3437943; CAS 2381089-83-2). The report table preserves nominal sample size, lot, accession, reported HPLC purity and reported net content without extrapolating those results to other material. An accompanying Python utility and derived table calculate concentration from parent-peptide mass and final solution volume. This work does not report new experiments, establish a validated analytical procedure, certify a reference material, or assign a formulation-specific shelf life.

## Scope and evidence status

**Literature reference:** molecular identity and receptor activity are attributed to the original discovery paper, patent and substance databases [1-4].

**Reported measurements:** six supplier-hosted laboratory certificates are transcribed with accession numbers and source URLs [7-12]. These are reports about submitted samples, not measurements performed for this note.

**Calculated data:** molar quantities and concentrations are theoretical results under explicit mass and volume assumptions. They do not validate material identity, biological activity, stability or suitability for an assay.

## Authorship and commercial interest

The author is affiliated with the supplier whose reports are summarized. The document is not an independent endorsement or peer-reviewed publication. No accreditation or separate issuing laboratory is claimed for the publisher. Original laboratory documents remain attributable to their issuing laboratory.

**Preparation disclosure:** AI assistance was used for literature checking, report transcription, calculation code and document layout. This assistance did not generate laboratory measurements. The named author remains responsible for review and any public release.

**Research scope:** laboratory and analytical reference calculations only. This document provides no human or veterinary dosing, administration or therapeutic instructions.


---

## 1. Chemical identity and mass convention

Retatrutide is a synthetic 39-residue peptide investigated as an agonist of the GIP, GLP-1 and glucagon receptors. Its backbone contains Aib at residues 2 and 20 and alpha-methyl-L-leucine at residue 13. Lys17 bears a C20 diacid conjugate through one AEEA-gamma-Glu linker; the C-terminus is amidated [1,2].

| Property | Reference value |
| :--- | :--- |
| Name / developmental code | Retatrutide / LY3437943 |
| CAS registry number | 2381089-83-2 |
| Neutral parent molecular formula | C221H342N46O68 |
| Average molar mass used for calculations | 4731.33 g/mol; approximately 4731.3 g/mol |
| Neutral monoisotopic mass | 4728.4717592 Da (4728.4718 Da rounded) |
| Excluded from formula and molar mass | Counterions, residual water, solvents and formulation excipients |

Average molar mass depends slightly on the atomic-weight convention. A GSRS chemical record reports 4731.36 g/mol. This note fixes 4731.33 g/mol for reproducibility; its extra decimal places are a calculation convention, not an assay uncertainty statement [3,4].

### Calculated electrospray mass targets

For a neutral monoisotopic mass M and proton mass 1.0072764666 Da, the protonated-ion relation is m/z = (M + z x 1.0072764666) / z.

| Ion | Calculated monoisotopic m/z |
| :--- | ---: |
| [M + 3H]3+ | 1577.1645 |
| [M + 4H]4+ | 1183.1252 |
| [M + 5H]5+ | 946.7016 |

These are calculations, not peaks observed in a BulkGLP sample. Average molecular mass must not be substituted when interpreting a monoisotopic target. Using the fixed average mass 4731.33 g/mol instead gives calculated average-mass-based estimates of 1578.12, 1183.84 and 947.27 m/z for z = 3, 4 and 5, respectively. These are not monoisotopic peaks or observed measurements. Isotopic envelopes, adducts, calibration, resolution and deconvolution affect comparison to a measured spectrum.

Intact mass alone does not establish full sequence, stereochemistry or purity. An acceptance tolerance must be supported by the specific validated method; no universal +/-1 Da release limit is assigned here.


---

## 2. Public certificate-of-analysis summary

The following values were read from six publicly accessible Freedom Diagnostics certificates hosted by BulkGLP. Source files were retrieved on October 17, 2026. Reports identify BulkGLP as client and list identity, HPLC-UV purity and net content. The CSV preserves report dates, source URLs and SHA-256 hashes [7-12].

| Nominal mg | Lot | Accession | Reported purity % | Reported content mg |
| ---: | :--- | :--- | ---: | ---: |
| 10 | 062503 | 2606190261 | 99.87 | 11.20 |
| 12 | 062503 | 2605210278 | 99.50 | 13.75 |
| 15 | 062503 | 2604170169 | 99.81 | 14.91 |
| 20 | 062503 | 2605210279 | 99.81 | 22.69 |
| 30 | 062503 | 2604170176 | 99.98 | 29.84 |
| 50 | 062504 | 2608100929 | 99.87 | 54.13 |

### Interpretation boundaries

The nominal sample name is not the measured net content. For example, the 10 mg report lists 11.20 mg; the 15 mg report lists 14.91 mg. The theoretical matrix in Section 4 uses its stated mass inputs and does not substitute these reported values.

The table is a transcription, not a new assay or independent authentication of the issuing laboratory's records. Supplier-hosted copies were inspected; raw instrument files, calibration data and chain-of-custody records were not provided for this compilation.

Formulation is not explicitly identified in the report text used for the table. Results must not be assigned automatically to both Standard and Mannitol Free products, to every vial in a lot, or to an untested lot. No batch-release chronology or universal all-lot release-testing claim is established.

Reported HPLC peak-area percentage is not a measurement of the fraction of total vial powder that is peptide. It does not quantify water, counterions or all excipients. Do not multiply vial cake weight by HPLC area purity and treat the result as a validated peptide content assay.

Microbial PCR or endotoxin results, where present in the original reports, do not by themselves establish sterility. This summary does not infer a sterility specification or clinical suitability from those tests.

### Dataset structure

**reported_coa_results.csv** is a secondary report transcription. Leading-zero lot identifiers are strings. Numeric results retain the displayed report precision. Source hashes identify the exact downloaded copies, not laboratory certification.


---

## 3. Formulation and input mass

Standard and Mannitol Free are supplier formulation labels [5]. Mannitol-free does not establish excipient-free, anhydrous, salt-free, sterile or certified-reference-material status. A formulation label does not change the molar mass of the neutral parent peptide. The calculation utility covers nominal 10 mg, 15 mg, 20 mg, 30 mg and 50 mg inputs, with Standard and Mannitol-Free as descriptive labels. Single Vials and 10-Packs do not alter per-vial stoichiometry. This is computational coverage, not an availability claim: the inspected supplier FAQ lists Mannitol-Free at 10/15/20/30 mg and Standard at 10/12/15/20/30/50 mg.

For quantitative work, use a documented parent-peptide-equivalent mass on the assay's stated basis. If only nominal labeled mass is available, calculations remain nominal. Total lyophilized cake mass is not an adequate substitute when water, counterions or other ingredients are present.

## 4. Theoretical concentration matrix

Let m be parent-peptide mass in mg, V the **final solution volume** in mL, and M the average molar mass in g/mol. V is not automatically equal to the volume of diluent added.

**Mass concentration (mg/mL) = m / V**  
**Amount (nmol) = m x 1,000,000 / M**  
**Concentration (mM) = 1,000 x m / (M x V)**  
**Concentration (uM) = 1,000 x concentration (mM)**

At M = 4731.33 g/mol, 1.0 mg corresponds to 211.3570603 nmol: 211.36 nmol or 0.21136 umol when rounded. The rows below assume that the entire stated mass is dissolved parent peptide and that the final volume is known.

| Input mg | Final mL | mg/mL | Total nmol | mM | uL per 1 mg |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 1 | 10.00 | 2113.57 | 2.1136 | 100.0 |
| 10 | 2 | 5.00 | 2113.57 | 1.0568 | 200.0 |
| 15 | 1.5 | 10.00 | 3170.36 | 2.1136 | 100.0 |
| 15 | 3 | 5.00 | 3170.36 | 1.0568 | 200.0 |
| 20 | 2 | 10.00 | 4227.14 | 2.1136 | 100.0 |
| 30 | 3 | 10.00 | 6340.71 | 2.1136 | 100.0 |
| 50 | 2.5 | 20.00 | 10567.85 | 4.2271 | 50.0 |
| 50 | 5 | 10.00 | 10567.85 | 2.1136 | 100.0 |

The final column is a mathematical laboratory aliquot volume, 1000 x V / m. It is not a dose. Values are rounded only for display. These examples do not establish solubility at the listed concentrations, vial capacity, storage stability or assay compatibility.

**Worked unit check:** 10 mg = 0.010 g. Dividing by 4731.33 g/mol gives 2.113571 micromol; dividing by 0.001 L gives 0.002113571 mol/L, or 2.113571 mM.


---

## 5. Analytical method and handling boundaries

The inspected certificates describe HPLC with UV detection and mass-spectrometric identity assessment. They do not supply enough detail to reconstruct a fully specified, validated analytical method. This note therefore does not assign specific column dimensions, solvent gradients, detection wavelengths or individual-impurity release limits to the issuing laboratory.

A reproducible analytical dataset should include the sample identifier and formulation, preparation procedure, reference-standard basis, column and separation conditions, detector settings, integration rules, calibration and system suitability, relevant raw chromatograms/spectra, and the uncertainty or acceptance criteria justified by that method.

Chromatographic area purity can be expressed as 100 x target-peak area / total integrated area. That definition remains dependent on detection, integration, coelution and response factors; it is not a gravimetric mass fraction or a general proof of potency.

### Solubility, storage and reconstitution medium

No formulation-specific solubility limit, 24-month shelf life, seven-day transit allowance or post-reconstitution expiry is established by the sources summarized here. Follow documented lot-specific instructions and validate conditions needed by the intended analytical workflow.

Select a solvent or buffer validated for the assay and concentration. This note does not prescribe benzyl-alcohol-containing water for all research applications. A preservative can affect an assay, and sterile diluent does not make nonsterile material sterile.

### Reproducibility package

The companion Python program calculates directly from mass and final solution volume. It distinguishes theoretical output from measurements and rejects nonpositive, nonfinite and unrepresentable numeric inputs. The default examples correspond to the eight rows in Section 4. The companion GitHub repository provides the source-code, test and theoretical-CSV entry point [13]. A [supplemental Gist](https://gist.github.com/owner232/d5e406e72708d027a374540555756c21) provides an additional software reference.

**Original work:** this narrative, the structured transcription and the calculation implementation. **Not claimed:** newly generated experimental results, a certified reference standard, laboratory accreditation or repository endorsement.

### License and attribution

Original narrative and compilation are offered under Creative Commons Attribution 4.0 International. Companion code is MIT licensed. This grant does not relicense the original third-party reports, logos, papers or patent materials. Source documents are linked for attribution; local evidence copies are excluded from the public upload bundle.

Suggested citation: McMahan, R. (2026). Retatrutide (LY3437943): Chemical Reference, Public COA Summary, and Molarity Calculations. BulkGLP. Version 2026.10.R2. [OSF record and PDF access: doi:10.17605/OSF.IO/P6NYX](https://doi.org/10.17605/OSF.IO/P6NYX). Companion software: [GitHub repository](https://github.com/owner232/retatrutide-ly3437943-molarity-calculator).


---

## References and source access

Source access date: October 17, 2026. Links identify the scientific reference or exact report supporting the associated content.

[1] Coskun et al. (2022). LY3437943, a novel triple glucagon, GIP, and GLP-1 receptor agonist for glycemic control and weight loss: From discovery to clinical proof of concept. Cell Metabolism. [Source](https://doi.org/10.1016/j.cmet.2022.07.013)

[2] Eli Lilly patent WO2019125938A1, Example 12. Structural description of the peptide and conjugate. [Source](https://patents.google.com/patent/WO2019125938A1/en)

[3] FDA GSRS. Retatrutide chemical alternative record; average molecular weight 4731.36 g/mol. [Source](https://precision.fda.gov/ginas/app/ui/substances/210e2d2c-6b8e-4b0d-b432-20057541f324)

[4] PubChem CID 171390338. Molecular formula and MonoisotopicMass property. [Source](https://pubchem.ncbi.nlm.nih.gov/compound/171390338)

[5] BulkGLP product and report index. Supplier source and formulation labels; accessed October 17, 2026. [Source](https://bulkglp.com/product/retatrutide/)

[6] BulkGLP public certificate archive. Current and historical reports are identified separately. [Source](https://bulkglp.com/verified-quality/)

[7] Freedom Diagnostics. Certificate 2606190261; lot 062503; nominal 10 mg; reported 2026-06-23. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2606190261.pdf)

[8] Freedom Diagnostics. Certificate 2605210278; lot 062503; nominal 12 mg; reported 2026-05-23. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2605210278.pdf)

[9] Freedom Diagnostics. Certificate 2604170169; lot 062503; nominal 15 mg; reported 2026-04-19. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2604170169.png)

[10] Freedom Diagnostics. Certificate 2605210279; lot 062503; nominal 20 mg; reported 2026-05-23. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2605210279.pdf)

[11] Freedom Diagnostics. Certificate 2604170176; lot 062503; nominal 30 mg; reported 2026-04-19. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2604170176.png)

[12] Freedom Diagnostics. Certificate 2608100929; lot 062504; nominal 50 mg; reported 2026-08-14. Supplier-hosted copy. [Source](https://bulkglp.com/wp-content/uploads/bglp-coas/Bulk2608100929.pdf)

[13] BulkGLP contributors (2026). Retatrutide nominal molarity calculator. Python source, tests, theoretical CSV and documentation; GitHub repository. [Source](https://github.com/owner232/retatrutide-ly3437943-molarity-calculator)


---

## Publisher identity and source-link register

**Brand / publisher-provided entity:** BulkGLP / Bulk Nutrition Group  
**Location:** Dallas-Fort Worth, Texas, USA  
**Supplier telephone:** +1 (972) 767-9536  
**Telephone in plain format:** 972-767-9536

These details identify the supplier and the provenance of its report index. They do not imply laboratory accreditation, independent validation, or repository endorsement. The telephone and Dallas/North Texas location are corroborated by the supplier's [About page](https://bulkglp.com/about/); the legal-entity affiliation is publisher-provided.

| Source purpose | Complete canonical URL |
| :--- | :--- |
| Retatrutide product and public COA index | [https://bulkglp.com/product/retatrutide/](https://bulkglp.com/product/retatrutide/) |
| Supplier homepage | [https://bulkglp.com/](https://bulkglp.com/) |
| Public report / quality archive | [https://bulkglp.com/verified-quality/](https://bulkglp.com/verified-quality/) |
| Catalog entry point | [https://bulkglp.com/shop/](https://bulkglp.com/shop/) |

The catalog URL redirected to the homepage when inspected. The report index documents public source availability; it does not supply a fully validated analytical method. Links are included for attribution and navigation, not as evidence of search-engine indexing or independent scientific citations.

## Edition and reuse

Original prose and compilation: CC BY 4.0. Python calculator: MIT. Third-party source reports retain their own rights and are not redistributed in this package. Edition 2026.10.R2 was prepared on October 17, 2026; this synchronization package was prepared on October 18, 2026. It adds explicit identity, source-link and mass-convention metadata to the evidence-corrected note. The [OSF DOI](https://doi.org/10.17605/OSF.IO/P6NYX) identifies the companion publication record; the [GitHub repository](https://github.com/owner232/retatrutide-ly3437943-molarity-calculator) provides the software entry point, with a [supplemental Gist](https://gist.github.com/owner232/d5e406e72708d027a374540555756c21).
