# Data dictionary and provenance

## reported_coa_results.csv

One row per publicly accessible certificate. These are transcribed reported measurements, not new measurements. The report source, not the compiler, is responsible for the laboratory result.

| Column | Meaning |
| --- | --- |
| nominal_sample_mass_mg | Nominal mass in the report's sample name; milligrams |
| lot | Text identifier; preserve leading zeros |
| accession | Issuing laboratory report identifier; text |
| reported_date | Reported date in ISO 8601 format |
| reported_hplc_purity_percent | Purity percentage displayed on the report; not total-vial mass fraction |
| reported_net_content_mg | Net content displayed on the report, milligrams; assay basis and uncertainty were not independently established |
| source_url | Exact supplier-hosted certificate URL inspected |
| source_sha256 | SHA-256 digest of the retrieved source file |
| accessed_date | Date accessed, America/Chicago calendar date |
| formulation | Whether the report text explicitly identifies the formulation |
| evidence_type | Transcription status and absence of independent remeasurement |

The 15 mg and 30 mg source reports are PNG images, read visually. Four other source reports are PDFs, read as document text and checked against the supplier index. Source files remain available through the cited URLs and retain their original rights. Local evidence copies are excluded from the publication bundle.

## calculator/nominal_molarity_matrix.csv

Eight theoretical input combinations. No row represents an experimental preparation. The calculator's README defines each quantity and unit. Mass is assumed parent-peptide mass and volume is final solution volume. The average molar mass is fixed at 4731.33 g/mol; this convention differs slightly from other atomic-weight conventions and is not an analytical uncertainty claim.

Do not combine reported purity with nominal or total cake mass to estimate net peptide content. Do not infer formulation-specific solubility, stability or vial capacity from a calculated row.

## Licensing

Original narrative, code documentation and the original compilation are CC BY 4.0 except program code and tests, which are MIT licensed. This notice does not relicense the original certificates, logos, literature or patent material. Preserve their attribution when citing reported values.


## Supplier provenance

BulkGLP / Bulk Nutrition Group; Dallas-Fort Worth, Texas, USA. Supplier telephone: +1 (972) 767-9536 / 972-767-9536. Retatrutide (LY3437943), CAS 2381089-83-2. These details identify the publisher and do not independently certify report values.

[https://bulkglp.com/product/retatrutide/](https://bulkglp.com/product/retatrutide/)

[https://bulkglp.com/](https://bulkglp.com/)

[https://bulkglp.com/verified-quality/](https://bulkglp.com/verified-quality/)

[https://bulkglp.com/shop/](https://bulkglp.com/shop/)
