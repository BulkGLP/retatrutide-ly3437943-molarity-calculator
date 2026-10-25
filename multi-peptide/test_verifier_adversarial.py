"""Adversarial semantic checks on isolated copies; never changes evidence originals.

Run after build_registry.py. Network is deliberately stubbed with local test
fixtures, so these tests prove rejection of artifact mutations, not HTTP health.
Most mutations rebuild all outputs and the source manifest to rule out merely
catching a stale CSV or hash. Only stdlib is required.
"""
import contextlib,csv,io,json,pathlib,shutil,tempfile
import build_registry as builder
import verify_multi_peptide_registry as verifier

BASE=pathlib.Path(__file__).resolve().parent
def read(root,name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
def write(root,name,data):(root/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def rows(data):return data if isinstance(data,list) else data['records']
def rebuild(root):
    old=builder.BASE
    try:
        builder.BASE=root
        with contextlib.redirect_stdout(io.StringIO()):builder.main()
    finally:builder.BASE=old
def network_fixture(root):
    inventory=read(root,'catalog-coa-inventory.json')
    urls={p['canonical_url'] for p in inventory['products']}|{r['source_url'] for r in inventory['coa_records']}|{'https://bulkglp.com/','https://bulkglp.com/verified-quality/'}
    write(root,'verification-http-results.json',[{'url':u,'status':200,'test_fixture':True} for u in sorted(urls)])
def mutate_coa(root,field,value):
    data=read(root,'inputs/coa-records.json')
    r=next(r for r in rows(data) if r['report_id']=='2606190267')
    r[field]=value
    write(root,'inputs/coa-records.json',data)
    rebuild(root)
def bad_purity(root):mutate_coa(root,'reported_hplc_purity_percent',88.8)
def bad_content(root):
    data=read(root,'inputs/coa-records.json')
    r=next(r for r in rows(data) if r['report_id']=='2606190267')
    r['reported_content'][0]['value']=100.9
    write(root,'inputs/coa-records.json',data);rebuild(root)
def swapped_component_content(root):
    data=read(root,'inputs/coa-records.json')
    r=next(r for r in rows(data) if r['report_id']=='2608100934')
    a,b=r['reported_content'][1],r['reported_content'][2]
    a['value'],b['value']=b['value'],a['value']
    write(root,'inputs/coa-records.json',data);rebuild(root)
def bad_nominal_mass(root):mutate_coa(root,'nominal_mass_mg',80)
def bad_report_date(root):mutate_coa(root,'reported_date','2026-06-24')
def bad_cas(root):
    data=read(root,'inputs/chemical-references.json')
    next(r for r in data['references'] if r['id']=='tesamorelin')['cas']='137525-51-0'
    write(root,'inputs/chemical-references.json',data);rebuild(root)
def bad_cid(root):
    data=read(root,'inputs/chemical-references.json')
    next(r for r in data['references'] if r['id']=='tesamorelin')['pubchem_cid']=9941957
    write(root,'inputs/chemical-references.json',data);rebuild(root)
def swapped_catalog_assignment(root):
    data=read(root,'inputs/chemical-references.json')
    t=next(r for r in data['references'] if r['id']=='tesamorelin')
    b=next(r for r in data['references'] if r['id']=='bpc157')
    t['slugs'],b['slugs']=b['slugs'],t['slugs']
    write(root,'inputs/chemical-references.json',data);rebuild(root)
def rewritten_pdf_companion(root):
    data=read(root,'inputs/coa-records.json')
    r=next(r for r in rows(data) if r['report_id']=='2606190267')
    r['reported_hplc_purity_percent']=88.8
    for ev in r['field_evidence'].values():
        if isinstance(ev,dict) and isinstance(ev.get('literal'),str):ev['literal']=ev['literal'].replace('99.10','88.80')
    path=root/r['extracted_text_file']
    path.write_text(path.read_text(encoding='utf-8').replace('99.10','88.80'),encoding='utf-8')
    write(root,'inputs/coa-records.json',data);rebuild(root)
def removed_source_manifest_entry(root):
    data=read(root,'multi_peptide_source_manifest.json')
    target='sources/chemistry/tesamorelin-properties.json'
    assert any(r['file']==target for r in data['files'])
    data['files']=[r for r in data['files'] if r['file']!=target]
    write(root,'multi_peptide_source_manifest.json',data)
def removed_vip_caveat(root):
    p=root/'site-preview/compounds/vip/index.html'
    txt=p.read_text(encoding='utf-8')
    import re
    txt,n=re.subn(r'<p>Explicit reference model:.*?</p>','',txt,count=1)
    assert n==1,'Expected native-VIP model caveat absent before mutation'
    p.write_text(txt,encoding='utf-8')
def corrupted_molarity(root):
    path=root/'multi_peptide_molarity_matrix.csv'
    with path.open(encoding='utf-8',newline='') as f:r=list(csv.DictReader(f));fields=list(r[0])
    r[0]['molarity_mM']=str(float(r[0]['molarity_mM'])+1)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(r)

def false_full_catalog_complete(root):
    data=read(root,'catalog-coa-inventory.json')
    data['catalog_accounting']['full_catalog_molarity_complete']=True
    write(root,'catalog-coa-inventory.json',data)
def drop_exclusion_row(root):
    path=root/'catalog_non_single_species_exclusions.csv'
    with path.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f));fields=list(records[0])
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records[:-1])
def unresolved_disguised_as_mixture(root):
    data=read(root,'inputs/chemical-references.json')
    r=next(r for r in data['references'] if 'ahk-cu-10000mg' in r['slugs'])
    r['identity_status']='multi_component_formulation_no_single_molar_mass'
    write(root,'inputs/chemical-references.json',data);rebuild(root)
