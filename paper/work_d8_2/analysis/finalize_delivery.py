"""Read-only verification mode and explicit final packaging; never invokes solvers."""
from pathlib import Path
import sys,json,argparse,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from paper.work_d8_2.analysis.run_d8_2 import BASE,sha,now,manifest,write_json,load_controls
REQUIRED=['D8_2_experiment_preregistration.md','source_and_config_manifest.json','code_change_audit.md',
    'K12_G_controls.json','K12_F_controls.json','K12_G_decisions.csv','K12_F_decisions.csv',
    'K12_cross_evaluation.csv','K12_numerical_quality.csv','K12_vs_K6_control_comparison.csv','K12_vs_K6_objective_comparison.csv',
    'R_LAG_E0_controls.csv','R_LAG_E1_controls.csv','R_LAG_E0_objectives.csv','R_LAG_E1_objectives.csv',
    'R_LAG_prediction_errors.csv','R_LAG_numerical_quality.csv','D8_2_experiment_report.md','D8_2_claim_evidence_map.md',
    'D8_2_remaining_issues.md','D8_2_numerical_audit.md','README_REPRODUCE.md']

def verify():
    for rel in REQUIRED:assert (BASE/rel).is_file() and (BASE/rel).stat().st_size>0,rel
    for g in range(5):assert json.loads((BASE/f'checkpoints/gate{g}.json').read_text())['passed']
    assert json.loads((BASE/'results/verification.json').read_text())['status']=='PASS'
    for rel in ('K12_numerical_quality.csv','R_LAG_numerical_quality.csv'):
        frame=pd.read_csv(BASE/rel);assert frame.passed.all()
    for method in ('G','F'):
        u=load_controls(BASE/f'K12_{method}_controls.json');assert all(a.shape==(12,6) for a in u)
        assert len(pd.read_csv(BASE/f'K12_{method}_decisions.csv'))==72
    cross=pd.read_csv(BASE/'K12_cross_evaluation.csv');assert len(cross)==18 and len(cross[cross.H==24])==6
    for e in ('E0','E1'):
        assert len(pd.read_csv(BASE/f'R_LAG_{e}_controls.csv'))==36
        assert len(pd.read_csv(BASE/f'R_LAG_{e}_objectives.csv'))==9
    qa=json.loads((BASE/'figures/qa/attempt03/summary.json').read_text());assert len(qa)==11
    for row in qa:
        assert row['exit_code']==0,row
        if 'figure' in row:assert sha(BASE/f"figures/{row['figure']}.pdf")==row['pdf_sha256']
    for p in (BASE/'figures').glob('fig*.alignment.json'):
        a=json.loads(p.read_text());assert a['verdict'] in ('PASS','NOT APPLICABLE')
    # Bind all immutable original data and code again at final delivery.
    source=json.loads((BASE/'source_and_config_manifest.json').read_text())
    for rel,row in source['sources'].items():
        data=(ROOT/rel).read_bytes()
        if rel in ('DECISIONS.md','reviews/APPROVAL_LOG.md'):data=data[:row['bytes']]
        assert hashlib.sha256(data).hexdigest()==row['sha256'],rel
    return dict(required_files=len(REQUIRED),cross_rows=len(cross),registered_sources=len(source['sources']),
        numerical_diagnostics_passed=True,figure_checks=11,figure_visual_review=(BASE/'figures/qa/visual_review.md').is_file(),
        paper_v3_unchanged=True,core_unchanged=True,status='WAITING_USER_D8_2_REVIEW')

def verify_hashes():
    count=0
    for line in (BASE/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,rel=line.split('  ',1);assert sha(BASE/rel)==expected,rel;count+=1
    return count

def finalize():
    result=verify()
    # Freeze an inventory of the retained output of each completed gate.
    # These inventories are finalized now; gate JSON retains actual completion time.
    patterns={0:['source_and_config_manifest.json','D8_2_experiment_preregistration.md'],
        1:['checkpoints/gate1*'],2:['results/K12/**/*','K12*controls.json','K12*decisions.csv','K12_cross_evaluation.csv'],
        3:['K12_vs_K6*.csv','results/K12/*comparison*','results/K12/*changes.csv','results/K12/asset*.csv'],
        4:['R_LAG*.csv','results/R_LAG/**/*'],5:['D8_2*.md','figures/fig*','figures/qa/attempt03/*']}
    for g,pats in patterns.items():
        paths=set()
        for pat in pats:
            paths.update(p for p in BASE.glob(pat) if p.is_file() and '__pycache__' not in p.parts)
        write_json(BASE/f'checkpoints/gate{g}_retained_inventory.json',dict(inventory_finalized_at=now(),gate=g,
            note='Final hashes of retained gate outputs; original completion timestamp is in gate JSON, not this inventory',
            files=[dict(path=p.relative_to(BASE).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)]))
    write_json(BASE/'checkpoints/gate5.json',dict(gate=5,completed_at=now(),passed=True,scope='Delivery and numerical/figure audits; not user approval'))
    write_json(BASE/'checkpoints/finalize.json',dict(completed_at=now(),**result))
    manifest();result['hashes_verified']=verify_hashes()
    out=ROOT/'reports/work_d8_2/D8_2_review_package.zip';out.parent.mkdir(parents=True,exist_ok=True)
    assert not out.exists(),'Do not overwrite review package'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BASE.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.part':z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for line in (BASE/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest,rel=line.split('  ',1);assert hashlib.sha256(z.read(f'paper/work_d8_2/{rel}')).hexdigest()==digest
    write_json(out.with_suffix('.verification.json'),dict(at=now(),sha256=sha(out),bytes=out.stat().st_size,**result))
    print(json.dumps(dict(package=str(out),**result)),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if a.verify_only:print(json.dumps(dict(**verify(),hashes_verified=verify_hashes())),flush=True)
    else:finalize()
if __name__=='__main__':main()
