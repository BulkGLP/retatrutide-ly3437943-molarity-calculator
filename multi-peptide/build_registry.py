"""Build local evidence-backed registry artifacts. Never publishes anything."""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path
from registry_math import calculate, STANDARD_FINAL_VOLUMES_ML
from catalog_accounting import derive as derive_accounting

BASE = Path(__file__).resolve().parent
EDITION = '2026.10.R3'
PUBLIC_SITE_URL = 'https://bulkglp.github.io/retatrutide-ly3437943-molarity-calculator/multi-peptide/'
DISCLOSURES = {
    'affiliation': 'Commercial affiliation: compiled for BulkGLP, the supplier whose catalog and hosted reports are referenced. Compilation was AI-assisted and source-reviewed.',
    'scope': 'For laboratory research reference only; not for human or veterinary use. No dosing, clinical advice, safety assessment, or independent wet-lab validation is provided.',
    'mass': 'Every assigned molar mass is a declared approximate average molar mass convention for the anhydrous parent species described by its cited reference. It is not a lot-specific measured molecular mass. Salts, counterions, hydrates, residual moisture and excipients are excluded from the parent-mass model.',
    'arithmetic': 'Theoretical molarity assumes the nominal mass equals net parent-peptide mass and uses final solution volume, not solvent volume added. mg/mL = mass (mg) / final volume (mL); mM = mg/mL × 1000 / molar mass (g/mol); uM = mM × 1000. Decimal places are computational precision, not measurement accuracy.',
    'limitations': 'The 1.0, 1.5, 2.0 and 2.5 mL scenarios are arithmetic only. They do not establish solubility, stability, pH, handling suitability, or container capacity, particularly for bulk powders. No single molar mass is assigned to mixtures or unresolved identities.',
    'coa': 'COA values are transcriptions of supplier-hosted documents for the submitted samples, not new measurements or certification of every sold lot. Chromatographic area purity is not net peptide content, sterility, or proof of absence of excipients. Original method labels are preserved; HPLC-UV is not silently relabeled RP-HPLC. Received, reported and test dates have separate fields.',
    'formulation': 'Mannitol-Free is a catalog label; it does not establish excipient-free, salt-free, anhydrous, sterile or buffered composition. COA formulation is unassigned unless explicitly identified by the source.',
    'availability': 'Catalog membership includes published options that were out of stock at capture. COA nominal sample sizes are distinct from current catalog sizes. Missing values are explicitly unestablished, not zero.',
}

def read_json(name):
    return json.loads((BASE/name).read_text(encoding='utf-8-sig'))

