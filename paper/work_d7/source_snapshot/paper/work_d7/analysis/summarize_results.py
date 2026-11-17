"""Traceable tables and per-asset action/cost exports; no new optimization."""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd
from scipy.integrate import solve_ivp
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.supplement_c2 import load_model,load_controls
BASE=ROOT/'paper/work_d7';OUT=BASE/'results/derived';OUT.mkdir(exist_ok=True)
assets=pd.read_csv(BASE/'topology_assets.csv').asset.tolist()
def table(df):return df.to_markdown(index=False,floatfmt='.6f')
actions=[];summaries=[]
def action_rows(folder,case,B,E,method,pre,post,u,status):
    x=pre.x0.copy();dt=5/3
    for k in range(6):
        m=pre if k<3 else post;a,s,r=[v[k] for v in u]
        def fun(t,y):
            z=y[:6];rate=(1-z)*(m.alpha*a+m.beta.T@((1-m.epsilon*s)*z))-(m.delta+m.gamma*r)*z
            return np.r_[rate,z]
        sol=solve_ivp(fun,(0,dt),np.r_[x,np.zeros(6)],rtol=1e-11,atol=1e-13,method='DOP853');assert sol.success
        end=sol.y[:6,-1];area=sol.y[6:,-1]
        for i in range(6):
            actions.append(dict(case=case,B=B,evaluation=E,method=method,slot=k,t_start=k*dt,t_end=(k+1)*dt,paper_node=f'v{i+1}',code_index=i,asset=assets[i],a=a[i],s=s[i],r=r[i],asset_resource=s[i]+r[i],total_resource=sum(s+r),capacity_slack=B-sum(s+r),attack_resource=sum(a),x_start=x[i],x_end=end[i],damage_area=area[i],security=m.q[i]*area[i],business=dt*m.h[i]*s[i],isolation=dt*m.c_s[i]*s[i]**2/2,recovery=dt*m.c_r[i]*r[i]**2/2,solver_status='passed_local_numerical_checks',status_source=status,control_source=str(folder.relative_to(BASE))))
        x=end.copy()

cross=[];static=[];allcost=[];timing=[];audit=[];qualities=[];attempts=[]
for B in [.6,1.2,1.8]:
    f=BASE/f'results/static/B{B}';df=pd.read_csv(f/'cross_evaluation.csv');allcost.append(df.assign(case='offline_cross',period='full'))
    for protocol,ag,af in [('共同固定攻击','a0','a0'),('各自攻击响应','aG','aBR_F')]:
        g=df[(df.method=='G')&(df.attack==ag)].iloc[0];v=df[(df.method=='F')&(df.attack==af)].iloc[0]
        cross.append(dict(B=B,protocol=protocol,J_D_G=g.J_D,J_D_F=v.J_D,F_minus_G=v.J_D-g.J_D,percent=100*(v.J_D-g.J_D)/v.J_D))
    m=load_model(f/'model.json')
    for method in ['G','F']:
        d=json.loads((f/f'{method}_evaluation.json').read_text());dec=json.loads((f/method/'decision.json').read_text());d.update(seconds=dec['online_seconds'],spread=dec['spread']);static.append(d)
        action_rows(f/f'{method}_controls.json','offline',B,'aG' if method=='G' else 'a0',method,m,m,load_controls(f/f'{method}_controls.json'),str((f/method/'decision.json').relative_to(BASE)))

rolling=[]
for folder in sorted((BASE/'results').glob('rolling_*_B*')):
    B=float(folder.name.rsplit('B',1)[1]);case='control' if 'control' in folder.name else 'event';f=folder/f'B{B}'
    comp=pd.read_csv(folder/'comparisons.csv');rolling.append(comp.assign(case=case))
    obj=pd.read_csv(folder/'objectives.csv');allcost.append(obj[obj.H==48].assign(case=case))
    pre=load_model(f/'model_pre.json');post=load_model(f/'model_post.json')
    for E in ['E0','E1']:
        for method in ['P','G','R']:
            action_rows(f/f'{E}_{method}_executed.json',case,B,E,method,pre,post,load_controls(f/f'{E}_{method}_executed.json'),str((f/'budget_gate.json').relative_to(BASE)))
for folder in [BASE/'results/static',*sorted((BASE/'results').glob('rolling_*_B*'))]:
    for dest,name in [(timing,'timing'),(audit,'solver_audit'),(qualities,'quality'),(attempts,'optimizer_attempts')]:
        dest.append(pd.read_csv(folder/f'{name}.csv').assign(run=folder.name))
acts=pd.DataFrame(actions);acts.to_csv(OUT/'all_asset_decisions.csv',index=False,encoding='utf-8-sig')
for key,df in [('cross_summary',pd.DataFrame(cross)),('static_summary',pd.DataFrame(static)),('rolling_summary',pd.concat(rolling,ignore_index=True)),('cost_components',pd.concat(allcost,ignore_index=True)),('timing_all',pd.concat(timing,ignore_index=True)),('audits_all',pd.concat(audit,ignore_index=True)),('quality_all',pd.concat(qualities,ignore_index=True))]:
    df.to_csv(OUT/f'{key}.csv',index=False,encoding='utf-8-sig')
    if key in ['cross_summary','static_summary','rolling_summary']: (OUT/f'{key}.md').write_text(table(df),encoding='utf-8')
a=pd.concat(audit);q=pd.concat(qualities);t=pd.concat(timing);o=pd.concat(attempts)
assert a.passed.all() and q.passed.all() and o.success.all()
metrics=dict(action_rows=len(acts),optimization_attempts=len(o),audit_rows=len(a),quality_rows=len(q),max_relative_improvement=a.relative_improvement.max(),max_incumbent_residual=a.incumbent_residual.max(),max_response_distance=a.response_distance.max(),max_path_spread=q[q.check.str.contains('spread')].value.max(),max_capacity_violation=max(0,-acts.capacity_slack.min()),max_database_isolation=acts[acts.code_index==4].s.max(),max_state=acts[['x_start','x_end']].max().max())
for method in ['G','R']:
    times=t[(t.run.str.startswith('rolling_event'))&(t.method==method)&(t.item=='replanning_total')].seconds
    metrics[f'{method}_event_replanning_seconds']=dict(n=len(times),median=times.median(),min=times.min(),max=times.max())
for B in [.6,1.2,1.8]:metrics[f'attack_change_B{B}']=json.loads((BASE/f'results/static/B{B}/cross_attacks.json').read_text())['max_attack_change']
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
# Check every exported per-node cost against its original aggregate objective.
errors=[]
for (case,B,E,method),group in acts.groupby(['case','B','evaluation','method']):
    if case=='offline':ref=json.loads((BASE/f'results/static/B{B}/{method}_evaluation.json').read_text())
    else:
        df=pd.read_csv(BASE/f'results/rolling_{case}_B{B}/objectives.csv');ref=df[(df.evaluation==E)&(df.method==method)&(df.H==48)&(df.period=='full')].iloc[0]
    errors.append(max(abs(group[k].sum()-ref[k]) for k in ['security','business','isolation','recovery']))
assert max(errors)<1e-6
(OUT/'asset_export_check.json').write_text(json.dumps(dict(passed=True,groups=len(errors),max_cost_error=max(errors)),indent=2),encoding='utf-8')
print(json.dumps(metrics))
