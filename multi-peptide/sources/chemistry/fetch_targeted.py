import json,pathlib,urllib.request,time
ROOT=pathlib.Path(__file__).resolve().parent
REQS={
 'vip-amidated-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/16140438/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'vip-amidated-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/16140438/synonyms/JSON',
 'vip-amidated-pubmed':'https://pubmed.ncbi.nlm.nih.gov/2171816/?format=pubmed',
 'foxo4-primary-pubmed':'https://pubmed.ncbi.nlm.nih.gov/28340339/?format=pubmed',
 'tb4-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Thymosin%20beta%204/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'tb4-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Thymosin%20beta%204/synonyms/JSON',
 'tb500-primary-pubmed':'https://pubmed.ncbi.nlm.nih.gov/22962027/?format=pubmed',
 'retatrutide-cas-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/2381089-83-2/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'retatrutide-cas-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/2381089-83-2/synonyms/JSON',
}
for key,url in REQS.items():
    path=ROOT/(key+('.html' if 'pubmed' in key else '.json'))
    try:
        with urllib.request.urlopen(url,timeout=20) as r: body=r.read()
        if path.suffix=='.json':
            path.write_text(json.dumps({'source_url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response':json.loads(body)},indent=2),encoding='utf-8')
        else: path.write_bytes(body)
        print(key,'OK',flush=True)
    except Exception as e: print(key,str(e),flush=True)
    time.sleep(.7)