def dump(name, value):
    path = BASE/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def csv_write(name, fields, rows):
    with (BASE/name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def as_records(data):
    return data if isinstance(data, list) else data['records']

def e(value):
    return html.escape(str(value if value is not None else 'Not established'), quote=True)

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+e(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def page(title, body, prefix=''):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow"><title>'+e(title)+' | BulkGLP reference registry</title><meta name="description" content="Source-documented chemical references, theoretical stoichiometry and supplier COA transcriptions. Edition 2026.10.R3."><link rel="stylesheet" href="'+prefix+'style.css"></head><body><header><a href="'+prefix+'index.html">BULKGLP / OPEN REFERENCE</a><span>Edition '+EDITION+' · Evidence and reference conventions</span></header><main>'+body+'</main><footer>Catalog evidence captured October 22, 2026; accounting reviewed October 25, 2026. Integrity verification is not independent laboratory validation.</footer></body></html>'

def make_site(products, matrix, coas, exclusions, unresolved, accounting):
    site = BASE/'site-preview'
    site.mkdir(exist_ok=True)
    review=read_json('inputs/catalog-resolution-review.json')
    reviewed_identities={r['product_slug']:r for r in review['unresolved_identity_products']}
    (site/'style.css').write_text('''*{box-sizing:border-box}body{margin:0;background:#f7f8fa;color:#172433;font:16px/1.6 system-ui,sans-serif}header,main,footer{max-width:1160px;margin:auto;padding:28px}header{display:flex;justify-content:space-between;border-bottom:1px solid #d5dde5;gap:20px;font-size:13px;letter-spacing:.04em}header a{font-weight:750}h1{font-size:36px;line-height:1.15;margin:20px 0}h2{font-size:23px;margin-top:38px}a{color:#174e75;text-underline-offset:3px}p{max-width:920px}.lead{font-size:19px;color:#415567}.note{padding:14px 18px;border-left:3px solid #7395ad;background:#edf2f6}.table-wrap{overflow:auto;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:14px;background:white}th,td{padding:11px 13px;border-bottom:1px solid #dce3e9;text-align:left;vertical-align:top}th{background:#e8eef3;font-size:12px;text-transform:uppercase;letter-spacing:.04em}td.num{font-variant-numeric:tabular-nums}footer{font-size:13px;color:#516474;border-top:1px solid #d5dde5}.meta{color:#516474;font-size:14px}ul{padding-left:22px}.downloads{display:flex;gap:20px;flex-wrap:wrap}@media(max-width:650px){header{display:block}header span{display:block;margin-top:10px}header,main,footer{padding:20px}h1{font-size:28px}th,td{padding:9px}}''', encoding='utf-8')
    indexrows=[]
    for p in products:
        slug=p['slug']; chem=p['chemical_reference']; rows=[r for r in matrix if r['product_slug']==slug]; reports=[r for r in coas if r['product_slug']==slug]
        molar=chem.get('molar_mass_g_mol')
        category=p['category']+(' (provisional)' if p.get('category_is_provisional') else '')
        mass_display=f'{molar:g}' if molar is not None else None
        hub_name=p['name']+(' [stoichiometry withheld: Thymalin / Thymulin conflict]' if slug=='thymalin-10mg' else '')
        indexrows.append([f'<a href="compounds/{e(slug)}/index.html">{e(hub_name)}</a>',f'<a href="{e(p["canonical_url"])}">{e(p["name"])} product specifications</a>',e(category),e(mass_display),str(len(reports))])
        body=f'<p class="meta">{e(category)}</p><h1>{e(p["name"])}</h1><p class="lead">Chemical reference, nominal concentration arithmetic and documented COA results.</p>'
        body+=f'<p><a href="{e(p["canonical_url"])}">Canonical product specifications</a> · <a href="https://bulkglp.com/verified-quality/">Public COA archive</a></p>'
        sizes=', '.join(f'{s["value"]} {s["unit"]}' for s in p['nominal_sizes']) or 'Not established in captured catalog'
        body+=table(['Nominal size per container','Formulations','CAS','Formula','Average molar mass (g/mol)'],[[e(sizes),e('; '.join(p['formulations']) or 'Unspecified'),e(chem.get('cas')),e(chem.get('formula')),e(mass_display)]])
        for note in p.get('identity_notes',[]):body+='<p>'+e(note)+'</p>'
        body+=f'<p class="note">{e(chem.get("allowed_molarity_reason") or chem.get("notes") or "No established single-species chemical reference is assigned.")}</p>'
        for note in chem.get('notes',[]):
            body+='<p>'+e(note)+'</p>'
        if chem.get('constituent_references'):
            body+=table(['Form-specific constituent','Formula','Reference g/mol'],[[e(r['name']),e(r.get('formula')),e(r.get('molar_mass_g_mol'))] for r in chem['constituent_references']])
        if molar is not None:
            body+=f'<p>{e(chem.get("convention") or DISCLOSURES["mass"])}</p>'
        if chem.get('source_urls'):
            body+='<p>Identity and mass sources: '+ ' · '.join(f'<a href="{e(u)}">Reference {i+1}</a>' for i,u in enumerate(chem['source_urls']))+'</p>'
        if slug in reviewed_identities:
            reviewed=reviewed_identities[slug]
            body+='<h2>Unselected reference candidates</h2><p>These are database structures, not assigned product identities or computed product molarities. CAS-like synonyms are database metadata, not independent CAS Registry validation.</p>'
            if reviewed['candidate_references']:
                body+=table(['Candidate reference','CAS-like synonyms','Formula','Source-rounded average g/mol'],[[f'<a href="https://pubchem.ncbi.nlm.nih.gov/compound/{r["pubchem_cid"]}">{e(r["name"])} (CID {r["pubchem_cid"]})</a>',e('; '.join(r['cas_like_synonyms']) or 'Not established'),e(r['formula']),e(r['average_molar_mass_g_mol'])] for r in reviewed['candidate_references']])
            else:
                body+='<p>No unique candidate selected. The exact PubChem Adamax compound-name query returned no CID; this is not proof that no structure or registry entry exists elsewhere.</p>'
            body+='<p>Supplier data needed: '+e(reviewed['supplier_data_needed'])+'</p>'
        body+='<h2>Theoretical stoichiometry</h2>'
        if rows:
            body+=table(['Nominal mass (mg)','Final volume (mL)','mg/mL','mM','uM'],[[e(r[x]) for x in ['nominal_mass_mg','final_volume_ml','mass_concentration_mg_ml','molarity_mM','molarity_uM']] for r in rows])
        else:
            body+='<p>No molarity rows: '+e(chem.get('allowed_molarity_reason') or 'mixture, support solution, accessory, or unresolved chemical identity')+'.</p>'
            if p['category']=='Multi-Peptide Blend' and any(s['unit']=='mg' for s in p['nominal_sizes']):
                from decimal import Decimal
                massrows=[[e(s['value']),e(v),e(f'{Decimal(str(s["value"]))/Decimal(v):.4f}')] for s in p['nominal_sizes'] if s['unit']=='mg' for v in STANDARD_FINAL_VOLUMES_ML]
                body+='<p>Total nominal mass concentration only; no constituent molarity is inferred.</p>'+table(['Total nominal mass (mg)','Final volume (mL)','Total mg/mL'],massrows)
        body+='<h2>COA transcriptions</h2>'
        if reports:
            body+='<p>'+str(len(reports))+' archive file entries; '+str(len({r['report_id'] for r in reports}))+' distinct printed report identifiers. File variants do not constitute independent tests.</p>'
            body+=table(['Report / source','Lot','Nominal sample','Reported HPLC purity (%)','Report date','Method'],[[f'<a href="{e(r["source_url"])}">{e(r["report_id"])}</a>',e(r.get('lot')),e(str(r.get('nominal_mass_mg'))+' mg' if r.get('nominal_mass_mg') is not None else str(r.get('nominal_volume_ml'))+' mL' if r.get('nominal_volume_ml') is not None else r.get('nominal_label')),e(r.get('reported_hplc_purity_percent')),e(r.get('reported_date')),e(r.get('purity_method'))] for r in reports])
            unique_notes=list(dict.fromkeys(note for r in reports for note in r.get('notes',[]) if not note.startswith('Direct method is preserved')))
            if unique_notes:body+='<h3>Source qualifications</h3>'+''.join('<p>'+e(note)+'</p>' for note in unique_notes)
        else:
            body+='<p>No COA is linked to this exact product in the captured public archive. A report for another product or container size is not automatically assigned here.</p>'
        body+='<h2>Scientific disclosures</h2>'+''.join('<p>'+e(t)+'</p>' for t in DISCLOSURES.values())
        target=site/'compounds'/slug/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page(p['name'],body,'../../'),encoding='utf-8')
    body='<p class="meta">RESEARCH DATA / EDITION '+EDITION+'</p><h1>Multi-peptide reference registry</h1><p class="lead">44 catalog products. Separate evidence for chemical identity, nominal concentration and reported laboratory results.</p><p class="note">A missing molar mass means the available sources do not support assigning one to that product. Explicitly withheld stoichiometry is a valid accounting disposition, not a computed molarity.</p>'
    body+='<p>49 published archive file entries represent 47 distinct printed report identifiers. Counts below describe file entries attached to each exact product.</p>'
    body+=table(['Reference page','Storefront product','Category','g/mol','COA file entries'],indexrows)
    body+='<p><a href="catalog-exclusions.html">Explicit product-level non-single-species exclusions</a> · <a href="unresolved-identities.html">Unresolved identity register and required supplier data</a></p>'
    body+='<p class="note">All 44 catalog products are accounted for. Full catalog molarity remains incomplete: stoichiometry is withheld for FOXO4, Adamax and AHK-Cu pending sequence/specification; Thymalin is withheld because the catalog says Thymalin while COA2608100933 names Thymulin. Free nonathymulin is a distinct defined reference and is not assigned to the catalog preparation. No Thymalin mass or molarity rows are published. Exclusions and nonpeptide reference records are not computed peptide molarities.</p>'
    body+='<p>R3 uses the cited PubChem source-rounded Retatrutide convention of 4731 g/mol. The <a href="https://bulkglp.github.io/retatrutide-ly3437943-molarity-calculator/">historical Retatrutide calculator</a> retains its 4731.33 g/mol convention and existing URLs and filenames; these conventions are disclosed separately, not silently overwritten.</p>'
    body+='<p><a href="catalog-dispositions.html">All 44 accounting dispositions</a> · <a href="data/multi_peptide_molarity_matrix.csv">Download theoretical matrix CSV</a> · <a href="data/multi_peptide_reported_coa_results.csv">Download reported COA CSV</a></p>'
    body+='<h2>Scientific disclosures</h2>'+''.join('<p>'+e(t)+'</p>' for t in DISCLOSURES.values())
    (site/'index.html').write_text(page('Compound hub',body),encoding='utf-8')
    body='<h1>Catalog non-single-species exclusions</h1><p>These product-level exclusions have no computed molarity. Mixtures have no single molecular formula or molar mass. A listing with multiple selectable chemical forms requires form-specific specifications; it is not automatically evidence that the forms are physically mixed.</p>'
    body+=table(['Catalog product','Exclusion type','Scientific reason','Reference page'],[[f'<a href="{e(r["canonical_url"])}">{e(r["product_name"])}</a>',e(r['exclusion_kind']),e(r['scientific_reason']),f'<a href="{e(r["reference_page"])}">Product reference</a>'] for r in exclusions])
    body+='<p>Uncertain identities are tracked separately in the <a href="unresolved-identities.html">unresolved identity register</a>. An identity gap is not evidence of a mixture.</p>'
    body+='<h2>Scientific disclosures</h2>'+''.join('<p>'+e(t)+'</p>' for t in DISCLOSURES.values())
    (site/'catalog-exclusions.html').write_text(page('Catalog exclusions',body),encoding='utf-8')
    body='<h1>Withheld catalog stoichiometry</h1><p>No candidate CAS, formula, molar mass or matrix rows are assigned to these four products. FOXO4, Adamax and AHK-Cu await sequence/specification; Thymalin is withheld for the catalog Thymalin versus COA Thymulin/nonathymulin nomenclature conflict. These are explicit withholding dispositions, not scientific mixtures or computed molarities. Full catalog molarity remains incomplete.</p>'
    body+=table(['Catalog product','Original flag','Supplier data needed','Reference page'],[[f'<a href="{e(r["canonical_url"])}">{e(r["product_name"])}</a>',e(r['original_flag_reason']),e(r['supplier_data_needed']),f'<a href="{e(r["reference_page"])}">Product reference</a>'] for r in unresolved])
    body+='<h2>Scientific disclosures</h2>'+''.join('<p>'+e(t)+'</p>' for t in DISCLOSURES.values())
    (site/'unresolved-identities.html').write_text(page('Unresolved identities',body),encoding='utf-8')
    ledger,_,_,_=derive_accounting(products,matrix)
    body='<h1>Complete catalog dispositions</h1><p>Every catalog product is accounted for exactly once. Publication readiness is separate from mathematical completeness. Withheld identities have no assigned mass or calculated molarity.</p>'
    body+=table(['Product specifications','Accounting disposition','Scientific reason'],[[f'<a href="{e(r["canonical_url"])}">{e(r["product_name"])}</a>',e(r['accounting_status']),e(r['reason'])] for r in ledger])
    body+='<h2>Scientific disclosures</h2>'+''.join('<p>'+e(t)+'</p>' for t in DISCLOSURES.values())
    (site/'catalog-dispositions.html').write_text(page('Catalog dispositions',body),encoding='utf-8')
    paths=['index.html','catalog-exclusions.html','unresolved-identities.html','catalog-dispositions.html']+['compounds/'+p['slug']+'/index.html' for p in products]
    (site/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+PUBLIC_SITE_URL+path+'</loc></url>' for path in paths)+'</urlset>\n',encoding='utf-8')
    (site/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+PUBLIC_SITE_URL+'sitemap.xml\n',encoding='utf-8')
    downloads=site/'data';downloads.mkdir(exist_ok=True)
    import shutil
    for name in ('compound_reference_registry.csv','multi_peptide_molarity_matrix.csv','multi_peptide_reported_coa_results.csv','catalog_molarity_accounting.csv','catalog_non_single_species_exclusions.csv','catalog_withheld_stoichiometry.csv'):
        shutil.copyfile(BASE/name,downloads/name)
    (site/'.nojekyll').write_text('',encoding='utf-8')

