import json,pathlib,urllib.request,urllib.parse,time
ROOT=pathlib.Path(__file__).resolve().parent
REQS = {
 'retatrutide-cid-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/171390338/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'retatrutide-cid-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/171390338/synonyms/JSON',
 'retatrutide-substance':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/507750402/JSON',
 'retatrutide-iuphar':'https://www.guidetopharmacology.org/GRAC/LigandDisplayForward?ligandId=13769',
 'vip-aviptadil-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aviptadil/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'vip-aviptadil-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aviptadil/synonyms/JSON',
 'acadesine-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/acadesine/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'acadesine-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/acadesine/synonyms/JSON',
 'nad-cid-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5892/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'b12-cas-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/68-19-9/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'b12-cas-synonyms':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/68-19-9/synonyms/JSON',
 'ahk-cu-alternative-properties':'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/176418766,178189140/property/MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,Title/JSON',
 'thymalin-pubmed':'https://pubmed.ncbi.nlm.nih.gov/9637345/?format=pubmed',
 'tb500-primary':'https://backoffice.biblio.ugent.be/download/3128392/3128706',
}
for key,url in REQS.items():
    path=ROOT/(key+('.pdf' if key=='tb500-primary' else '.html' if key in ['retatrutide-iuphar','thymalin-pubmed'] else '.json'))
    if path.exists(): continue
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=45) as r: body=r.read()
            if path.suffix=='.json':
                data={'source_url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response':json.loads(body)}
                path.write_text(json.dumps(data,indent=2),encoding='utf-8')
            else: path.write_bytes(body)
            print(key, 'OK',len(body)); break
        except Exception as e:
            print(key, str(e)); time.sleep(2)
    time.sleep(1)
