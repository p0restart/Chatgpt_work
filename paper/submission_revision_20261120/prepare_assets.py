from pathlib import Path
import shutil,json,csv,hashlib
R=Path(__file__).resolve().parent
ROOT=R.parents[1]
out=R/'latex'
out.mkdir(exist_ok=True)
for n in ['main.tex','IEEEtran.cls']:shutil.copyfile(R/'original_latex'/n,out/n)
data=out/'data';data.mkdir(exist_ok=True)
for b in [.6,1.2,1.8]:
 for n in ['G_controls.json','model.json']:
  shutil.copyfile(ROOT/f'paper/work_d7/results/static/B{b}'/n,data/f'B{b}_{n}')
for name in ['fig4_states.csv','fig4_controls.csv','fig2_capacity.csv','verification.json']:
 shutil.copyfile(ROOT/'paper/figure_2_4_20261118'/name,data/name)
source=ROOT/'paper/work_d7/results/static'
rows=list(csv.DictReader((source/'solver_audit.csv').open()))
rows=[row for row in rows if row['method']=='G' and row['evaluation']=='offline']
with (data/'numerical_diagnostics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
record={}
for b in [.6,1.2,1.8]:
 folder=source/f'B{b}/G';decision=json.loads((folder/'decision.json').read_text())
 warm=json.loads((folder/'warm/last.json').read_text())
 record[str(b)]={'decision':decision,'uniform_start':{k:warm[k] for k in ['iteration','relative_D','relative_A','incumbent_residual','response_distance','passed']}}
(data/'diagnostics_summary.json').write_text(json.dumps(record,indent=2))
shutil.copyfile(source/'environment_static_1.2.json',data/'experiment_environment.json')
audit_dir=ROOT/'reports/conference_word_audit_20261120'
shutil.copyfile(audit_dir/'input/A Finite-Resource Network Defense Decision Method Based on a Nonzero-Sum Differential Game.docx',R/'word_original.docx')
print('Prepared frozen data and original manuscript copies')
