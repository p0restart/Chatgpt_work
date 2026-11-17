"""Prepare an isolated workspace; --run executes all preregistered stages."""
from pathlib import Path
import argparse,shutil,subprocess,sys
BASE=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('target',type=Path);ap.add_argument('--run',action='store_true');args=ap.parse_args()
target=args.target.resolve()
if target.exists():raise SystemExit('Target must not exist; original data will never be overwritten.')
shutil.copytree(BASE/'source_snapshot',target)
d7=target/'paper/work_d7';d7.mkdir(parents=True,exist_ok=True)
shutil.copytree(BASE/'analysis',d7/'analysis',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for p in BASE.glob('*'):
    if p.is_file() and p.suffix in ['.md','.yaml','.csv','.bib','.json']:shutil.copyfile(p,d7/p.name)
(d7/'sources').mkdir(exist_ok=True);shutil.copyfile(BASE/'sources/source_manifest.json',d7/'sources/source_manifest.json')
(d7/'results').mkdir(exist_ok=True)
print(f'Prepared isolated workspace: {target}',flush=True)
if args.run:
    commands=[['run_d7.py','preflight'],['run_d7.py','static','--budget','1.2'],['run_d7.py','cross','--budget','1.2'],['run_remaining.py'],['verify_d7.py'],['summarize_results.py'],['make_figures.py'],['assemble_paper.py']]
    for command in commands:
        subprocess.run([sys.executable,str(d7/'analysis'/command[0]),*command[1:]],cwd=target,check=True)
    print('Full isolated numerical reproduction completed. Compare values with original; wall times may differ.')
