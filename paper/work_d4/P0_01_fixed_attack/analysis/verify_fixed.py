"""Reconstruct paired arithmetic and replay all saved primary plans after the run."""
from pathlib import Path
import sys
import json
import hashlib
import csv
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from src.core import simulate,check_controls
from src.supplement_c2 import load_model,load_controls
from src.game_solver import ResponseProblem
PAPER=ROOT/'paper/work_d4/P0_01_fixed_attack'
RUN=ROOT/'results/work_d4/p0_1_fixed_attack/run01'
REPORT=ROOT/'reports/work_d4'
PARTS=['security','business','isolation','recovery','terminal_defense','attacker_value','attacker_effort','terminal_attacker']

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def csvrows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def did(x):return (x['D']-x['C'])-(x['B']-x['A'])

def main():
    checks=[]
    def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
    design=csvrows(PAPER/'design_matrix.csv');comparison=csvrows(PAPER/'four_cell_comparison.csv')
    frozen=load(PAPER/'frozen_inputs.json');meta=load(RUN/'metadata.json')
    for path,digest in frozen['protected_files'].items():
        check('protected:'+path,(ROOT/path).is_file() and sha(ROOT/path)==digest)
    for path,digest in meta['bindings'].items():
        check('registered_binding:'+path,sha(ROOT/path)==digest)
    check('complete_36_unique_design_cells',len(design)==36 and len({r['case'] for r in design})==36)
    check('nine_comparison_rows',len(comparison)==9)
    check('registered_pilot_passed',load(RUN/'pilot_gate.json')['passed'])
    failures=[];replaymax=0.;partmax=0.;residualmax=0.;vals={}
    for row in design:
        folder=RUN/row['case'];model=load_model(folder/'model.json')
        key=(int(row['seed']),float(row['B']))
        vals.setdefault(key,{})[row['cell']]={}
        if not (folder/'complete.json').exists():
            check('case_complete:'+row['case'],False);continue
        quality=load(folder/'case_quality.json')
        check('case_numeric_quality:'+row['case'],quality['numerical_pass'],quality['failed_conditions'])
        check('original_model_bytes:'+row['case'],sha(folder/'model.json')==row['model_sha256'])
        for mode in ('GAME','FIXED','CROSS'):
            target=folder/mode;u=load_controls(target/'controls.json');check_controls(model,*u)
            if mode!='GAME':
                expected=np.zeros((6,6));expected[:,:2]=.4
                check('constant_exogenous_attack:'+row['case']+':'+mode,np.array_equal(u[0],expected))
            else:
                original=load_controls(ROOT/row['game_source'])
                check('GAME_not_reoptimized:'+row['case'],all(np.array_equal(x,y) for x,y in zip(u,original)))
            objectives=load(target/'objectives.json')
            # Fresh replay from the actual serialized plan, separate from the run's aggregation.
            sim=simulate(model,*u,10.,48)
            err=max(abs(sim['J_D']-objectives['48']['J_D']),abs(sim['J_A']-objectives['48']['J_A']))
            replaymax=max(replaymax,err)
            check('serialized_primary_replay:'+row['case']+':'+mode,err<=1e-12,err)
            trajectory=np.load(target/'trajectory_H48.npz')
            check('full_trajectory_replay:'+row['case']+':'+mode,
                  np.array_equal(trajectory['times'],sim['times']) and np.array_equal(trajectory['states'],sim['states']))
            check('initial_state_and_domain:'+row['case']+':'+mode,
                  np.array_equal(sim['states'][0],model.x0) and sim['states'].min()>=-1e-10 and sim['states'].max()<=1+1e-10)
            part_error=abs(sum(sim['parts'][p] for p in PARTS[:5])-sim['J_D']);partmax=max(partmax,part_error)
            check('cost_parts_sum:'+row['case']+':'+mode,part_error<=1e-12)
            check('independent_integrator:'+row['case']+':'+mode,
                  load(target/'quality.json')['independent_pass'])
            vals[key][row['cell']][mode]=objectives
        fixed=load_controls(folder/'FIXED/controls.json')
        pr=ResponseProblem(model,*fixed,10.,48,'D')
        _,gradient=pr.value_gradient(pr.initial)
        residual=pr.projected_residual(pr.initial,gradient);residualmax=max(residualmax,residual)
        check('current_candidate_residual_recomputed:'+row['case'],residual<=1e-4,residual)
        for label in ('uniform','zero','random'):
            for H in (12,48):
                phase=folder/f'{label}_H{H}'
                initial=load_controls(phase/'initial_controls.json')
                check('all_path_attack_fixed:'+row['case']+f':{label}:{H}',np.array_equal(initial[0],fixed[0]))
                check('path_complete:'+row['case']+f':{label}:{H}',load(phase/'quality.json')['passed'])
    table_error=0.;delta_identity=0.;component_identity=0.
    for row in comparison:
        key=(int(row['seed']),float(row['B']));cells=vals[key]
        if len(cells)!=4 or any(not c for c in cells.values()):
            check('paired_group_complete:'+str(key),False);continue
        for mode,col in [('GAME','I_game'),('FIXED','I_fixed'),('CROSS','I_cross')]:
            values={c:o[mode]['48']['J_D'] for c,o in cells.items()}
            I=did(values);error=abs(I-float(row[col]));table_error=max(table_error,error)
            check('interaction_from_raw:'+str(key)+mode,error<=1e-12,error)
            normalized=100*I/values['C']
            check('C_denominator_normalization:'+str(key)+mode,
                  abs(normalized-float(row[mode+'_I_over_C_percent']))<=1e-10)
            component_sum=sum(did({c:o[mode]['48']['parts'][p] for c,o in cells.items()}) for p in PARTS[:5])
            component_identity=max(component_identity,abs(component_sum-I))
            check('component_interactions_sum:'+str(key)+mode,abs(component_sum-I)<=1e-12)
        delta=float(row['I_game'])-float(row['I_fixed'])
        check('delta_sign_definition:'+str(key),abs(delta-float(row['delta_I']))<=1e-12)
        error=abs(delta-(float(row['delta_I_attack_input'])+float(row['delta_I_defense_reoptimization'])))
        delta_identity=max(delta_identity,error)
        check('cross_decomposition_identity:'+str(key),error<=1e-12)
    check('no_protected_changes_at_run_end',not meta['protected_changes'])
    report=dict(status='PASS' if all(c['passed'] for c in checks) else 'REQUIRES_ATTENTION',
                check_count=len(checks),failures=[c for c in checks if not c['passed']],
                maximum_primary_replay_error=replaymax,maximum_cost_identity_error=partmax,
                maximum_recomputed_current_residual=residualmax,maximum_interaction_table_error=table_error,
                maximum_decomposition_identity_error=delta_identity,maximum_cost_interaction_identity_error=component_identity,
                scope='saved-plan replay, registered-quality checks and independent raw-file arithmetic; not global optimality',checks=checks)
    (REPORT/'P0_01_independent_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
    if report['failures']:raise SystemExit(1)

if __name__=='__main__':main()
