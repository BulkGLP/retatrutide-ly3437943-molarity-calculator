"""Generate the R3 reference report using only files inside this release."""
import argparse
import csv
import json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    root=parser.parse_args().root
    inv=json.loads((root/'catalog-coa-inventory.json').read_text(encoding='utf-8'))
    result=json.loads((root/'verification-results.json').read_text(encoding='utf-8'))
    def cell(value):return str(value).replace('|','\\|').replace('\n',' ')
    lines=['# BulkGLP multi-peptide registry - Edition 2026.10.R3','',
        '**44 catalog products accounted for. Publication readiness and mathematical completeness are separate.**','',
        f"Saved verifier: exit {result['exit_code']}; {result['checks']} checks; publication_ready={str(result.get('publication_ready',False)).lower()}; full_catalog_molarity_complete={str(result['full_catalog_molarity_complete']).lower()}; http_fresh={str(result['http_fresh']).lower()}.",
        '', 'Publication readiness means all accounting, integrity, arithmetic, COA, link and disclosure checks passed. It is not proof of independent laboratory authentication, chemical identification of every product, deployment or Google indexing.', '',
        '## Explicit withholding and reference conventions','',
        '- FOXO4, Adamax and AHK-Cu: `stoichiometry_withheld_pending_sequence_specification`.',
        '- Thymalin: `stoichiometry_withheld_catalog_coa_nomenclature_conflict`. The catalog says Thymalin; COA2608100933 says Thymulin. Free nonathymulin is a defined candidate, not proof of the catalog preparation. No product CAS/formula/molar mass or matrix rows are assigned.',
        '- GHK-Cu vial and powder models use the declared neutral 1:1 C14H22CuN6O4 / CAS89030-95-5 reference, 401.91 g/mol. The convention does not certify actual lot stoichiometry, counterions, hydration or net complex content.',
        '- TB-500 uses the full-length thymosin beta-4/timbetasin parent named by COA2605280346, 4963 g/mol. It is not the Ac-LKKTETQ fragment; the commercial name alone does not establish every lot or variant.',
        '- R3 Retatrutide uses the cited PubChem rounded convention 4731 g/mol. Existing historical calculator assets retain 4731.33 g/mol; their filenames and URLs are preserved by additive deployment.', '',
        '## Complete catalog','', '| Product | Disposition | Reference g/mol | Matrix rows |', '|---|---|---|---|']
    by_slug={p['slug']:p for p in inv['products']}
    with (root/'catalog_molarity_accounting.csv').open(encoding='utf-8',newline='') as stream:
        ledger=list(csv.DictReader(stream))
    for row in ledger:
        p=by_slug[row['product_slug']];mass=p['chemical_reference'].get('molar_mass_g_mol')
        lines.append('| '+ ' | '.join([f"[{cell(p['name'])}]({p['canonical_url']})",cell(row['accounting_status']),str(mass) if mass is not None else 'Withheld / not applicable',row['matrix_rows']])+' |')
    lines.extend(['', '## Published COA Reference Reports - Lots 062503 / 062504','',
        'Seven published supplier-hosted Retatrutide sample reports cover 10, 12, 15, 20, 30 and 50 mg nominal samples and report 99.50%-99.98% HPLC-UV purity. These reports do not establish every variant current fulfillment lot, formulation or net peptide content. HPLC-UV purity describes resolved UV-active peak area; reverse-phase column chemistry is not explicitly stated.', '',
        '| Report | Lot | Nominal sample | Reported HPLC-UV purity |', '|---|---|---|---|'])
    for r in inv['coa_records']:
        if r['product_slug']=='retatrutide' and r.get('lot') in ('062503','062504'):
            lines.append(f"| [{r['report_id']}]({r['source_url']}) | {r['lot']} | {cell(r['nominal_label'])} | {r['reported_hplc_purity_percent']:.2f}% |")
    lines.extend(['', '## Provenance and scientific disclosures','',
        'The 49 public source-file entries contain 47 distinct printed report identifiers. Multiple archive formats of one report are not independent laboratory tests. Local-only supplemental reports are excluded from the public portable payload. Candidate references remain provenance, not selected catalog species.', '',
        'Sources are hash-locked in `multi_peptide_source_manifest.json`. Public payload metadata path redactions are disclosed separately; analytical source document bytes remain unchanged. `--offline` verifies cached HTTP observations and explicitly does not refresh reachability. This generator has no workspace or operations-account dependencies.', ''])
    lines.extend('- '+text for text in inv['disclosures'].values())
    lines.extend(['', '## Reproduce','', '```text', 'python -m pip install -r requirements.txt', 'python build_registry.py', 'python -m unittest discover -v', 'python verify_multi_peptide_registry.py --offline', 'python test_verifier_adversarial.py', 'python write_report.py', '```','',
        'Online verification omits `--offline` and makes read-only requests to the public product/COA targets. No DOI is presented as independent endorsement or peer review. Publication and deployed HTTP/indexability are verified separately.', ''])
    (root/'GEMINI-MULTI-PEPTIDE-INVENTORY.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'report':'GEMINI-MULTI-PEPTIDE-INVENTORY.md','products':len(by_slug),'saved_verifier_exit':result['exit_code']}))

if __name__=='__main__':main()
