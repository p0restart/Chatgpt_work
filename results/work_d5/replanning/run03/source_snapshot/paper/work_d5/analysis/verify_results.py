"""Saved-file audit and independent DOP853 replay for D5."""
import argparse
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from src.core import dynamics,cost_rates,check_controls
from src.supplement_c2 import load_model,load_controls
from src.experiments import write_json


def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args()
    out=Path(args.run);started=time.perf_counter();checks=[];nodes=[];replays=[]
    def check(name,value,threshold=0):
        checks.append(dict(check=name,value=float(value),threshold=threshold,passed=bool(value<=threshold)))
    meta=json.loads((out/'metadata.json').read_text())
    controls=pd.read_csv(out/'executed_controls.csv')
    obj=pd.read_csv(out/'objectives.csv');tr=pd.read_csv(out/'trajectories.csv')
    plans=pd.read_csv(out/'planned_controls.csv')
    attempts=pd.read_csv(out/'optimizer_attempts.csv')
    audit=pd.read_csv(out/'solver_audit.csv');quality=pd.read_csv(out/'quality.csv')
    check('all_recorded_optimizer_success',int((~attempts.success).sum()))
    check('all_final_local_diagnostics_pass',int((~audit.passed).sum()))
    check('all_registered_quality_checks_pass',int((~quality.passed).sum()))
    check('source_protection',len(json.loads((out/'protected_after.json').read_text())['changed']))
    check('complete_18_trajectories',abs(len(controls.groupby(['B','evaluation','method']))-18))
    for (B,e),group in controls.groupby(['B','evaluation']):
        schedule={m:tuple(g.pivot(index='slot',columns='node',values=v).to_numpy()
            for v in ('a_actual','s','r')) for m,g in group.groupby('method')}
        for m,u in schedule.items():
            check(f'fair_attack:{B}:{e}:{m}',np.max(abs(u[0]-schedule['P'][0])))
            check(f'fair_prefix:{B}:{e}:{m}',max(np.max(abs(v[:3]-w[:3])) for v,w in zip(u,schedule['P'])))
        for method,u in schedule.items():
            label=f'{B}:{e}:{method}';folder=out/f'B{B}'
            mpre=load_model(folder/'model_pre.json');mpost=load_model(folder/'model_post.json')
            check_controls(mpre,*u)
            source=load_model(ROOT/f'results/matched_mechanism/run01/seed11_B{B}_unequal_high_at_node3/model.json')
            for key,value in vars(source).items():
                check(f'pre_model:{B}:{key}',np.max(abs(np.asarray(value,dtype=float)-np.asarray(getattr(mpre,key),dtype=float))))
                expected=np.array([.5,.25,0,0,0,0]) if key=='alpha' else value
                check(f'post_model:{B}:{key}',np.max(abs(np.asarray(expected,dtype=float)-np.asarray(getattr(mpost,key),dtype=float))))
            y=np.r_[mpre.x0,np.zeros(12)];pre=None
            for k in range(6):
                m=mpre if k<3 else mpost;a,s,r=(v[k] for v in u)
                def rhs(t,z):
                    x=z[:6]
                    return np.r_[dynamics(m,x,a,s,r),cost_rates(m,x,a,s,r),x]
                iv=solve_ivp(rhs,(k*5/3,(k+1)*5/3),y,method='DOP853',rtol=1e-11,atol=1e-13)
                assert iv.success;y=iv.y[:,-1]
                if k==2:pre=y.copy()
                if method in ('G','R') and k>=3:
                    j=k-3;restart=load_model(folder/f'{e}_{method}'/f'update{j}'/'model_restart.json')
                    saved=tr[(tr.B==B)&(tr.evaluation==e)&(tr.method==method)&(tr.H==48)]
                    state=saved.iloc[k*48][[f'x{i}' for i in range(6)]].to_numpy(float)
                    check(f'restart_observed_state:{label}:{j}',np.max(abs(restart.x0-state)),1e-12)
                    p=plans[(plans.B==B)&(plans.evaluation==e)&(plans.method==method)&
                        (plans['update']==j)&(plans.selected)]
                    first=p[p.absolute_slot==3+j].sort_values('node')
                    check(f'first_planned_action_executed:{label}:{j}',
                        max(np.max(abs(first.s_plan-u[1][k])),np.max(abs(first.r_plan-u[2][k]))),1e-14)
                    if method=='R':
                        for slot,pg in p.groupby('absolute_slot'):
                            check(f'R_uses_only_past_attack:{label}:{j}:{slot}',
                                np.max(abs(pg.sort_values('node').a_plan-u[0][k-1])),1e-14)
            for period,z in [('pre',pre),('post',y-pre),('full',y)]:
                parts=z[6:12];jd=float(sum(parts[:4]));ja=float(parts[4]-parts[5])
                row=obj[(obj.B==B)&(obj.evaluation==e)&(obj.method==method)&(obj.H==192)&(obj.period==period)].iloc[0]
                error=max(abs(jd-row.J_D),abs(ja-row.J_A),
                    max(abs(parts[i]-row[name]) for i,name in enumerate(('security','business','isolation','recovery','attacker_value','attacker_effort'))))
                check(f'DOP853_objectives:{label}:{period}',error,1e-6)
                replays.append(dict(B=B,evaluation=e,method=method,period=period,J_D_DOP853=jd,J_A_DOP853=ja,error=error))
                for node in range(6):
                    nodes.append(dict(B=B,evaluation=e,method=method,period=period,node=node,
                        state_area=float(z[12+node]),q=float(mpre.q[node]),
                        weighted_security=float(z[12+node]*mpre.q[node]),
                        end_state=float((pre if period=='pre' else y)[node])))
            terminal=tr[(tr.B==B)&(tr.evaluation==e)&(tr.method==method)&(tr.H==192)].iloc[-1]
            check(f'DOP853_terminal_state:{label}',np.max(abs(y[:6]-terminal[[f'x{i}' for i in range(6)]].to_numpy(float))),1e-6)
    compare=pd.read_csv(out/'comparisons.csv')
    for _,row in compare.iterrows():
        vals=obj[(obj.B==row.B)&(obj.evaluation==row.evaluation)&(obj.period==row.period)&(obj.H==48)].set_index('method').J_D
        check(f'paired_P_G:{row.B}:{row.evaluation}:{row.period}',abs(row.delta_P_to_G-(vals.P-vals.G)),1e-12)
        check(f'paired_R_G:{row.B}:{row.evaluation}:{row.period}',abs(row.delta_R_to_G-(vals.R-vals.G)),1e-12)
    pd.DataFrame(checks).to_csv(out/'independent_checks.csv',index=False)
    pd.DataFrame(nodes).to_csv(out/'node_state_summary.csv',index=False)
    pd.DataFrame(replays).to_csv(out/'independent_replay.csv',index=False)
    result=dict(passed=all(c['passed'] for c in checks),checks=len(checks),
        failures=[c for c in checks if not c['passed']],seconds=time.perf_counter()-started,
        method='separate DOP853 replay using frozen dynamics and cost rates; saved-file arithmetic and information checks',
        scope='author-side independent numerical audit, not independent peer review or global optimality')
    write_json(out/'independent_validation.json',result);print(json.dumps(result))


if __name__=='__main__':main()
