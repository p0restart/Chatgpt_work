"""Build a checked delivery ZIP; omit temporary render pages and third-party full text."""
from pathlib import Path
import zipfile,hashlib,json
BASE=Path(__file__).resolve().parent
OUT=BASE.parents[1]/'reports/final_20261115';OUT.mkdir(parents=True,exist_ok=True)
def included(p):
    rel=p.relative_to(BASE)
    if any(part in ['__pycache__','intake'] for part in rel.parts):return False
    if rel.parts[0]=='document_qa' and p.suffix.lower() in ['.png','.txt']:return False
    if rel.parts[0]=='vendor' and any(part.endswith('.dist-info') for part in rel.parts):return False
    if rel.as_posix().startswith('raw_d7/sources/papers/') and p.suffix=='.txt':return False
    if rel.as_posix()=='raw_d7/sources/Hu2023_extracted.txt':return False
    return p.name!='package_manifest.json'
files=sorted(p for p in BASE.rglob('*') if p.is_file() and included(p))
manifest={p.relative_to(BASE).as_posix():dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in files}
(BASE/'package_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
files.append(BASE/'package_manifest.json')
archive=OUT/'论文终稿与复现审计包_20261115.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,'final_20261115/'+p.relative_to(BASE).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,meta in manifest.items():assert hashlib.sha256(z.read('final_20261115/'+name)).hexdigest()==meta['sha256']
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
(OUT/'SHA256SUMS.txt').write_text(sha+'  '+archive.name+'\n',encoding='utf-8')
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=archive.stat().st_size,sha256=sha),ensure_ascii=False,indent=2))
