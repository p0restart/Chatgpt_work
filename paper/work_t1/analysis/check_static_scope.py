"""Scope hashes and arithmetic evaluation of a proven conservative bound; no solver."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'paper/work_t1'
REPORT=ROOT/'reports/work_t1'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    manifest=OUT/'source_manifest.json'
    if not manifest.exists():
        names=['AGENTS.md','02_MODEL_SPEC.md','DECISIONS.md','reviews/APPROVAL_LOG.md',
               'src/core.py','src/game_solver.py','configs/base.yaml',
               'configs/proposed_mechanism_identification.yaml',
               'reviews/G_D4_P0_1_submission.md']
        paths={ROOT/n for n in names}
        for base in ['paper/work_d1','paper/work_d2','paper/work_d3']:
            for p in (ROOT/base).rglob('*'):
                if p.is_file() and '_qa_packages' not in p.parts and '__pycache__' not in p.parts:
                    paths.add(p)
        for case in (ROOT/'results/matched_mechanism/run01').glob('seed*'):
            for leaf in ['model.json','config.yaml','fine/controls.json','case_audit.json']:
                if (case/leaf).is_file():paths.add(case/leaf)
        manifest.write_text(json.dumps({'scope':'T1 read-only source audit, not experiment preregistration',
            'files':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}},ensure_ascii=False,indent=2),encoding='utf-8')
    protected=json.loads(manifest.read_text(encoding='utf-8'))['files']
    changes=[n for n,d in protected.items() if digest(ROOT/n)!=d]
    rows=[]
    for case in sorted((ROOT/'results/matched_mechanism/run01').glob('seed*')):
        path=case/'model.json'
        if not path.is_file():continue
        m=json.loads(path.read_text(encoding='utf-8'));n=len(m['x0']);T=10.;K=6
        incoming=[sum(m['beta'][j][i] for j in range(n)) for i in range(n)]
        M=max(max(m['alpha'][i]+incoming[i],m['delta'][i]+m['gamma'][i]) for i in range(n))
        L=max(m['alpha'][i]+m['delta'][i]+m['gamma'][i]+2*incoming[i] for i in range(n))
        sb_D=sum(m['epsilon'][j]*max(m['beta'][j]) for j in range(n))+sum(m['gamma'])
        sl_D=2*sum(m['epsilon'][j]*max(m['beta'][j]) for j in range(n))+sum(m['gamma'])
        sb_A=sum(m['alpha'][i] for i in range(n) if m['entry'][i]);sl_A=sb_A
        C_D=math.exp(L*T)*(M*T*sl_D+sb_D);C_A=math.exp(L*T)*(M*T*sl_A+sb_A)
        Q_D=T*sum(m['q'])+sum(m['omega']);Q_A=T*sum(m['g'])+sum(m['nu'])
        delta_D=Q_D*C_D*T/K;delta_A=Q_A*C_A*T/K
        # A trivial uniform objective-width bound is much smaller here.
        JD_upper=T*(sum(m['q'])+sum(m['h'])+.5*(sum(m['c_s'])+sum(m['c_r'])))+sum(m['omega'])
        rows.append(dict(case=case.name,B=m['B'],T=T,K=K,M=M,L=L,
                         state_averaging_constant_D=C_D,state_averaging_constant_A=C_A,
                         conservative_continuous_gap_addition_D=delta_D,
                         conservative_continuous_gap_addition_A=delta_A,
                         trivial_defense_objective_upper_bound=JD_upper,
                         D_discretization_bound_is_vacuous_at_K6=delta_D>JD_upper,
                         model_sha256=digest(path)))
    with (OUT/'discretization_bound_constants.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    example=dict(scope='analytic model-family illustration, not a new experiment or frozen-parameter counterexample',
                 F0=20+20*math.exp(-2),Fhalf=11.25+40/math.e,F1=25.)
    example['quasiconvex_inequality_violated']=example['Fhalf']>max(example['F0'],example['F1'])
    proof=(OUT/'T1_proofs_zh.md').read_text(encoding='utf-8')
    tags=re.findall(r'\\tag\{(T1\.\d+)\}',proof)
    report=dict(status='STATIC_SCOPE_AND_ARITHMETIC_PASS' if not changes else 'SOURCE_CHANGED',
                protected_files=len(protected),protected_changes=changes,model_count=len(rows),
                numbered_equations=len(tags),unique_equation_tags=len(set(tags)),
                complete_equation_sequence=tags==[f'T1.{i}' for i in range(1,27)],
                balanced_display_math=proof.count(r'\[')==proof.count(r'\]'),
                balanced_inline_math=proof.count(r'\(')==proof.count(r'\)'),
                generic_illustration=example,
                bound_ranges={'D_K6':[min(r['conservative_continuous_gap_addition_D'] for r in rows),max(r['conservative_continuous_gap_addition_D'] for r in rows)],
                              'A_K6':[min(r['conservative_continuous_gap_addition_A'] for r in rows),max(r['conservative_continuous_gap_addition_A'] for r in rows)]},
                no_new_optimization_or_ODE_integration=True,
                mathematical_verification='manual derivation only; static checks do not certify proofs')
    (REPORT/'T1_scope_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    assert not changes and example['quasiconvex_inequality_violated'] and report['complete_equation_sequence']

if __name__=='__main__':main()
