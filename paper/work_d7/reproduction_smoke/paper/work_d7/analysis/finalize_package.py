"""Snapshot actual sources and create a self-contained review archive."""
from pathlib import Path
import sys,json,hashlib,shutil,platform,zipfile,importlib.metadata
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'paper/work_d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[*sorted((ROOT/'src').glob('*.py')),ROOT/'02_MODEL_SPEC.md',ROOT/'paper/work_d5/analysis/run_replanning.py',*sorted((BASE/'analysis').rglob('*.py'))]
snapshot=BASE/'source_snapshot';snapshot.mkdir(exist_ok=True)
manifest={}
for p in paths:
    dest=snapshot/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    manifest[str(p.relative_to(ROOT)).replace('\\','/')]=dict(sha256=sha(p),bytes=p.stat().st_size)
(BASE/'sources/runtime_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for p in [ROOT/'DECISIONS.md',ROOT/'reviews/APPROVAL_LOG.md']:
    d=BASE/'sources'/('current_'+p.name);shutil.copyfile(p,d)
env=dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),packages={k:importlib.metadata.version(k) for k in ['numpy','scipy','pandas','PyYAML','matplotlib','tabulate']})
(BASE/'sources/environment_final.json').write_text(json.dumps(env,indent=2),encoding='utf-8')
if '--snapshot-only' in sys.argv:print('Actual source snapshot saved.');sys.exit(0)
report=ROOT/'reports/work_d7';report.mkdir(exist_ok=True)
archive=report/'D7_review_package.zip'
excluded={'__pycache__','reproduction_smoke'}
files=[p for p in BASE.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(BASE).parts) and not (p.parent==BASE/'sources/papers' and p.suffix=='.txt') and p.name!='Hu2023_extracted.txt']
# Include actual source roots so standard ROOT-relative commands work after extraction.
files+=list((ROOT/'src').glob('*.py'))+[ROOT/'02_MODEL_SPEC.md',ROOT/'paper/work_d5/analysis/run_replanning.py']
contents={str(p.relative_to(ROOT)).replace('\\','/'):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files if p.name!='package_manifest.json'}
(BASE/'package_manifest.json').write_text(json.dumps(contents,indent=2),encoding='utf-8');files=[p for p in files if p.name!='package_manifest.json']+[BASE/'package_manifest.json']
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,info in contents.items():assert hashlib.sha256(z.read(rel)).hexdigest()==info['sha256'],rel
(report/'archive_verification.json').write_text(json.dumps(dict(passed=True,files=len(files),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size),indent=2),encoding='utf-8')
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=archive.stat().st_size)))
