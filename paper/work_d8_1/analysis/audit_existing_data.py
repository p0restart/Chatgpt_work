"""D8-1: read saved D7 outputs; no solver calls, simulation or parameter changes."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
D7 = ROOT / 'paper/work_d7'
OUT = ROOT / 'paper/work_d8_1'
DATA = OUT / 'data'
DATA.mkdir(parents=True, exist_ok=True)
sources = {}
checks = []

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(rel):
    p = D7 / rel
    sources[str(p.relative_to(ROOT)).replace('\\', '/')] = sha(p)
    return pd.read_csv(p)

def load(rel):
    p = D7 / rel
    sources[str(p.relative_to(ROOT)).replace('\\', '/')] = sha(p)
    return json.loads(p.read_text(encoding='utf-8-sig'))

def check(name, condition, error=None):
    checks.append(dict(check=name, passed=bool(condition), error=error))
    assert condition, (name, error)

def close(name, a, b, tol=1e-9):
    error = float(np.max(np.abs(np.asarray(a) - np.asarray(b))))
    check(name, error <= tol, error)

def save(name, df):
    df.to_csv(DATA / (name + '.csv'), index=False, encoding='utf-8-sig')
    (DATA / (name + '.md')).write_text(df.to_markdown(index=False, floatfmt='.6f'), encoding='utf-8')

cross = pd.concat([read(f'results/static/B{B}/cross_evaluation.csv') for B in [.6, 1.2, 1.8]], ignore_index=True)
close('18 cross costs sum', cross.J_D, cross[['security','business','isolation','recovery','terminal_defense']].sum(axis=1))
close('18 attacker payoffs', cross.J_A, cross.attacker_value-cross.attacker_effort+cross.terminal_attacker)
save('cross_full', cross)
matrix = cross.pivot(index=['B','method'], columns='attack', values='J_D').reset_index()[['B','method','a0','aG','aBR_F']]
save('cross_matrix', matrix)
save('fixed_attack_costs', cross[cross.attack=='a0'][['B','method','security','business','isolation','recovery','J_D']])
payoffs = []
for B in [.6,1.2,1.8]:
    d = cross[cross.B==B].set_index(['method','attack'])
    for attack in ['a0','aG','aBR_F']:
        g, f = d.loc[('G',attack)], d.loc[('F',attack)]
        payoffs.append(dict(B=B,attack=attack,G=g.J_D,F=f.J_D,F_minus_G=f.J_D-g.J_D,percent=100*(f.J_D-g.J_D)/f.J_D))
    attacks = load(f'results/static/B{B}/cross_attacks.json')
    close(f'attack change B{B}', np.max(np.abs(np.array(attacks['aG'])-attacks['aBR_F'])), attacks['max_attack_change'])
    check(f'JA response to G B{B}', d.loc[('G','aG')].J_A >= d.loc[('G','aBR_F')].J_A)
    check(f'JA response to F B{B}', d.loc[('F','aBR_F')].J_A >= d.loc[('F','aG')].J_A)
close('user B1.2 matrix rounded', matrix[matrix.B==1.2].set_index('method').loc[['G','F'],['a0','aG','aBR_F']], [[9.467228,9.326647,9.326860],[9.466796,9.327081,9.327376]], 5.1e-7)
save('same_attack_differences', pd.DataFrame(payoffs))

rolling = []
objectives = []
predictions = []
for case, B in [('event',.6),('event',1.2),('event',1.8),('control',1.2)]:
    folder = f'results/rolling_{case}_B{B}'
    comp = read(folder+'/comparisons.csv')
    obj = read(folder+'/objectives.csv')
    obj = obj[obj.H==48].copy()
    exe = read(folder+'/executed_controls.csv')
    plans = read(folder+'/planned_controls.csv')
    attacks = read(folder+'/attack_scenarios.csv')
    objectives.append(obj.assign(case=case))
    close(f'{folder} cost sum',obj.J_D,obj[['security','business','isolation','recovery','terminal_defense']].sum(axis=1))
    for E in ['E0','E1']:
        e = exe[exe.evaluation==E]
        pivot = e.pivot(index=['slot','node'],columns='method',values='a_actual')
        close(f'{folder}/{E} common actual attack',pivot[['G','R']],np.repeat(pivot[['P']].values,2,axis=1),1e-14)
        for action in ['s','r']:
            pivot=e[e.slot<3].pivot(index=['slot','node'],columns='method',values=action)
            close(f'{folder}/{E} common prefix {action}',pivot[['G','R']],np.repeat(pivot[['P']].values,2,axis=1),1e-14)
        for method in ['P','G','R']:
            o=obj[(obj.evaluation==E)&(obj.method==method)].set_index('period')
            close(f'{folder}/{E}/{method} full=pre+post',o.loc['full','J_D'],o.loc['pre','J_D']+o.loc['post','J_D'])
            actual=e[(e.method==method)&(e.slot>=3)].sort_values(['slot','node'])
            ref=attacks[attacks.evaluation==E].sort_values(['slot','node'])
            close(f'{folder}/{E}/{method} attack export',actual.a_actual,ref.a_actual,1e-14)
        for period in ['post','full']:
            o=obj[(obj.evaluation==E)&(obj.period==period)].set_index('method')
            c=comp[(comp.evaluation==E)&(comp.period==period)].iloc[0]
            P,G,R=[o.loc[m,'J_D'] for m in ['P','G','R']]
            close(f'{folder}/{E}/{period} comparison',[c.J_D_P,c.J_D_G,c.J_D_R],[P,G,R])
            rolling.append(dict(case=case,B=B,evaluation=E,period=period,P=P,G=G,R=R,
                P_minus_G=P-G,P_minus_R=P-R,R_minus_G=R-G,
                percent_P_to_G=100*(P-G)/P,percent_P_to_R=100*(P-R)/P,percent_R_to_G=100*(R-G)/R))
        for method in ['G','R']:
            for j in range(3):
                k=j+3
                sel=plans[(plans.evaluation==E)&(plans.method==method)&(plans['update']==j)&(plans.selected==True)&(plans.absolute_slot==k)].sort_values('node')
                act=attacks[(attacks.evaluation==E)&(attacks.slot==k)].sort_values('node')
                check(f'{folder}/{E}/{method}/{j} six selected prediction rows',len(sel)==6)
                err=sel.a_plan.to_numpy()-act.a_actual.to_numpy()
                predictions.append(dict(case=case,B=B,evaluation=E,method=method,update=j,t_start=k*5/3,
                    API_pred=sel.a_plan.iloc[0],Web_pred=sel.a_plan.iloc[1],API_actual=act.a_actual.iloc[0],Web_actual=act.a_actual.iloc[1],
                    API_error=err[0],Web_error=err[1],L1=np.abs(err).sum(),L2=np.linalg.norm(err),Linf=np.abs(err).max()))
rolling=pd.DataFrame(rolling)
save('rolling_all_periods', rolling)
save('rolling_event_post',rolling[(rolling['case']=='event')&(rolling.period=='post')])
save('rolling_event_full',rolling[(rolling['case']=='event')&(rolling.period=='full')])
save('rolling_control',rolling[rolling['case']=='control'])
save('execution_costs',pd.concat(objectives,ignore_index=True))
predictions=pd.DataFrame(predictions)
save('prediction_errors_all_updates',predictions)
save('prediction_errors_first_B1.2',predictions[(predictions['case']=='event')&(predictions.B==1.2)&(predictions['update']==0)])
save('prediction_error_time_mean',predictions.groupby(['case','B','evaluation','method'],as_index=False)[['L1','L2','Linf']].mean())

actions=read('results/derived/all_asset_decisions.csv')
g=actions[(actions['case']=='offline')&(actions.method=='G')].copy()
check('all action exports 1080 rows',len(actions)==1080)
for B in [.6,1.2,1.8]:
    model=load(f'results/static/B{B}/model.json')
    u=load(f'results/static/B{B}/G_controls.json')
    z=g[g.B==B].sort_values(['slot','code_index'])
    for i,col in enumerate(['a','s','r']):
        close(f'raw G controls and asset export B{B} {col}',np.array(u[i]).ravel(),z[col],1e-14)
    selected=read('results/static/planned_controls.csv')
    selected=selected[(selected.B==B)&(selected.method=='G')&(selected.selected==True)].sort_values(['absolute_slot','node'])
    for col in ['a','s','r']:
        close(f'static plan export B{B} {col}',selected[col+'_plan'],z[col],1e-14)
save('asset_actions_B1.2',g[g.B==1.2])
avg=g.groupby(['B','paper_node'],as_index=False)[['s','r','asset_resource']].mean()
avg['share_of_used_defense']=avg.asset_resource/avg.groupby('B').asset_resource.transform('sum')
save('asset_mean_all_budgets',avg)
use=g.drop_duplicates(['B','slot'])[['B','slot','t_start','t_end','total_resource','capacity_slack']]
save('resource_by_interval',use)

# Record original diagnostics; these are inherited D7 checks, not newly executed optimization.
quality=read('results/derived/numerical_quality_summary.csv')
save('inherited_numerical_quality',quality)
load('results/verification.json')
for rel in ['D7_experiment_protocol.md','paper_v2_zh.md','execution_report.md','config_new_topology.yaml','algorithm_code_map.md','claim_evidence_map.md','reference_claim_map.md','topology_assets.csv','topology_edges.csv']:
    p=D7/rel;sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
for rel in ['src/core.py','src/game_solver.py','src/matched_mechanism.py','src/experiments.py','paper/work_d5/analysis/run_replanning.py']:
    p=D7/'source_snapshot'/rel;sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
for rel in ['analysis/run_d7.py','analysis/run_rolling.py','analysis/summarize_results.py']:
    p=D7/rel;sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
manifest=OUT/'data/source_hashes.json'
if manifest.exists():
    close('source manifest keys unchanged',len(sources),len(json.loads(manifest.read_text())))
    check('all D7 input hashes unchanged since first D8 audit',sources==json.loads(manifest.read_text()))
else:
    manifest.write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'data/audit_checks.json').write_text(json.dumps(dict(passed=all(c['passed'] for c in checks),checks=checks,scope='Read-only arithmetic and saved-control audit. No optimization or new simulation.'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=True,checks=len(checks),sources=len(sources),output=str(DATA)),ensure_ascii=False))
