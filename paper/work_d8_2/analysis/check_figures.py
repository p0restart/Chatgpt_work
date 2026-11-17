"""Run final rendered figure audits, preserving each actual tool result."""
from pathlib import Path
import sys,json,subprocess,os
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from paper.work_d8_2.analysis.run_d8_2 import BASE,sha
SKILL=ROOT/'paper/work_d8_2/sources/figure_qa_tools'
OUT=BASE/'figures/qa/attempt03';OUT.mkdir(parents=True,exist_ok=True)
def run(script,args,target):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'.figure-deps')
    p=subprocess.run([sys.executable,str(SKILL/script),*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
    target.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    return dict(script=script,exit_code=p.returncode,log=str(target.relative_to(BASE)))
rows=[]
rows.append(run('validate_figure.py',[BASE/'analysis/plot_d8_2.py','--json'],OUT/'source_validation.json'))
for pdf in sorted((BASE/'figures').glob('fig*.pdf')):
    rows.append(dict(figure=pdf.stem,pdf_sha256=sha(pdf),**run('audit_pdf_text.py',[pdf,'--min-pt','5','--json'],OUT/f'{pdf.stem}.text.json')))
    rows.append(dict(figure=pdf.stem,pdf_sha256=sha(pdf),**run('audit_figure_collisions.py',[pdf,'--json-out',OUT/f'{pdf.stem}.collisions.json','--overlay-pdf',OUT/f'{pdf.stem}.overlay.pdf'],OUT/f'{pdf.stem}.collisions.log')))
(OUT/'summary.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows),flush=True)
assert all(r['exit_code']==0 for r in rows)
