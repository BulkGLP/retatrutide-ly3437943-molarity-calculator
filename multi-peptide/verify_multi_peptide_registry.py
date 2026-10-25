"""Verify the local R3 release; default includes fresh read-only HTTP checks.

This checks evidence integrity/transcription correspondence, not lab accuracy.
Unresolved product identity is explicitly excluded, never silently completed.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from build_registry import DISCLOSURES, PUBLIC_SITE_URL

BASE=Path(__file__).resolve().parent

def read(root,name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
def csv_rows(root,name):
    with (root/name).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def norm(value):return re.sub(r'\s+','',str(value)).casefold()

class Html(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.text=[];self.robots=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a':self.links.append(a)
        if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content',''))
    def handle_data(self,data):self.text.append(data)

def request(url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'BulkGLP-Registry-Verification/2026.10.R3'}),timeout=35) as response:
            response.read(256)
            return dict(url=url,status=response.status,final_url=response.url,checked_at_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:return dict(url=url,status=getattr(exc,'code',None),error=str(exc))

def verify(root,online=True):
    errors=[];warnings=[];checks=0
    def check(condition,message):
        nonlocal checks
        checks+=1
        if not condition:errors.append(message)
    inv=read(root,'catalog-coa-inventory.json'); manifest=read(root,'multi_peptide_source_manifest.json')
    cat=read(root,'inputs/catalog-products.json'); chemistry=read(root,'inputs/chemical-references.json')
    catalog={p['slug']:p for p in cat['products']};products={p['slug']:p for p in inv['products']}
    check(inv['edition']=='2026.10.R3','Wrong edition')
    check(len(products)==44 and set(products)==set(catalog),'Catalog coverage differs from captured 44 products')
    for f in manifest['files']:
        path=root/f['file']
        check(path.is_file() and sha(path)==f['sha256'],'Source hash mismatch: '+f['file'])
    actual_sources={p.relative_to(root).as_posix() for folder in ('inputs','sources') for p in (root/folder).rglob('*') if p.is_file()}
    check({f['file'] for f in manifest['files']}==actual_sources and len(manifest['files'])==len(actual_sources),'Source manifest file coverage is incomplete or duplicated')
    check(set(inv['disclosures'])==set(DISCLOSURES),'Disclosure dictionary incomplete')
    for r in chemistry['references']:
        if r.get('molar_mass_g_mol') is not None:
            properties=[]
            for filename in r.get('source_files',[]):
                if filename.endswith('.json'):
                    data=read(root,filename)
                    if isinstance(data,dict):
                        payload=data.get('response',data)
                        if isinstance(payload,dict):properties.extend(payload.get('PropertyTable',{}).get('Properties',[]))
            check(any(p.get('CID')==r.get('pubchem_cid') and Decimal(str(p.get('MolecularWeight','0')))==Decimal(str(r['molar_mass_g_mol'])) and p.get('MolecularFormula')==r['formula'] for p in properties),'CID/mass/formula differ from PubChem snapshot: '+r['id'])
            check(bool(r.get('cas')) and bool(r.get('source_urls')),'Missing chemical identifier/source: '+r['id'])
            chemistry_evidence=[root/f for f in r.get('source_files',[]) if f.startswith('sources/chemistry/')]
            check(any(str(r['cas']) in f.read_text(encoding='utf-8-sig') for f in chemistry_evidence),'CAS absent from cited chemical evidence: '+r['id'])
            for slug in r['slugs']:
                check('sources/catalog/'+slug+'.extracted.json' in r.get('source_files',[]),'Chemical assignment lacks mapped catalog evidence: '+r['id']+' '+slug)
    reference_map={}
    for r in chemistry['references']:
        for slug in r['slugs']:reference_map.setdefault(slug,[]).append(r)
    for slug,p in products.items():
        source_refs=reference_map.get(slug,[])
        c=p['chemical_reference']
        if len(source_refs)==1:check(c==source_refs[0],'Inventory chemical reference differs from evidence input: '+slug)
        elif len(source_refs)>1:check(c.get('molar_mass_g_mol') is None and not c.get('allowed_molarity') and c.get('constituent_references')==source_refs,'Multiple chemical forms improperly collapsed: '+slug)
        else:check(False,'Missing chemical input mapping: '+slug)
    reference_rows=csv_rows(root,'compound_reference_registry.csv')
    expected_registry={s for s,p in products.items() if p['category'] in ('Single-Species Lyophilized Peptide','Bulk Lyophilized Powder') or p['chemical_reference'].get('identity_status')=='unresolved_catalog_coa_nomenclature_conflict' or (p['chemical_reference'].get('allowed_molarity') and p['chemical_reference'].get('is_peptide'))}
    check({r['product_slug'] for r in reference_rows}==expected_registry and len(reference_rows)==len(expected_registry),'Reference registry coverage mismatch')
    for row in reference_rows:
        p=products[row['product_slug']];c=p['chemical_reference']
        for column,key in [('cas','cas'),('molecular_formula','formula'),('molar_mass_g_mol','molar_mass_g_mol')]:
            check(row[column]==('' if c.get(key) is None else str(c[key])),'Reference CSV changed: '+row['product_slug']+' '+column)
        check(row['canonical_url']==p['canonical_url'],'Reference product URL mismatch')
        check(row.get('selected_reference_name')==(c['name'] if c.get('molar_mass_g_mol') is not None else ''),'Reference CSV loses selected parent-species name '+row['product_slug'])
        check(row.get('model_caveat')==c['allowed_molarity_reason'],'Reference CSV loses conditional model/case-specific identity caveat '+row['product_slug'])
        if row['product_slug']=='thymalin-10mg':check(row.get('model_status')=='stoichiometry_withheld_catalog_coa_nomenclature_conflict' and not row['molar_mass_g_mol'],'Reference CSV silently resolves Thymalin identity conflict')
    matrix=csv_rows(root,'multi_peptide_molarity_matrix.csv');expected=set()
    for slug,p in products.items():
        c=p['chemical_reference']
        if c.get('allowed_molarity') and c.get('is_peptide'):
            for size in p['nominal_sizes']:
                if size['unit']=='mg':
                    for volume in ('1.0','1.5','2.0','2.5'):expected.add((slug,Decimal(str(size['value'])),Decimal(volume)))
        elif c.get('identity_status') in ('unresolved_catalog_species','unresolved_catalog_coa_nomenclature_conflict'):warnings.append('Stoichiometry withheld: '+slug)
        conditional_preparation_model=(slug=='thymalin-10mg' and p.get('category_is_provisional') and c.get('identity_status')=='reference_species_supported_from_named_coa_with_explicit_model' and c.get('pubchem_cid')==3085284 and c.get('reported_identity_source_report')=='2608100933')
        if p['category'] in ('Multi-Peptide Blend','Bacteriostatic / Accessory') and not conditional_preparation_model:
            check(c.get('molar_mass_g_mol') is None and not c.get('allowed_molarity'),'Invalid single molecular mass on mixture/accessory '+slug)
        check(p['canonical_url']==catalog[slug]['canonical_url'],'Canonical URL changed: '+slug)
        check(p['nominal_sizes']==catalog[slug]['nominal_sizes'],'Nominal size changed without catalog evidence: '+slug)
    keys=[]
    for r in matrix:
        slug=r['product_slug'];p=products.get(slug);check(p is not None,'Unknown matrix product '+slug)
        if not p:continue
        c=p['chemical_reference'];check(c.get('allowed_molarity') and c.get('is_peptide'),'Disallowed species in molarity matrix '+slug)
        check(r.get('selected_reference_name')==c['name'],'Molarity CSV loses selected parent-species name '+slug)
        check(r.get('model_caveat')==c['allowed_molarity_reason'],'Molarity CSV loses conditional model/case-specific identity caveat '+slug)
        if slug=='thymalin-10mg':check(r.get('model_status')=='conditional_catalog_report_identity_conflict' and 'Thymalin' in r.get('model_caveat','') and 'Thymulin' in r.get('model_caveat','') and 'zinc' in r.get('model_caveat',''),'Molarity CSV silently resolves Thymalin or loses zinc-free parent scope')
        m,v,mw=map(Decimal,(r['nominal_mass_mg'],r['final_volume_ml'],r['molar_mass_g_mol']))
        check(m>0 and v>0 and mw>0,'Non-positive arithmetic input '+slug)
        check(mw==Decimal(str(c.get('molar_mass_g_mol') or 0)),'Matrix molar mass mismatch '+slug)
        # Independent dimensional recomputation, deliberately not registry_math.calculate.
        concentration=m/v; molar_M=(m/Decimal(1000))/mw/(v/Decimal(1000))
        for key,value in [('mass_concentration_mg_ml',concentration),('molarity_mM',molar_M*1000),('molarity_uM',molar_M*1000000)]:
            check(abs(Decimal(r[key])-value)<=Decimal('0.0000000051'),'Arithmetic mismatch '+slug+' '+key)
        keys.append((slug,m,v))
    check(set(keys)==expected and len(keys)==len(expected),'Matrix coverage/duplicate rows mismatch')
    # Separate complete accounting from complete science. This is independently
    # recomputed here, not copied from the builder's completeness boolean.
    review=read(root,'inputs/catalog-resolution-review.json')
    ledger=csv_rows(root,'catalog_molarity_accounting.csv')
    exclusions=csv_rows(root,'catalog_non_single_species_exclusions.csv')
    unresolved_manifest=read(root,'catalog_unresolved_identity_manifest.json')
    disposition={};matrix_counts={s:sum(r['product_slug']==s for r in matrix) for s in products}
    for slug,p in products.items():
        c=p['chemical_reference'];state=c.get('identity_status')
        if state=='unresolved_catalog_species':status='stoichiometry_withheld_pending_sequence_specification'
        elif state=='unresolved_catalog_coa_nomenclature_conflict':status='stoichiometry_withheld_catalog_coa_nomenclature_conflict'
        elif state in ('multi_component_formulation_no_single_molar_mass','formulation_specific_references_only'):status='non_single_species_exclusion'
        elif c.get('allowed_molarity') and c.get('is_peptide') and matrix_counts[slug]:status='computed_peptide_reference'
        elif not c.get('is_peptide') and c.get('molar_mass_g_mol') and not c.get('allowed_molarity'):status='verified_non_peptide_reference_outside_matrix'
        else:status='unaccounted'
        disposition[slug]=status
    check(len(ledger)==44 and {r['product_slug'] for r in ledger}==set(products),'Catalog accounting must include every product exactly once')
    for r in ledger:
        slug=r['product_slug'];p=products.get(slug)
        if not p:continue
        check(r['accounting_status']==disposition[slug] and disposition[slug]!='unaccounted','Incorrect catalog accounting disposition '+slug)
        check(r['canonical_url']==p['canonical_url'] and json.loads(r['nominal_sizes'])==p['nominal_sizes'],'Accounting URL/nominal size differs from catalog '+slug)
        check(r['reason']==p['chemical_reference']['allowed_molarity_reason'],'Accounting scientific reason changed '+slug)
        check(r['molarity_computed']==str(bool(matrix_counts[slug])) and int(r['matrix_rows'])==matrix_counts[slug],'Accounting arithmetic claim differs from matrix '+slug)
    reviewed_exclusions={r['product_slug']:r for r in review['reviewed_non_single_species_exclusions']}
    excluded={s for s,d in disposition.items() if d=='non_single_species_exclusion'}
    unresolved_set={s for s,d in disposition.items() if d=='stoichiometry_withheld_pending_sequence_specification'}
    conditional_conflicts={s for s,d in disposition.items() if d=='stoichiometry_withheld_catalog_coa_nomenclature_conflict'}
    withheld_set=unresolved_set|conditional_conflicts
    check(unresolved_set=={'foxo4-10mg','adamax','ahk-cu-10000mg'} and conditional_conflicts=={'thymalin-10mg'},'Required withheld stoichiometry dispositions changed')
    check(set(reviewed_exclusions)==excluded,'Scientific exclusion set differs from reviewed catalog composition evidence')
    check(len(exclusions)==len(excluded) and {r['product_slug'] for r in exclusions}==excluded,'Scientific exclusion CSV coverage missing/duplicated')
    expected_exclusion_fields={'product_slug','product_name','canonical_url','nominal_sizes','offer_formats','reference_page','molarity_computed','matrix_rows','exclusion_kind','scientific_reason','catalog_evidence_file','catalog_evidence_literal','exclusion_scope'}
    for r in exclusions:
        slug=r['product_slug'];p=products.get(slug)
        check(set(r)==expected_exclusion_fields,'Unexpected scientific exclusion schema '+slug)
        if not p or slug not in reviewed_exclusions:continue
        original=reviewed_exclusions[slug]
        check(r['exclusion_kind']==original['exclusion_kind'],'Scientific exclusion type changed '+slug)
        check(r['scientific_reason']==p['chemical_reference']['allowed_molarity_reason'],'Scientific exclusion reason changed '+slug)
        check(r['catalog_evidence_file']==original['catalog_evidence_file'] and r['catalog_evidence_literal']==original['catalog_evidence_literal']==catalog[slug]['description'],'Scientific exclusion lacks matching composition evidence '+slug)
        check(r['molarity_computed']=='False' and r['matrix_rows']=='0' and matrix_counts[slug]==0,'Exclusion is improperly described as computed molarity '+slug)
        check(r['canonical_url']==p['canonical_url'],'Exclusion storefront URL changed '+slug)
    reviewed_unresolved={r['product_slug']:r for r in review['unresolved_identity_products']}
    requirements=csv_rows(root,'catalog_unresolved_identity_requirements.csv')
    check(len(requirements)==len(withheld_set) and {r['product_slug'] for r in requirements}==withheld_set,'Supplier requirements CSV coverage missing/duplicated')
    for r in requirements:
        if r['product_slug'] in reviewed_unresolved:check(r['supplier_data_needed']==reviewed_unresolved[r['product_slug']]['supplier_data_needed'],'Supplier requirements changed '+r['product_slug'])
    check(set(reviewed_unresolved)==unresolved_set,'Unresolved identity falsely reclassified without reviewed evidence')
    check(len(unresolved_manifest['products'])==len(withheld_set) and {r['product_slug'] for r in unresolved_manifest['products']}==withheld_set,'Unresolved identity manifest coverage missing/duplicated')
    check(unresolved_manifest['primary_identity_review']==review,'Unresolved manifest lost primary scientific review')
    withheld_rows=csv_rows(root,'catalog_withheld_stoichiometry.csv')
    check(len(withheld_rows)==4 and {r['product_slug'] for r in withheld_rows}==withheld_set,'Withheld stoichiometry manifest coverage missing/duplicated')
    for r in withheld_rows:
        slug=r['product_slug'];c=products[slug]['chemical_reference']
        check(c.get('molar_mass_g_mol') is None and c.get('cas') is None and c.get('formula') is None and not c.get('allowed_molarity') and matrix_counts[slug]==0,'Withheld identity assigned an invented chemical tuple or matrix '+slug)
        check(r['molarity_computed']=='False' and r['matrix_rows']=='0' and r['original_flag_reason']==c['allowed_molarity_reason'] and bool(r['supplier_data_needed']),'Withheld record loses evidence/requirements '+slug)
    dispositions_manifest=read(root,'catalog_dispositions_manifest.json')
    check(len(dispositions_manifest['products'])==44 and {r['product_slug']:r['accounting_status'] for r in dispositions_manifest['products']}==disposition,'Disposition manifest differs from independent full catalog accounting')
    check(dispositions_manifest['summary']==inv['catalog_accounting'],'Disposition manifest summary differs from accounting')
    for slug,r in reviewed_unresolved.items():
        c=products[slug]['chemical_reference']
        check(c['identity_status']=='unresolved_catalog_species' and not c.get('allowed_molarity') and c.get('molar_mass_g_mol') is None,'Unresolved identity assigned unsubstantiated molarity '+slug)
        check(bool(r['supplier_data_needed']) and r['original_flag_reason']==c['allowed_molarity_reason'],'Missing original identity reason or supplier resolution requirements '+slug)
        check(r['catalog_evidence_literal']==catalog[slug]['description'],'Identity review catalog evidence changed '+slug)
        for candidate in r['candidate_references']:
            prop=read(root,candidate['source_files'][0])['response']['PropertyTable']['Properties'][0]
            check(prop['CID']==candidate['pubchem_cid'] and prop['MolecularFormula']==candidate['formula'] and Decimal(prop['MolecularWeight'])==Decimal(candidate['average_molar_mass_g_mol']),'Candidate parameters differ from primary PubChem source '+slug)
            check(candidate['selected_for_catalog'] is False,'Unresolved candidate falsely selected as catalog identity '+slug)
    for r in review['resolved_reference_products']:
        slug=r['product_slug'];c=products[slug]['chemical_reference'];assigned=r['assigned_reference']
        if slug=='thymalin-10mg':
            check(c['identity_status']=='unresolved_catalog_coa_nomenclature_conflict' and not c['allowed_molarity'] and c['molar_mass_g_mol'] is None,'Thymalin withholding superseded by historical candidate assignment')
            check(all(word in c['allowed_molarity_reason'] for word in ('Thymalin','Thymulin','nonathymulin')),'Thymalin nomenclature distinction missing')
            from pypdf import PdfReader
            direct='\n'.join(p.extract_text() or '' for p in PdfReader(root/'sources/coa/Bulk2608100933.pdf').pages)
            check(norm('Identity (LC-MS) Thymulin') in norm(direct),'Thymalin conflict lacks original COA identity evidence')
            continue
        check(c['cas']==assigned['cas'] and c['formula']==assigned['formula'] and c['pubchem_cid']==assigned['pubchem_cid'] and Decimal(str(c['molar_mass_g_mol']))==Decimal(assigned['average_molar_mass_g_mol']),'Reviewed named reference differs from assigned model '+slug)
        if slug in ('tb-500','thymalin-10mg'):
            report='2605280346' if slug=='tb-500' else '2608100933'
            identity='Thymosin Beta-4' if slug=='tb-500' else 'Thymulin'
            cid=16132341 if slug=='tb-500' else 3085284
            check(c.get('reported_identity_source_report')==report and c['pubchem_cid']==cid and c['identity_status']=='reference_species_supported_from_named_coa_with_explicit_model','Wrong conditional report-named reference '+slug)
            from pypdf import PdfReader
            direct='\n'.join(p.extract_text() or '' for p in PdfReader(root/f'sources/coa/Bulk{report}.pdf').pages)
            check(norm('Identity (LC-MS) '+identity) in norm(direct),'Conditional identity model lacks named LC-MS report evidence '+slug)
    # Preserve the source's neutral charge and exact CAS/CID linkage. A cation
    # sharing a CAS synonym is not interchangeable with this neutral reference.
    ghk=next(r for r in chemistry['references'] if r['id']=='ghk_cu')
    gsrs=read(root,'sources/chemistry/checkpoint-2026-10-24/ghk-cu-gsrs-full.json')['response']
    check(gsrs['approvalID']=='6BJQ43T1I9' and gsrs['structure']['charge']==0 and gsrs['structure']['formula']=='C14H22N6O4.Cu','GSRS neutral GHK-Cu reference composition/charge changed')
    check(any(r['codeSystem']=='CAS' and r['code']==ghk['cas'] for r in gsrs['codes']) and any(r['codeSystem']=='PUBCHEM' and r['code']==str(ghk['pubchem_cid']) for r in gsrs['codes']),'GHK-Cu CAS/CID linkage differs from primary GSRS record')
    check(ghk['formula']=='C14H22CuN6O4' and ghk['pubchem_cid']==10111685 and Decimal(str(ghk['molar_mass_g_mol']))==Decimal('401.91'),'Wrong neutral 1:1 GHK-Cu model')
    accounting=inv['catalog_accounting']
    accounting_complete=(len(ledger)==44 and {r['product_slug'] for r in ledger}==set(products) and 'unaccounted' not in disposition.values())
    science_complete=accounting_complete and not unresolved_set and not conditional_conflicts
    check(accounting['full_catalog_accounted_for']==accounting_complete,'Incorrect full catalog accounting flag')
    check(accounting['full_catalog_molarity_complete']==science_complete and unresolved_manifest['full_catalog_molarity_complete']==science_complete,'False full catalog molarity completeness claim')
    check(set(accounting['unresolved_identity_product_slugs'])==unresolved_set and accounting['exclusions_are_computed_molarities'] is False,'Accounting confuses exclusions/unresolved identities with molarity')
    check(set(accounting['conditional_identity_conflict_product_slugs'])==conditional_conflicts,'Conditional reference arithmetic falsely resolves catalog/report identity conflict')
    check(set(accounting['withheld_stoichiometry_product_slugs'])==withheld_set,'Accounting omits withheld identities')
    actual_disposition_counts={s:list(disposition.values()).count(s) for s in set(disposition.values())}
    check(accounting['disposition_counts']==actual_disposition_counts,'Catalog disposition counts differ from independent accounting')
    current=read(root,review['current_site_review']['file'])
    check(current['findings']==review['current_site_review']['findings'] and {r['product_slug'] for r in current['findings']}=={'foxo4-10mg','adamax','ahk-cu-10000mg','tb-500','thymalin-10mg'},'Fresh current-site scientific review missing products or findings')
    for r in current['files']:
        check((root/r['file']).is_file() and sha(root/r['file'])==r['sha256'],'Current-site scientific evidence hash changed '+r['file'])
    for slug,report,current_file in [('tb-500','2605280346','tb-500-current-coa.pdf'),('thymalin-10mg','2608100933','Bulk2608100933.pdf'),('adamax','2606190267','adamax-current-coa-Bulk2606190267.pdf')]:
        check(sha(root/'sources/catalog/checkpoint-2026-10-24'/current_file)==sha(root/f'sources/coa/Bulk{report}.pdf'),'Current linked COA differs from reviewed original '+slug)
    acquired=read(root,'inputs/coa-acquisition.json')['records'];locked={r['source_url']:r for r in acquired}
    coa_input=read(root,'inputs/coa-records.json');coa_input=coa_input if isinstance(coa_input,list) else coa_input['records']
    coa={r['source_url']:r for r in coa_input};coacsv=csv_rows(root,'multi_peptide_reported_coa_results.csv')
    check(len(coa)==49 and set(coa)==set(locked),'Published COA source set mismatch')
    check(len(coacsv)==49 and {r['source_url'] for r in coacsv}==set(coa),'COA CSV missing or duplicate sources')
    check(inv['coa_records']==coa_input,'Inventory COA records differ from reviewed transcription')
    for r in coacsv:
        original=coa[r['source_url']];acquisition=locked[r['source_url']]
        for key,value in r.items():
            expectedvalue=original.get(key)
            if isinstance(expectedvalue,(dict,list)):expectedvalue=json.dumps(expectedvalue,ensure_ascii=False)
            elif expectedvalue is None:expectedvalue=''
            else:expectedvalue=str(expectedvalue)
            check(value==expectedvalue,'COA CSV field mismatch: '+r['report_id']+' '+key)
        check(original['source_sha256']==acquisition['sha256']==sha(root/original['source_file']),'COA original file hash mismatch '+r['report_id'])
        check(original['product_slug']==acquisition['product_slug'],'COA-to-product mapping changed '+r['report_id'])
        check(bool(original.get('review_method')) and bool(original.get('field_evidence')),'COA review evidence missing '+r['report_id'])
        pdftext=None
        if original['source_file'].lower().endswith('.pdf'):
            from pypdf import PdfReader
            pdftext='\n'.join(page.extract_text() or '' for page in PdfReader(root/original['source_file']).pages)
        if original.get('test_date'):
            check(bool(original.get('field_evidence',{}).get('test_date')),'Unsubstantiated test date '+r['report_id'])
        for field,evidence in original.get('field_evidence',{}).items():
            if not isinstance(evidence,dict):continue
            evidencefile=evidence.get('evidence_file') or evidence.get('source_file')
            if evidencefile:
                path=root/evidencefile;check(path.is_file(),'Evidence file missing '+str(evidencefile))
                if path.is_file() and evidence.get('evidence_sha256'):check(sha(path)==evidence['evidence_sha256'],'Field evidence hash changed '+r['report_id']+' '+field)
                literal=evidence.get('literal')
                if path.is_file() and path.suffix=='.txt' and literal:
                    literals=literal if isinstance(literal,list) else [literal]
                    evidence_text=path.read_text(encoding='utf-8-sig')
                    for item in literals:
                        check(norm(item) in norm(evidence_text),'Literal missing from evidence '+r['report_id']+' '+field)
                        if pdftext is not None:check(norm(item) in norm(pdftext),'Literal absent from original PDF '+r['report_id']+' '+field)
            literal=evidence.get('literal')
            if literal is not None and field in original and original[field] is not None:
                literaltxt=' '.join(str(x) for x in literal) if isinstance(literal,list) else str(literal)
                value=original[field]
                if field=='reported_hplc_purity_percent':
                    numbers=re.findall(r'(\d+(?:\.\d+)?)\s*%',literaltxt)
                    check(any(Decimal(x)==Decimal(str(value)) for x in numbers),'Purity value disagrees with source literal '+r['report_id'])
                elif field in ('nominal_mass_mg','nominal_volume_ml'):
                    unit='mg' if field=='nominal_mass_mg' else 'm[lL]'
                    numbers=re.findall(r'(\d+(?:\.\d+)?)\s*'+unit,literaltxt)
                    check(any(Decimal(x)==Decimal(str(value)) for x in numbers),'Nominal sample value disagrees with source literal '+r['report_id'])
                elif field in ('received_date','reported_date','test_date'):
                    dates=[]
                    for token in re.findall(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}',literaltxt):
                        for fmt in ('%m/%d/%Y','%m/%d/%y','%Y-%m-%d','%Y/%m/%d'):
                            try:dates.append(datetime.strptime(token,fmt).date().isoformat())
                            except ValueError:pass
                    # Some image reports spell the month; their reviewed transcription includes ISO date fields.
                    if not dates:
                        for fmt in ('%d %B %Y','%B %d, %Y','%d %b %Y','%b %d, %Y'):
                            try:dates.append(datetime.strptime(literaltxt,fmt).date().isoformat())
                            except ValueError:pass
                    check(value in dates,'Date value disagrees with source literal '+r['report_id']+' '+field)
                elif field=='reported_content':
                    if isinstance(value,list):
                        for item in value:
                            own=item.get('source_literal','')
                            check(norm(own) in norm(literaltxt),'Component literal absent from reported evidence '+r['report_id'])
                            if pdftext is not None:check(norm(own) in norm(pdftext),'Component literal absent from PDF '+r['report_id'])
                            quantities=re.findall(r'(\d+(?:\.\d+)?)\s*('+re.escape(str(item['unit']))+r')(?![A-Za-z])',own)
                            check(any(Decimal(number)==Decimal(str(item['value'])) for number,unit in quantities),'Reported component quantity/unit disagrees with own source literal '+r['report_id'])
                            if len(value)>1:check(norm(item['name']) in norm(own),'Reported component identity differs from own source literal '+r['report_id'])
                    else:check(norm(value) in norm(literaltxt),'Reported content disagrees with source literal '+r['report_id'])
                elif field in ('report_id','lot','nominal_label','purity_method'):
                    check(norm(value) in norm(literaltxt),'Assigned value disagrees with source literal '+r['report_id']+' '+field)
        purity=original.get('reported_hplc_purity_percent')
        check(purity is None or Decimal(0)<=Decimal(str(purity))<=Decimal(100),'Invalid purity range '+r['report_id'])
        if purity is None:
            literal=original.get('field_evidence',{}).get('reported_hplc_purity_percent',{}).get('literal')
            check(not literal or not re.search(r'\d\s*%',str(literal)),'Purity discarded despite numerical source evidence '+r['report_id'])
    urls=set(p['canonical_url'] for p in products.values())|set(coa)|{'https://bulkglp.com/','https://bulkglp.com/verified-quality/'}
    local=read(root,'inputs/local-coa-assets.json')
    check(inv['local_coa_assets']==local,'Local archive inventory differs from input')
    coverage=read(root,'inputs/local-coa-search-coverage.json')
    check(inv['local_search_coverage']==coverage and not coverage['errors'] and not coverage['additional_unexplored_assets'],'Local COA search coverage is incomplete')
    for r in local['additional_records']:
        from pypdf import PdfReader
        check(sha(root/r['source_file'])==r['source_sha256'],'Local supplemental COA hash mismatch '+r['report_id'])
        direct='\n'.join(p.extract_text() or '' for p in PdfReader(root/r['source_file']).pages)
        check(r['source_scope']=='local_only' and r.get('source_url') is None,'Local supplement misrepresented as public '+r['report_id'])
        for field,evidence in r.get('field_evidence',{}).items():
            literal=evidence.get('literal')
            for item in (literal if isinstance(literal,list) else [literal]):
                if item:check(norm(item) in norm(direct),'Supplemental literal absent from original PDF '+r['report_id']+' '+field)
        purity_evidence=r.get('field_evidence',{}).get('reported_hplc_purity_percent',{}).get('literal','')
        if r.get('reported_hplc_purity_percent') is not None:
            check(any(Decimal(x)==Decimal(str(r['reported_hplc_purity_percent'])) for x in re.findall(r'(\d+(?:\.\d+)?)\s*%',str(purity_evidence))),'Supplemental purity differs from source '+r['report_id'])
    for slug,p in products.items():
        path=root/'site-preview/compounds'/slug/'index.html';check(path.is_file(),'Missing HTML '+slug)
        if not path.is_file():continue
        parser=Html();parser.feed(path.read_text(encoding='utf-8'));text=' '.join(parser.text)
        check(any('index,follow'==v for v in parser.robots),'Missing indexability directive '+slug)
        for required in DISCLOSURES.values():check(required in text,'Missing scientific disclosure '+slug)
        for note in p['chemical_reference'].get('notes',[]):check(note in text,'Missing compound-specific caveat '+slug)
        for note in p.get('identity_notes',[]):check(note in text,'Missing catalog identity/formulation scope '+slug)
        reason=p['chemical_reference'].get('allowed_molarity_reason')
        if reason:check(reason in text,'Missing calculation scope '+slug)
        for target in [p['canonical_url'],'https://bulkglp.com/verified-quality/']:
            matches=[a for a in parser.links if a.get('href')==target]
            check(bool(matches) and all(not(set(a.get('rel','').split())&{'nofollow','sponsored','ugc'}) for a in matches),'Missing followed deep link '+slug+' '+target)
        for a in parser.links:
            target=a.get('href','')
            if target and not target.startswith(('https://','http://','#')):check((path.parent/target).resolve().exists(),'Broken local link '+slug+' '+target)
    for filename,slugs in [('catalog-exclusions.html',excluded),('unresolved-identities.html',withheld_set),('catalog-dispositions.html',set(products))]:
        path=root/'site-preview'/filename
        check(path.is_file(),'Missing catalog accounting reference page '+filename)
        if not path.is_file():continue
        parser=Html();parser.feed(path.read_text(encoding='utf-8'))
        check('index,follow' in parser.robots,'Accounting reference page lacks indexability '+filename)
        for slug in slugs:
            matches=[a for a in parser.links if a.get('href')==products[slug]['canonical_url']]
            check(bool(matches) and all(not(set(a.get('rel','').split())&{'nofollow','sponsored','ugc'}) for a in matches),'Accounting page missing followed storefront deep link '+filename+' '+slug)
        for a in parser.links:
            target=a.get('href','')
            if target and not target.startswith(('https://','http://','#')):check((path.parent/target).resolve().exists(),'Broken accounting local link '+filename+' '+target)
    hub=(root/'site-preview/index.html').read_text(encoding='utf-8')
    check('Thymalin 10mg [stoichiometry withheld: Thymalin / Thymulin conflict]' in hub and 'No Thymalin mass or molarity rows are published.' in hub,'Hub omits Thymalin withholding or nomenclature distinction')
    check('4731 g/mol' in hub and '4731.33 g/mol' in hub,'Hub silently merges R3 and historical Retatrutide mass conventions')
    hub_parser=Html();hub_parser.feed(hub)
    for p in products.values():
        matches=[a for a in hub_parser.links if a.get('href')==p['canonical_url']]
        check(bool(matches) and all(not(set(a.get('rel','').split())&{'nofollow','sponsored','ugc'}) for a in matches),'Hub missing direct followed catalog product link '+p['slug'])
    sitemap_path=root/'site-preview/sitemap.xml'
    expected_site_paths={'index.html','catalog-exclusions.html','unresolved-identities.html','catalog-dispositions.html'}|{'compounds/'+slug+'/index.html' for slug in products}
    if sitemap_path.is_file():
        try:
            sitemap=ElementTree.parse(sitemap_path)
            locations=[n.text for n in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            check(set(locations)=={PUBLIC_SITE_URL+p for p in expected_site_paths} and len(locations)==len(expected_site_paths),'Sitemap omits or duplicates public reference pages')
        except ElementTree.ParseError:check(False,'Invalid sitemap XML')
    else:check(False,'Missing publication sitemap')
    for name in ('compound_reference_registry.csv','multi_peptide_molarity_matrix.csv','multi_peptide_reported_coa_results.csv','catalog_molarity_accounting.csv','catalog_non_single_species_exclusions.csv','catalog_withheld_stoichiometry.csv'):
        copy=root/'site-preview/data'/name
        check(copy.is_file() and sha(copy)==sha(root/name),'Published CSV download differs from verified artifact '+name)
    if online:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:network=list(pool.map(request,sorted(urls)))
        (root/'verification-http-results.json').write_text(json.dumps(network,indent=2),encoding='utf-8')
    else:
        network=read(root,'verification-http-results.json')
        warnings.append('HTTP not refreshed in this run; cached prior observations only.')
    check({r['url'] for r in network}==urls,'HTTP verification URL coverage mismatch')
    for response in network:check(response['status']==200,'HTTP target did not return 200: '+response['url'])
    unresolved=[p['slug'] for p in products.values() if p['chemical_reference'].get('identity_status')=='unresolved_catalog_species']
    conflicts=[r['report_id'] for r in coa_input if r.get('notes')]
    ready=bool(accounting_complete and not errors)
    result=dict(edition='2026.10.R3',checked_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=1 if errors else 0,checks=checks,errors=errors,warnings=warnings,counts=inv['summary'],catalog_accounting=accounting,http_fresh=online,publication_performed=False,publication_ready=ready,publication_gate={'full_catalog_accounted_for':accounting_complete,'all_integrity_arithmetic_coa_link_disclosure_checks_pass':not errors,'full_catalog_molarity_complete_required':False},full_catalog_accounted_for=accounting_complete and not errors,full_catalog_molarity_complete=science_complete and not errors,unresolved_identity_product_slugs=unresolved,conditional_reference_product_slugs=sorted(s for s in ('ghk-cu','ghk-cu-10000mg','tb-500') if products[s]['chemical_reference'].get('allowed_molarity')),nomenclature_conflict_product_slugs=sorted(conditional_conflicts),withheld_stoichiometry_product_slugs=sorted(withheld_set),reviewed_coa_records_with_notes=conflicts,verification_scope='Artifact integrity, deterministic arithmetic, source/transcription correspondence, exhaustive scientific catalog accounting, current-site source correspondence, disclosures and HTTP targets. Exclusions and withheld dispositions are not computed molarities. Does not remeasure or independently authenticate laboratory results. Raster correspondence relies on recorded visual review of hash-locked originals.',publication_recommendation='Ready for publication as an explicitly scoped reference compilation; mathematical completeness remains false and deployment must be verified separately.' if ready else 'Publication blocked by failed integrity, accounting or disclosure checks.')
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');parser.add_argument('--root',type=Path,default=BASE);args=parser.parse_args()
    try:result=verify(args.root,not args.offline)
    except Exception as exc:result={'exit_code':1,'publication_ready':False,'errors':[type(exc).__name__+': '+str(exc)]}
    (args.root/'verification-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2));return result['exit_code']

if __name__=='__main__':sys.exit(main())
