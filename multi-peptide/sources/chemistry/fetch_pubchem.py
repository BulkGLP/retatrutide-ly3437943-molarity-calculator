import json, pathlib, urllib.request, urllib.parse, time, concurrent.futures, re
ROOT = pathlib.Path(__file__).resolve().parent
NAMES = ['Tesamorelin','Sermorelin','CJC-1295','GHK-Cu','Thymalin','FOXO4-DRI','Bremelanotide','Epitalon','AICAR','Adamax','Cibinetide','Elamipretide','Thymosin alpha 1','AHK-Cu','Selank','Semax','Vasoactive intestinal peptide','Semaglutide','Tirzepatide','LL-37','Melanotan II','Afamelanotide','Lys-Pro-Val','TB-500','MOTS-c','BPC-157','NAD+','Cyanocobalamin','Methylcobalamin','Retatrutide']
def fetch(name):
    key = re.sub('[^a-z0-9]+','-', name.lower()).strip('-')
    rows=[]
    for endpoint in ['property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON','synonyms/JSON']:
        url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+urllib.parse.quote(name,safe='')+'/'+endpoint
        path=ROOT/(key+('-properties.json' if endpoint.startswith('property') else '-synonyms.json'))
        if path.exists():
            data=json.loads(path.read_text())
        else:
            try:
                with urllib.request.urlopen(url,timeout=50) as r: body=r.read()
                data=json.loads(body)
            except Exception as e: data={'error':str(e)}
            path.write_text(json.dumps({'source_url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response':data},indent=2),encoding='utf-8')
            data={'response':data}
        rows.append(data)
        time.sleep(.35)
    props=rows[0].get('response',{}).get('PropertyTable',{}).get('Properties',[])
    syns=rows[1].get('response',{}).get('InformationList',{}).get('Information',[])
    cas={s.get('CID'):[x for x in s.get('Synonym',[]) if re.fullmatch(r'\d{2,7}-\d{2}-\d',x)] for s in syns}
    return {'query':name,'properties':props,'cas_candidates':cas,'errors':[r.get('response',{}).get('error') for r in rows if r.get('response',{}).get('error')]}
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        rows=list(ex.map(fetch,NAMES))
    (ROOT/'pubchem-index.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps(rows,indent=2))
