"""Build the reviewed reference registry from captured primary database records.

This models reference species; it never authenticates a commercial lot or treats
nominal powder fill / HPLC area purity as net parent-peptide mass.
"""
import json,pathlib,re,datetime,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC=ROOT/'sources'/'chemistry'
def load(stem): return json.loads((SRC/(stem+'.json')).read_text(encoding='utf-8'))
def props(stem): return load(stem)['response']['PropertyTable']['Properties']
def source(stem): return load(stem)['source_url']
def candidate(stem,cid=None,cas=None,label=None):
    p=next((x for x in props(stem) if cid is None or x['CID']==cid))
    row={'name':label or p['Title'],'pubchem_cid':p['CID'],'cas':cas,'formula':p['MolecularFormula'],
      'molar_mass_g_mol':float(p['MolecularWeight']),'source_reported_molecular_weight':p['MolecularWeight'],
      'monoisotopic_mass_da':float(p['MonoisotopicMass']),'database_exact_mass_da':float(p['ExactMass']),
      'source_urls':['https://pubchem.ncbi.nlm.nih.gov/compound/'+str(p['CID']),source(stem)],
      'source_files':['sources/chemistry/'+stem+'.json'],
      'convention':'PubChem reported MolecularWeight: rounded approximate average molar mass, g/mol. MonoisotopicMass and ExactMass are separate fields and are not used for molarity.'}
    synstem=stem.replace('-properties','-synonyms')
    if (SRC/(synstem+'.json')).exists():
        row['source_urls'].append(source(synstem)); row['source_files'].append('sources/chemistry/'+synstem+'.json')
    return row
REF=[]
def add(id,name,slugs,stem,cas,cid=None,notes=None,extra=None,is_peptide=True,allowed=True):
    c=candidate(stem,cid,cas,name)
    row={'id':id,'name':name,'slugs':slugs,'identity_status':'reference_species_supported_catalog_name_mapped',
      'is_peptide':is_peptide,'compound_class':'peptide' if is_peptide else 'non_peptide_support',
      'allowed_molarity':allowed,'allowed_molarity_reason':
      'Permitted only for a theoretical reference-species matrix assuming net anhydrous parent-peptide mass and final solution volume; no claim of lot composition or measured concentration.' if allowed else 'Non-peptide support material is outside the peptide molarity matrix.',
      'notes':notes or [],'candidate_references':[],**c}
    synstem=stem.replace('-properties','-synonyms')
    if (SRC/(synstem+'.json')).exists():
        row['source_urls'].append(source(synstem)); row['source_files'].append('sources/chemistry/'+synstem+'.json')
    for slug in slugs: row['source_files'].append('sources/catalog/'+slug+'.extracted.json')
    if extra: row.update(extra)
    REF.append(row); return row
def unresolved(id,name,slugs,reason,cands=None,peptide=True,extra=None):
    row={'id':id,'name':name,'slugs':slugs,'cas':None,'formula':None,'molar_mass_g_mol':None,
      'source_reported_molecular_weight':None,'pubchem_cid':None,'monoisotopic_mass_da':None,
      'database_exact_mass_da':None,'identity_status':'unresolved_catalog_species',
      'is_peptide':peptide,'compound_class':'peptide_identity_unresolved' if peptide else 'blend_or_support',
      'allowed_molarity':False,'allowed_molarity_reason':reason,'convention':'No assigned molecular species or single molar mass.',
      'notes':[reason],'candidate_references':cands or [],'source_urls':[],
      'source_files':['sources/catalog/'+s+'.extracted.json' for s in slugs]}
    for c in row['candidate_references']:
        row['source_urls'].extend(c['source_urls']); row['source_files'].extend(c['source_files'])
    if extra: row.update(extra)
    REF.append(row); return row

add('tesamorelin','Tesamorelin',['tesamorelin'],'tesamorelin-properties','218949-48-5',notes=['Reference is the modified 44-residue parent; counterions, hydrate water and excipients are excluded.'])
add('sermorelin','Sermorelin',['sermorelin'],'sermorelin-properties','86168-78-7',notes=['Reference is GHRH(1-29) amide; not an acetate-salt formula.'])
add('cjc1295_dac','CJC-1295 with DAC',['cjc-1295-with-dac-10mg'],'cjc-1295-properties','446262-90-4',notes=['The DAC conjugation moiety is included; this is not modified GRF(1-29), commonly marketed as CJC-1295 without DAC.'])
ghk=[]
for p in props('ghk-cu-properties'):
    if 'Cu' in p['MolecularFormula']:
        ghk.append(candidate('ghk-cu-properties',p['CID'],label=p['Title']))
