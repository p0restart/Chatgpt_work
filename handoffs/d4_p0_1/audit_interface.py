"""Read-only audit of the 36 C1 inputs for the D4-P0-1 fixed-attack control."""
from pathlib import Path
from dataclasses import asdict
import hashlib
import json
import platform
import sys

import numpy as np
import scipy
import yaml

from src.matched_mechanism import matched_model
from src.supplement_c2 import load_model, load_controls
from src.core import check_controls

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/work_d4_p0_1'
CELLS = {'A':('equal','high_at_node2'), 'B':('equal','high_at_node3'),
         'C':('unequal','high_at_node2'), 'D':('unequal','high_at_node3')}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    design = yaml.safe_load((ROOT/'configs/proposed_mechanism_identification.yaml').read_text(encoding='utf-8'))
    base = yaml.safe_load((ROOT/'configs/base.yaml').read_text(encoding='utf-8'))
    rows, issues, inputs = [], [], {}
    for seed in (11,22,33):
        for budget in (.6,1.2,1.8):
            models = {}
            for cell,(outgoing,value) in CELLS.items():
                name = f'seed{seed}_B{budget}_{outgoing}_{value}'
                folder = ROOT/'results/matched_mechanism/run01'/name
                cfg = yaml.safe_load((folder/'config.yaml').read_text(encoding='utf-8'))
                if cfg['design'] != design or cfg['base'] != {**base,'seed':seed,'B':budget}:
                    issues.append({'case':name,'config_differs_from_current_frozen_sources':True})
                m = load_model(folder/'model.json')
                generated = matched_model(cfg['base'],cfg['design'],outgoing,value)
                mismatches=[]
                for key,expected in asdict(generated).items():
                    if not np.array_equal(getattr(m,key),expected):
                        mismatches.append(key)
                u=load_controls(folder/'fine/controls.json')
                check_controls(m,*u)
                attack=np.zeros((6,6));attack[:,:2]=.4
                check_controls(m,attack,u[1],u[2])
                old=json.loads((folder/'case_audit.json').read_text(encoding='utf-8'))
                if mismatches or not old['numerical_pass']:
                    issues.append({'case':name,'model_mismatches':mismatches,'old_pass':old['numerical_pass']})
                models[cell]=asdict(m)
                for leaf in ['model.json','config.yaml','fine/controls.json','case_audit.json','fine_audit.json','fine_evaluation/summary.json']:
                    p=folder/leaf;inputs[p.relative_to(ROOT).as_posix()]=sha(p)
                rows.append({'case':name,'cell':cell,'seed':seed,'B':budget,'n':m.n,'K':len(u[0]),
                             'T':cfg['base']['T'],'model_mismatches':mismatches,'old_numerical_pass':old['numerical_pass'],
                             'fixed_attack':attack.tolist(),'model_source':str(folder.relative_to(ROOT)/'model.json'),
                             'game_source':str(folder.relative_to(ROOT)/'fine/controls.json'),
                             'q':m.q.tolist(),'g':m.g.tolist(),'out_strength':m.beta.sum(axis=1).tolist(),
                             'upstream_weights':[m.beta[0,2],m.beta[1,2]]})
            for left,right,allowed in [('A','B',{'q'}),('C','D',{'q'}),('A','C',{'beta'}),('B','D',{'beta'})]:
                changed={key for key in models[left] if not np.array_equal(models[left][key],models[right][key])}
                if changed!=allowed:
                    issues.append({'seed':seed,'B':budget,'pair':[left,right],'changed':sorted(changed),'expected':sorted(allowed)})
    # These are the historical nine D cells, not a complete four-cell fixed reoptimization.
    c2=ROOT/'results/supplement_c2/run02/comparison'
    c2_fixed=sorted(c2.glob('*/Fixed-trained_response.json'))
    for p in c2_fixed:
        info=json.loads(p.read_text(encoding='utf-8'))
        inputs[p.relative_to(ROOT).as_posix()]=sha(p)
        if info['player']!='D':
            issues.append({'wrong_C2_fixed_interface':p.as_posix()})
    # Preserve D1/D2/D3, solver and the original experiment sources as they stand now.
    for name in ['02_MODEL_SPEC.md','configs/base.yaml','configs/proposed_mechanism_identification.yaml',
                 'src/core.py','src/game_solver.py','src/matched_mechanism.py','src/supplement_c2.py',
                 'src/experiments.py','reports/MATCHED_MECHANISM_PROTOCOL.md','reports/SUPPLEMENT_C2_PROTOCOL.md',
                 'reports/WORK_C2_ROBUSTNESS_PROTOCOL.md','handoffs/C1_fix_report.md',
                 'results/work_c2_robustness/k_refinement/run01/metadata.json',
                 'results/work_c2_robustness/k_refinement/run01/tables/interactions.csv',
                 'results/work_c2_robustness/cross_environment/comparison.json']:
        inputs[name]=sha(ROOT/name)
    for base in ['paper/work_d1','paper/work_d2','paper/work_d3']:
        for p in (ROOT/base).rglob('*'):
            if p.is_file() and '_qa_packages' not in p.parts and '__pycache__' not in p.parts:
                inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    report={'status':'INTERFACE_AUDITED_INSTRUCTIONS_PENDING','date':'2026-11-11','timezone':'Asia/Shanghai',
            'formal_experiment_started':False,'case_count':len(rows),'issues':issues,'cases':rows,
            'C2_fixed_response_records':len(c2_fixed),
            'environment':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
                           'scipy':scipy.__version__,'yaml':yaml.__version__},
            'protected_files':inputs,
            'missing_required_input':'Work_D4_P0_修订执行指令.md; exact file not located; user path/content requested',
            'independence':'same execution session; proposed independent integrator is numerical cross-check, not a separate human reviewer'}
    (OUT/'interface_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'case_count':len(rows),'issues':issues,'protected_files':len(inputs),
                      'C2_fixed_response_records':len(c2_fixed),'status':report['status']},ensure_ascii=False))
    if issues:
        raise SystemExit(1)

if __name__=='__main__':
    run()