def fake_exclusion_computation(root):
    path=root/'catalog_non_single_species_exclusions.csv'
    with path.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f));fields=list(records[0])
    records[0]['molarity_computed']='True'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
def wrong_ghk_reference_charge(root):
    path='sources/chemistry/checkpoint-2026-10-24/ghk-cu-gsrs-full.json'
    data=read(root,path);data['response']['structure']['charge']=2
    write(root,path,data);rebuild(root)
def missing_unresolved_manifest_entry(root):
    data=read(root,'catalog_unresolved_identity_manifest.json');data['products']=data['products'][:-1]
    write(root,'catalog_unresolved_identity_manifest.json',data)
def nofollow_exclusion_link(root):
    path=root/'site-preview/catalog-exclusions.html'
    content=path.read_text(encoding='utf-8').replace('<a href="https://bulkglp.com/product/lipotropic-c/">','<a rel="nofollow" href="https://bulkglp.com/product/lipotropic-c/">')
    path.write_text(content,encoding='utf-8')
def stripped_conditional_matrix_scope(root):
    path=root/'multi_peptide_molarity_matrix.csv'
    with path.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f));fields=list(records[0])
    r=next(r for r in records if r['product_slug']=='ghk-cu')
    r['model_caveat']='Nominal reference math.';r['model_status']='declared_parent_reference'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)

CASES=[
 ('wrong_coa_purity_rebuilt_outputs',bad_purity),
 ('wrong_coa_content_rebuilt_outputs',bad_content),
 ('swapped_blend_component_content_values',swapped_component_content),
 ('wrong_coa_nominal_mass_rebuilt_outputs',bad_nominal_mass),
 ('wrong_coa_report_date_rebuilt_outputs',bad_report_date),
 ('wrong_chemical_cas_rebuilt_outputs',bad_cas),
 ('wrong_chemical_cid_rebuilt_outputs',bad_cid),
 ('swapped_compound_catalog_mapping',swapped_catalog_assignment),
 ('rewritten_pdf_companion_and_assignments',rewritten_pdf_companion),
 ('source_manifest_omission',removed_source_manifest_entry),
 ('missing_vip_terminal_caveat',removed_vip_caveat),
 ('molarity_arithmetic_error',corrupted_molarity),
 ('false_full_catalog_completeness_claim',false_full_catalog_complete),
 ('missing_scientific_exclusion_row',drop_exclusion_row),
 ('unresolved_identity_disguised_as_mixture',unresolved_disguised_as_mixture),
 ('exclusion_claims_computed_molarity',fake_exclusion_computation),
 ('wrong_neutral_ghk_reference_charge_rebuilt_hashes',wrong_ghk_reference_charge),
 ('missing_unresolved_manifest_entry',missing_unresolved_manifest_entry),
 ('nofollow_storefront_link_on_exclusions_page',nofollow_exclusion_link),
 ('stripped_conditional_ghk_scope_in_standalone_csv',stripped_conditional_matrix_scope),
]
def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix='bulkglp-r3-adversarial-') as temp:
        suite=pathlib.Path(temp)
        pristine=suite/'pristine'
        shutil.copytree(BASE,pristine,ignore=shutil.ignore_patterns('__pycache__'))
        network_fixture(pristine)
        baseline=verifier.verify(pristine,online=False)
        if baseline['errors']:
            print(json.dumps({'status':'BASELINE_FAILED','errors':baseline['errors'],'note':'No adversarial conclusion is valid until pristine verification passes.'},indent=2));return 2
        inv=read(pristine,'catalog-coa-inventory.json')
        b12=next(p for p in inv['products'] if p['slug']=='vitamin-b12')['chemical_reference']
        assert b12['molar_mass_g_mol'] is None and not b12['allowed_molarity'] and len(b12['constituent_references'])==2
        for label,mutate in CASES:
            root=suite/label;shutil.copytree(pristine,root)
            mutate(root)
            try:
                result=verifier.verify(root,online=False)
                caught=bool(result['errors']);errors=result['errors']
            except Exception as exc:caught=True;errors=[type(exc).__name__+': '+str(exc)]
            results.append({'case':label,'rejected':caught,'errors':errors[:8]})
    escaped=[r['case'] for r in results if not r['rejected']]
    report={'status':'PASS' if not escaped else 'FAIL','tests':len(results),'escaped_mutations':escaped,'network':'synthetic local HTTP fixtures only; no network calls','results':results}
    (BASE/'verifier-adversarial-results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return int(bool(escaped))
if __name__=='__main__':raise SystemExit(main())