unresolved('ghk_cu','GHK-Cu',['ghk-cu','ghk-cu-10000mg'],
 'Catalog names the copper(II) complex but does not establish ligand:copper stoichiometry, protonation, counterions or hydration. PubChem name resolution returns multiple copper complexes with different masses. No single GHK-Cu mass is assigned.',ghk)
unresolved('thymalin','Thymalin',['thymalin-10mg'],
 'Thymalin is described in primary literature as a natural thymic peptide preparation. PubChem name lookup resolves to nonathymulin (thymulin peptide moiety), which does not establish identity of this catalog product. Require exact sequence or mixture characterization.',
 [candidate('thymalin-properties',cas='63958-90-7',label='Nonathymulin (name-search candidate; not assigned to Thymalin)')],
 extra={'source_urls':['https://pubmed.ncbi.nlm.nih.gov/9637345/','https://pubchem.ncbi.nlm.nih.gov/compound/3085284'],
 'source_files':['sources/catalog/thymalin-10mg.extracted.json','sources/chemistry/thymalin-properties.json','sources/chemistry/thymalin-synonyms.json','sources/chemistry/thymalin-pubmed.html','sources/chemistry/primary-web-evidence.json']})
unresolved('foxo4','FOXO4 catalog material',['foxo4-10mg'],
 'FOXO4 denotes a protein/gene-associated target and does not identify the supplied peptide sequence, stereochemistry, termini or cell-penetrating conjugate. FOXO4-DRI is a candidate only; catalog identity is not established.',
 [candidate('foxo4-dri-properties',167312269,'2460055-10-9','FOXO4-DRI (candidate only)')],
 extra={'source_urls':['https://pubchem.ncbi.nlm.nih.gov/compound/167312269','https://pubmed.ncbi.nlm.nih.gov/28340339/'],
 'source_files':['sources/catalog/foxo4-10mg.extracted.json','sources/chemistry/foxo4-dri-properties.json','sources/chemistry/foxo4-dri-synonyms.json','sources/chemistry/foxo4-primary-pubmed.html','sources/chemistry/primary-web-evidence.json']})
add('bremelanotide','PT-141 / Bremelanotide',['pt-141'],'bremelanotide-properties','189691-06-3',notes=['Cyclic parent heptapeptide; not bremelanotide acetate or Melanotan II.'])
add('epitalon','Epitalon',['epitalon-50mg'],'epitalon-properties','307297-39-8',notes=['Reference sequence H-Ala-Glu-Asp-Gly-OH (AEDG); PubChem also lists CAS 64082-79-7.'])
add('acadesine','AICAR / Acadesine nucleoside',['aicar'],'acadesine-properties','2627-69-2',is_peptide=False,allowed=False,
 notes=['Catalog describes a nucleoside analogue, so the acadesine/AICA-riboside reference is shown. The abbreviation AICAR also names the phosphorylated ribonucleotide ZMP (PubChem CID65110, C9H15N4O8P, 338.21 g/mol). Identity is conditional on the catalog nucleoside description; obtain a specific CAS/structure for the supplied lot.'],
 extra={'identity_status':'reference_nucleoside_mapped_with_acronym_ambiguity','candidate_references':[candidate('aicar-properties',cas='3031-94-5',label='AICAR ribonucleotide / ZMP (not assigned)')]})
unresolved('adamax','Adamax',['adamax'],
 'Catalog describes an N-acetylated Semax analogue with a C-terminal adamantane modification, but provides no exact sequence, linker, attachment chemistry or verified registry identifier. PubChem name lookup returned no record. No mass inferred from Semax.',
 extra={'source_files':['sources/catalog/adamax.extracted.json','sources/chemistry/adamax-properties.json','sources/chemistry/adamax-synonyms.json']})
