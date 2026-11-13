"""Create a local review archive and byte manifest; does not submit or approve."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT=Path(__file__).resolve().parents[4]
REPORT=ROOT/'reports/work_d4'
ARCHIVE=REPORT/'Work_D4_P0_1_review_package.zip'
MANIFEST=REPORT/'P0_01_delivery_manifest.json'
RECEIPT=REPORT/'P0_01_delivery_receipt.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files():
    found=[]
    for base in ['paper/work_d4','results/work_d4','reports/work_d4']:
        for p in (ROOT/base).rglob('*'):
            if p.is_file() and p not in (ARCHIVE,MANIFEST,RECEIPT) and not any(s in p.parts for s in ['__pycache__','mpl_config']):
                found.append(p)
    found.append(ROOT/'reviews/G_D4_P0_1_submission.md')
    return sorted(set(found))

def main():
    validation=json.loads((REPORT/'P0_01_independent_validation.json').read_text(encoding='utf-8'))
    if validation['status']!='PASS':raise RuntimeError('Validation must pass before packaging')
    summary=json.loads((REPORT/'P0_01_summary.json').read_text(encoding='utf-8'))
    if summary['completed_cells']!=36 or summary['passed_cells']!=36:
        raise RuntimeError('This completed-run package expects all preregistered cells to pass')
    broken=[]
    for p in files():
        if p.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8-sig')):
                if re.match(r'^(https?://|#|mailto:)',link):continue
                if not (p.parent/link.split('#')[0]).exists():broken.append(dict(file=str(p.relative_to(ROOT)),link=link))
    if broken:raise RuntimeError('Broken review links: '+repr(broken))
    manifest=dict(date='2026-11-11',status='WAITING_USER_G_D4_P0_1_REVIEW',
                  scope='local review package with full P0-1 raw outputs; no execution of P0-2/P0-3',
                  exclusions='archive itself, manifest itself, receipt, font cache and pycache',
                  files={str(p.relative_to(ROOT)):sha(p) for p in files()})
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files()+[MANIFEST]:z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(ARCHIVE) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('Archive integrity error: '+bad)
    receipt=dict(archive=str(ARCHIVE.relative_to(ROOT)),bytes=ARCHIVE.stat().st_size,sha256=sha(ARCHIVE),
                 files=len(files())+1,links_checked=True,status='WAITING_USER_G_D4_P0_1_REVIEW')
    RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