def main():
    cat=read_json('inputs/catalog-products.json')
    chem=read_json('inputs/chemical-references.json')
    coas=as_records(read_json('inputs/coa-records.json'))
    grouped={}
    for r in chem['references']:
        for slug in r['slugs']:grouped.setdefault(slug,[]).append(r)
    refs={slug:items[0] if len(items)==1 else dict(id=slug,name='Multiple chemical forms',slugs=[slug],cas=None,formula=None,molar_mass_g_mol=None,identity_status='formulation_specific_references_only',is_peptide=False,allowed_molarity=False,allowed_molarity_reason='Multiple chemical forms and supplied solution: no single product molar mass or molarity assigned.',notes=['Form-specific molecular masses are constituent references only; they are not a molecular mass for the solution.'],constituent_references=items,source_urls=list(dict.fromkeys(u for r in items for u in r.get('source_urls',[]))),source_files=list(dict.fromkeys(f for r in items for f in r.get('source_files',[])))) for slug,items in grouped.items()}
    products=[]; registry=[]; matrix=[]
    for original in cat['products']:
        p=dict(original)
        if p['category'] in ('Lipotropic','Support Compound'):p['category']='Lipotropic / Support Compound'
        if p['category'] in ('Bacteriostatic','Accessory'):p['category']='Bacteriostatic / Accessory'
        reference=refs.get(p['slug'], dict(id=p['slug'],name=p['name'],slugs=[p['slug']],cas=None,formula=None,molar_mass_g_mol=None,identity_status='not_applicable_or_unresolved',is_peptide=False,allowed_molarity=False,allowed_molarity_reason='No verified single-species molar mass assigned.',source_urls=[],source_files=[]))
        p['chemical_reference']=reference
        p['verified_coa_count']=sum(r['product_slug']==p['slug'] for r in coas)
        products.append(p)
        model=dict(selected_reference_name=reference['name'] if reference.get('molar_mass_g_mol') is not None else '',
            model_status='stoichiometry_withheld_catalog_coa_nomenclature_conflict' if p['slug']=='thymalin-10mg' else 'declared_parent_reference' if reference.get('allowed_molarity') else reference['identity_status'],
            model_caveat=reference['allowed_molarity_reason'])
        if p['category'] in ('Single-Species Lyophilized Peptide','Bulk Lyophilized Powder') or reference.get('identity_status')=='unresolved_catalog_coa_nomenclature_conflict' or (reference.get('allowed_molarity') and reference.get('is_peptide')):
            registry.append(dict(product_slug=p['slug'],compound_id=reference['id'],product_name=p['name'],category=p['category'],**model,cas=reference.get('cas'),molecular_formula=reference.get('formula'),molar_mass_g_mol=reference.get('molar_mass_g_mol'),molar_mass_convention=reference.get('convention') or DISCLOSURES['mass'],nominal_sizes=p['nominal_sizes'],formulations=p['formulations'],canonical_url=p['canonical_url'],identity_status=reference['identity_status'],allowed_molarity=reference['allowed_molarity'],source_urls=reference.get('source_urls'),exclusion_reason=reference.get('allowed_molarity_reason') if not reference['allowed_molarity'] else ''))
        if reference['allowed_molarity'] and reference.get('is_peptide'):
            assert reference.get('molar_mass_g_mol') and reference.get('source_urls'), p['slug']
            for size in p['nominal_sizes']:
                if size['unit']!='mg':continue
                for volume in STANDARD_FINAL_VOLUMES_ML:
                    matrix.append(dict(product_slug=p['slug'],compound_id=reference['id'],**model,nominal_mass_mg=str(size['value']),final_volume_ml=volume,molar_mass_g_mol=str(reference['molar_mass_g_mol']),**calculate(size['value'],volume,reference['molar_mass_g_mol']),mass_basis='nominal mass assumed to equal net anhydrous parent-complex mass' if reference.get('compound_class')=='peptide_copper_complex_reference' else 'nominal mass assumed to equal net anhydrous parent-peptide mass',volume_basis='final solution volume',canonical_url=p['canonical_url']))
    counts=dict(products=len(products),chemical_reference_rows=len(registry),matrix_rows=len(matrix),coa_records=len(coas),products_with_coa=sum(p['verified_coa_count']>0 for p in products),products_with_molarity=len({r['product_slug'] for r in matrix}))
    ledger,exclusions,unresolved,accounting=derive_accounting(products,matrix)
    inventory=dict(edition=EDITION,capture_date='2026-10-22',scope='Reference release prepared locally; deployment is separately verified',summary=counts,catalog_accounting=accounting,coverage=cat['coverage'],disclosures=DISCLOSURES,products=products,coa_records=coas,local_coa_assets=read_json('inputs/local-coa-assets.json'),local_search_coverage=read_json('inputs/local-coa-search-coverage.json'))
    dump('catalog-coa-inventory.json',inventory)
    csv_write('catalog_molarity_accounting.csv',list(ledger[0]),ledger)
    csv_write('catalog_non_single_species_exclusions.csv',list(exclusions[0]),exclusions)
    csv_write('catalog_withheld_stoichiometry.csv',list(unresolved[0]),unresolved)
    dump('catalog_dispositions_manifest.json',dict(edition=EDITION,review_date='2026-10-25',summary=accounting,products=ledger))
    dump('catalog_unresolved_identity_manifest.json',dict(review_date='2026-10-25',full_catalog_molarity_complete=accounting['full_catalog_molarity_complete'],products=unresolved,primary_identity_review=read_json('inputs/catalog-resolution-review.json')))
    csv_write('catalog_unresolved_identity_requirements.csv',list(unresolved[0]),unresolved)
    csv_write('compound_reference_registry.csv',list(registry[0]),registry)
    csv_write('multi_peptide_molarity_matrix.csv',list(matrix[0]),matrix)
    fields=['product_slug','report_id','lot','nominal_mass_mg','nominal_volume_ml','nominal_label','reported_hplc_purity_percent','reported_content','purity_method','received_date','reported_date','test_date','formulation','source_url','source_file','source_sha256','review_method','notes']
    csv_write('multi_peptide_reported_coa_results.csv',fields,coas)
    make_site(products,matrix,coas,exclusions,unresolved,accounting)
    sources=[]
    for folder in ('inputs','sources'):
        for path in sorted((BASE/folder).rglob('*')):
            if path.is_file():sources.append(dict(file=path.relative_to(BASE).as_posix(),sha256=hash_file(path),bytes=path.stat().st_size))
    dump('multi_peptide_source_manifest.json',dict(edition=EDITION,files=sources,reports=[{k:r.get(k) for k in ('report_id','product_slug','source_url','source_file','source_sha256','field_evidence','review_method')} for r in coas],disclosure='Hashes lock acquired evidence bytes; they do not independently validate laboratory measurements.'))
    dump('build-summary.json',counts)
    print(json.dumps(counts))

if __name__=='__main__':main()