add('cibinetide','ARA-290 / Cibinetide',['ara-290'],'cibinetide-properties','1208243-50-8',notes=['Reference molecule only. The catalog reports a sample purity of 53.90% for the linked lot; HPLC area purity does not supply a valid net-peptide mass correction.'])
add('elamipretide','SS-31 / Elamipretide',['ss-31-1000mg'],'elamipretide-properties','736992-21-5',notes=['Modified tetrapeptide parent; counterions excluded.'])
add('thymosin_alpha1','Thymosin alpha-1 / Thymalfasin',['ta-1-10mg','thymosin-ta-1-1000mg'],'thymosin-alpha-1-properties','62304-98-7',notes=['N-acetylated 28-residue peptide parent. PubChem includes other CAS aliases; the stated identifier is not a claim about supplied salt form.'])
ahk=[candidate('ahk-cu-properties',label='AHK-Cu hydrochloride name-search candidate')]
ahk += [candidate('ahk-cu-alternative-properties',p['CID'],label=p['Title']) for p in props('ahk-cu-alternative-properties')]
unresolved('ahk_cu','AHK-Cu',['ahk-cu-10000mg'],
 'Catalog identifies Ala-His-Lys copper complex but does not resolve protonation, counterions, ligand:copper ratio or hydration. PubChem name lookup resolves to a hydrochloride species; other deposited AHK-Cu structures have different formulas. No single mass assigned.',ahk)
add('selank','Selank',['selank','selank-1000mg'],'selank-properties','129954-34-3',notes=['Reference H-Thr-Lys-Pro-Arg-Pro-Gly-Pro-OH; counterions excluded.'])
add('semax','Semax',['semax','semax-1000mg'],'semax-properties','80714-61-0',notes=['Reference MEHFPGP heptapeptide; not an N-acetylated derivative.'])
add('vip','VIP (human/porcine, C-terminal amide)',['vip','vip-1000mg'],'vip-amidated-properties','37221-79-7',
 notes=['Explicit reference model: H-HSDAVFTDNYTRLRKQMAVKKYLNSILN-NH2. The catalog identifies 28-residue VIP but does not independently confirm terminal chemistry. The numerical matrix assumes this native amidated reference; verify termini on the lot specification before use.',
 'PubChem name lookup Aviptadil CID16132300 instead represents the free-acid form C147H237N43O43S, 3326.8 g/mol. That value is not used for the amidated VIP reference.',
 'CAS37221-79-7 is the VIP identifier in the cited PubMed substance record; it does not prove the exact commercial salt or preparation.'],
 extra={'identity_status':'reference_native_amidated_species_catalog_terminals_unverified','candidate_references':[candidate('vip-aviptadil-properties',cas='40077-57-4',label='VIP/aviptadil free-acid database record (not used)')]})
REF[-1]['source_urls'].append('https://pubmed.ncbi.nlm.nih.gov/2171816/'); REF[-1]['source_files'].append('sources/chemistry/vip-amidated-pubmed.html')
add('semaglutide','Semaglutide',['semaglutide','glp1s-1000mg'],'semaglutide-properties','910463-68-2',notes=['Includes lipid side-chain modification; anhydrous parent reference rather than sodium/acetate salt.'])
add('tirzepatide','Tirzepatide',['tirzepatide','glp2t-1000mg'],'tirzepatide-properties','2023788-19-2',166567236,notes=['Includes lipid side-chain modification. PubChem name lookup returns several deposited stereochemical representations with the same formula and reported average mass; CAS and catalog LY3298176 mapping are used.'])
add('ll37','LL-37',['ll-37'],'ll-37-properties','154947-66-7',notes=['Human 37-residue cathelicidin-derived parent reference; no salt or hydration mass added.'])
add('melanotan_ii','Melanotan II',['melanotan-2'],'melanotan-ii-properties','121062-08-6',notes=['Cyclic melanocortin analogue distinct from PT-141/bremelanotide.'])
add('afamelanotide','Melanotan I / Afamelanotide',['melanotan-1-mt-1'],'afamelanotide-properties','75921-69-6',notes=['Acetylated 13-residue alpha-MSH analogue parent reference.'])
add('kpv','KPV (Lys-Pro-Val free acid)',['kpv'],'lys-pro-val-properties','67727-97-3',notes=['Explicit reference is H-Lys-Pro-Val-OH. Catalog shorthand does not authenticate lot termini or salt form; an amidated KPV derivative would require a different formula.'])
unresolved('tb500','TB-500 catalog material',['tb-500'],
 'The live catalog explicitly states that TB-500 does not define a unique sequence. Do not substitute the seven-residue N-acetyl fragment mass or full-length thymosin beta-4 mass without an exact lot sequence/specification.',
 [candidate('tb-500-properties',cas='885340-08-9',label='Ac-LKKTETQ-OH / TB-500 fragment (candidate only)'),candidate('tb4-properties',label='Full-length thymosin beta-4 (candidate only)')])
add('mots_c','MOTS-c',['mots-c-10mg-20mg'],'mots-c-properties','1627580-64-6',notes=['16-residue parent reference. Mannitol listed in the catalog is excluded; nominal vial fill must not be treated as verified net peptide mass.'])
add('nad_plus','NAD+ / Nadide reference',['nad-plus'],'nad-cid-properties','53-84-9',is_peptide=False,allowed=False,notes=['Non-peptide coenzyme. Formula is the PubChem CID5892 reference, not a verified commercial counterion/hydrate. Mannitol is listed in the catalog.'])
add('bpc157','BPC-157',['bpc-157-peptide-research-vials'],'bpc-157-properties','137525-51-0',notes=['15-residue parent peptide reference; no acetate or other counterion mass included.'])
add('retatrutide','Retatrutide / LY3437943',['retatrutide','retatrutide-powder'],'retatrutide-cid-properties','2381089-83-2',
 notes=['PubChem name lookup Retatrutide returned no compound record; IUPHAR-deposited PubChem SID507750402 maps retatrutide/LY3437943 to CID171390338, titled Triple G. The linkage is saved.',
 'This edition uses the verified PubChem rounded average molar mass 4731 g/mol. The previous 4731.33 g/mol convention is not silently carried forward; its additional decimal precision is not supplied by this PubChem property record.',
 'The difference from 4731.33 g/mol is approximately 0.00698%; theoretical concentrations using 4731 are approximately 0.00698% higher for the same parent mass and volume.',
 'PubChem ExactMass 4730.4784689 Da and MonoisotopicMass 4728.4717592 Da are separate database values; neither is used as average molar mass.',
 'Mannitol Free does not prove salt-free, anhydrous, excipient-free or net parent-peptide mass. Reference formula includes the covalent lipid modification.'])
REF[-1]['source_urls']+=['https://pubchem.ncbi.nlm.nih.gov/substance/507750402','https://go.drugbank.com/drugs/DB18993']
REF[-1]['source_files']+=['sources/chemistry/retatrutide-substance.json','sources/chemistry/primary-web-evidence.json']
add('cyanocobalamin','Cyanocobalamin (Vitamin B12 option)',['vitamin-b12'],'b12-cas-properties','68-19-9',is_peptide=False,allowed=False,notes=['Cyanocobalamin-specific reference; does not represent methylcobalamin or all Vitamin B12 formulations.'])
add('methylcobalamin','Methylcobalamin (Vitamin B12 option)',['vitamin-b12'],'methylcobalamin-properties','13422-55-4',10898559,is_peptide=False,allowed=False,notes=['Methylcobalamin-specific reference; product form must be selected explicitly.'])
frag=candidate('tb-500-properties',cas='885340-08-9',label='Ac-LKKTETQ-OH fragment explicitly named in blend catalog')
for id,name,slug,reason in [
 ('glow','GLOW blend','glow-blend','Mixture of GHK-Cu, BPC-157 and an explicitly named Ac-LKKTETQ TB-500 fragment; no single molecular formula or molar mass exists.'),
 ('klow','KLOW blend','klow-peptide','Mixture of GHK-Cu, BPC-157, KPV and an explicitly named Ac-LKKTETQ TB-500 fragment; no single molecular formula or molar mass exists.'),
 ('wolverine','Wolverine blend','bpc-157-tb-500-blend','Mixture of BPC-157 and TB-500; catalog does not establish exact TB-500 sequence, component amounts or ratio. No single molecular mass.'),
 ('lipotropic_b','Lipotropic B','lipotropic-b','Multi-component liquid formulation with B12 options; no single molecular formula or molar mass.'),
 ('lipotropic_c','Lipotropic C','lipotropic-c','Multi-component liquid formulation with B12/NADH options; no single molecular formula or molar mass.'),
 ('shb','SHB Super Human Blend','shb','Mixture of amino acids, L-carnitine and NAC; no single molecular formula or molar mass.'),
 ('reconstitution_solution','Reconstitution solution','reconstitution-solution','Bacteriostatic water formulation labeled 0.9% benzyl alcohol; support solution, not a single peptide species.')]:
    unresolved(id,name,[slug],reason,[frag] if id in ('glow','klow') else [],peptide=id in ('glow','klow','wolverine'),extra={'identity_status':'multi_component_formulation_no_single_molar_mass','compound_class':'peptide_blend' if id in ('glow','klow','wolverine') else 'blend_or_support'})

byid={r['id']:r for r in REF}
byid['thymalin']['notes'].append('Additional catalog/COA conflict: supplier-hosted report Bulk2608100933 labels the product Thymalin 10mg but reports Identity (LC-MS) Thymulin. This supports a naming conflict, not a verified sequence or zinc/counterion stoichiometry. Keep mass unassigned.')
byid['thymalin']['source_files']+=['sources/coa/Bulk2608100933.pdf','sources/coa/Bulk2608100933.pdf.txt','sources/chemistry/primary-literature-search-evidence.json']
byid['vip']['source_files'].append('sources/chemistry/primary-literature-search-evidence.json')
byid['tb500']['notes'].append('Supplier-hosted report Bulk2605280346 labels Identity (LC-MS) Thymosin Beta-4, but does not state the exact sequence or unambiguous parent/salt species. The label alone is not a sequence assignment.')
byid['tb500']['source_files']+=['sources/coa/Bulk2605280346.pdf','sources/coa/Bulk2605280346.pdf.txt']
for rid,coa in [('glow','Bulk2608100934'),('klow','Bulk2604170178')]:
    byid[rid]['notes'].append('Unresolved identity conflict: live catalog describes TB-500 as Ac-LKKTETQ fragment; supplier-hosted COA '+coa+' labels the component Thymosin Beta-4. Candidate fragment metadata is catalog-derived and must not override this disagreement. No component molarity assigned.')
    byid[rid]['source_files']+=['sources/coa/'+coa+'.pdf','sources/coa/'+coa+'.pdf.txt']
byid['glow']['notes'].append('Supplier-hosted COA Bulk2608100934 says Product GLOW 50mg, whereas the live catalog states nominal 70mg total (50mg GHK-Cu + 10mg BPC-157 + 10mg TB-500). Preserve both claims separately.')

for r in REF:
    r['source_urls']=list(dict.fromkeys(r['source_urls']))
    r['source_files']=list(dict.fromkeys(r['source_files']))
    if r['cas'] and r['id'] not in ['retatrutide','vip','nad_plus']:
        hay=' '.join((ROOT/p).read_text(encoding='utf-8') for p in r['source_files'] if p.endswith('-synonyms.json'))
        assert r['cas'] in hay, (r['id'],'CAS not in saved synonym evidence')
    for f in r['source_files']: assert (ROOT/f).exists(),f
out={'schema_version':1,'edition':'2026.10.R3','compiled_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'mass_convention':'Use the source-reported approximate average molar mass of the explicitly specified anhydrous parent reference species (g/mol), retaining source rounding. Not monoisotopic mass, ExactMass, ion m/z, salt/hydrate mass, total powder fill, or HPLC-area-adjusted mass.',
 'allowed_molarity_semantics':'True permits a theoretical reference-species calculation only. It does not establish a real lot concentration, chemical identity, net peptide content, quantitative assay, suitable solvent, stability, or use in humans/animals.',
 'references':REF}
(ROOT/'inputs').mkdir(exist_ok=True)
(ROOT/'inputs'/'chemical-references.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'references':len(REF),'distinct_product_slugs':len(set(s for r in REF for s in r['slugs'])),'molarity_reference_count':sum(r['allowed_molarity'] for r in REF),'unresolved':[r['id'] for r in REF if r['identity_status']=='unresolved_catalog_species']},indent=2))
