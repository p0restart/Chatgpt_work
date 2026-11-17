"""Recheck saved controls and objectives only; no optimization or new scenarios."""
from pathlib import Path
import json, hashlib, csv, sys
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
# Prefer the self-contained saved inputs; retain the original project fallback.
STATIC = BASE/'raw_static' if (BASE/'raw_static').is_dir() else ROOT/'paper/work_d7/results/static'
OUT = BASE/'data'
OUT.mkdir(exist_ok=True)
checks=[]; sources={}; controls=[]; budgets=[]; crosses=[]; replayrows=[]

def read_json(p):
    sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text(encoding='utf-8-sig'))

def check(name, value, tolerance=1e-9):
    value=float(value)
    checks.append(dict(check=name,error=value,tolerance=tolerance,passed=value<=tolerance))

def simulate(m, ctrl, H):
    """Independent augmented RK4 integration, same defined model, fixed controls."""
    a,s,r=ctrl
    n=len(m['x0']); dt=10/len(a)/H
    beta=np.asarray(m['beta']); alpha=np.asarray(m['alpha']); eps=np.asarray(m['epsilon'])
    delta=np.asarray(m['delta']); gamma=np.asarray(m['gamma']); q=np.asarray(m['q']); g=np.asarray(m['g'])
    h=np.asarray(m['h']); cs=np.asarray(m['c_s']); cr=np.asarray(m['c_r']); ca=np.asarray(m['c_a'])
    y=np.r_[m['x0'],np.zeros(6)]
    history=[y.copy()]
    for k in range(len(a)):
        business=float(h@s[k]); isolation=float(.5*cs@s[k]**2)
        recovery=float(.5*cr@r[k]**2); effort=float(.5*ca@a[k]**2)
        def rhs(v):
            x=v[:n]
            dx=(1-x)*(alpha*a[k]+beta.T@(x*(1-eps*s[k])))-(delta+gamma*r[k])*x
            return np.r_[dx,q@x,business,isolation,recovery,g@x,effort]
        for _ in range(H):
            f1=rhs(y);f2=rhs(y+dt*f1/2);f3=rhs(y+dt*f2/2);f4=rhs(y+dt*f3)
            y=y+dt*(f1+2*f2+2*f3+f4)/6;history.append(y.copy())
    parts=dict(zip(['security','business','isolation','recovery','attacker_value','attacker_effort'],y[n:]))
    return dict(J_D=float(sum(y[n:n+4])+np.asarray(m['omega'])@y[:n]),
                J_A=float(y[n+4]-y[n+5]+np.asarray(m['nu'])@y[:n]),parts=parts,
                states=np.asarray(history)[:,:n],all=np.asarray(history))

for B in (.6,1.2,1.8):
    folder=STATIC/f'B{B}'
    m=read_json(folder/'model.json')
    plans={p:np.asarray(read_json(folder/f'{p}_controls.json')) for p in ('G','F')}
    attacks={p:np.asarray(a) for p,a in read_json(folder/'cross_attacks.json').items() if p in ('a0','aG','aBR_F')}
    sourcecross=pd.read_csv(folder/'cross_evaluation.csv')
    for plan, u in plans.items():
        for k in range(6):
            total=float(np.asarray(m['b_s'])@u[1,k]+np.asarray(m['b_r'])@u[2,k])
            budgets.append(dict(B=B,plan=plan,slot=k+1,t_start=k*10/6,t_end=(k+1)*10/6,
                isolation=float(np.asarray(m['b_s'])@u[1,k]),recovery=float(np.asarray(m['b_r'])@u[2,k]),
                total=total,capacity=B,slack=B-total,active=abs(B-total)<=1e-8))
            for i in range(6):
                controls.append(dict(B=B,plan=plan,slot=k+1,asset=i+1,t_start=k*10/6,t_end=(k+1)*10/6,
                    a=u[0,k,i],s=u[1,k,i],r=u[2,k,i],resource=m['b_s'][i]*u[1,k,i]+m['b_r'][i]*u[2,k,i]))
        check(f'B{B}/{plan}/bounds',max(0,float(-u.min()),float(u.max()-1)),1e-10)
        check(f'B{B}/{plan}/capacity',max(0,float(np.max(u[1]@m['b_s']+u[2]@m['b_r']-B))),1e-10)
        for attack,a in attacks.items():
            ctrl=np.array([a,u[1],u[2]])
            lo=simulate(m,ctrl,48); hi=simulate(m,ctrl,192)
            sr=sourcecross[(sourcecross.method==plan)&(sourcecross.attack==attack)].iloc[0]
            err=max(abs(lo['J_D']-sr.J_D),abs(lo['J_A']-sr.J_A))
            check(f'B{B}/{plan}/{attack}/saved_objective',err,1e-9)
            griderr=float(np.max(abs(lo['all']-hi['all'][::4])))
            check(f'B{B}/{plan}/{attack}/H48_H192',griderr,1e-6)
            check(f'B{B}/{plan}/{attack}/state_bounds',max(0,float(-hi['states'].min()),float(hi['states'].max()-1)),1e-10)
            replayrows.append(dict(B=B,plan=plan,attack=attack,saved_J_D=sr.J_D,replayed_J_D=hi['J_D'],
                saved_J_A=sr.J_A,replayed_J_A=hi['J_A'],integration_error=griderr,
                **{f'x{i+1}_T':hi['states'][-1,i] for i in range(6)},**hi['parts']))
    for attack in attacks:
        g=next(x for x in replayrows if x['B']==B and x['plan']=='G' and x['attack']==attack)
        f=next(x for x in replayrows if x['B']==B and x['plan']=='F' and x['attack']==attack)
        crosses.append(dict(B=B,attack=attack,J_D_G=g['replayed_J_D'],J_D_F=f['replayed_J_D'],
            F_minus_G=f['replayed_J_D']-g['replayed_J_D'],percent_relative_F=(f['replayed_J_D']-g['replayed_J_D'])/f['replayed_J_D']*100))

pd.DataFrame(controls).to_csv(OUT/'complete_controls.csv',index=False,float_format='%.17g',encoding='utf-8-sig')
pd.DataFrame(budgets).to_csv(OUT/'capacity_by_slot.csv',index=False,float_format='%.17g',encoding='utf-8-sig')
pd.DataFrame(replayrows).to_csv(OUT/'fixed_control_replay.csv',index=False,float_format='%.17g',encoding='utf-8-sig')
pd.DataFrame(crosses).to_csv(OUT/'common_attack_comparison.csv',index=False,float_format='%.17g',encoding='utf-8-sig')
pair=[]
for B in (.6,1.2,1.8):
    g=next(x for x in replayrows if x['B']==B and x['plan']=='G' and x['attack']=='aG')
    f=next(x for x in replayrows if x['B']==B and x['plan']=='F' and x['attack']=='aBR_F')
    pair.append(dict(B=B,J_D_G=g['replayed_J_D'],J_D_F=f['replayed_J_D'],F_minus_G=f['replayed_J_D']-g['replayed_J_D'],
        percent_relative_F=(f['replayed_J_D']-g['replayed_J_D'])/f['replayed_J_D']*100))
pd.DataFrame(pair).to_csv(OUT/'own_response_comparison.csv',index=False,float_format='%.17g',encoding='utf-8-sig')

# The downloaded package provides saved responses, not full optimizer traces.
sens=BASE/'input/sensitivity_package'
sumdf=pd.read_csv(sens/'item_04.csv'); adf=pd.read_csv(sens/'item_02.csv'); ddf=pd.read_csv(sens/'item_06.csv')
m=read_json(STATIC/'B1.2/model.json'); orig=np.asarray(read_json(STATIC/'B1.2/G_controls.json'))
al={name:g.pivot(index='slot',columns='asset',values='attack').sort_index().to_numpy() for name,g in adf.groupby('scenario')}
dl={}
sens_replay=[]
for name,sign in [('positive',1),('negative',-1)]:
    shifted=orig.copy();shifted[2,1:4,0]-=sign*.05;shifted[2,1:4,1]+=sign*.05
    check(f'sensitivity/{name}/capacity_preserved',np.max(abs((shifted[1]+shifted[2]).sum(1)-(orig[1]+orig[2]).sum(1))),1e-12)
    g=ddf[ddf.scenario==name]
    defense=np.array([g.pivot(index='slot',columns='asset',values=v).sort_index().to_numpy() for v in ('isolation','recovery')])
    dl[name]=defense
    row=sumdf[sumdf.scenario==name].iloc[0]
    olda=simulate(m,shifted,192)
    newa=simulate(m,np.array([al[name],shifted[1],shifted[2]]),192)
    oldd=simulate(m,np.array([al[name],orig[1],orig[2]]),192)
    newd=simulate(m,np.array([al[name],*defense]),192)
    vals=dict(JA_original_attack=olda['J_A'],JA_BR=newa['J_A'],JA_improvement=newa['J_A']-olda['J_A'],
              JD_original_defense=oldd['J_D'],JD_BR=newd['J_D'],JD_improvement=oldd['J_D']-newd['J_D'],
              max_attack_change_from_baseline_BR=float(np.max(abs(al[name]-al['baseline']))),
              max_defense_change=float(np.max(abs(defense-orig[1:]))))
    for key,val in vals.items():check(f'sensitivity/{name}/{key}',abs(val-row[key]),1e-9)
    sens_replay.append(dict(scenario=name,**vals))
comp=read_json(sens/'item_05.json')
check('sensitivity/attack_distance',abs(np.max(abs(al['positive']-al['negative']))-comp['positive_negative_attack_distance']),1e-12)
check('sensitivity/defense_distance',abs(np.max(abs(dl['positive']-dl['negative']))-comp['positive_negative_defense_distance']),1e-12)
pd.DataFrame(sens_replay).to_csv(OUT/'sensitivity_replay.csv',index=False,float_format='%.17g',encoding='utf-8-sig')
audit=pd.read_csv(STATIC/'solver_audit.csv')
attempts=pd.read_csv(STATIC/'optimizer_attempts.csv')
quality=pd.read_csv(STATIC/'quality.csv')
diagnostics=dict(scope='D7 static three capacities, all recorded paths and static validation calls',
    audit_rows=len(audit),optimizer_calls=len(attempts),all_optimizer_success=bool(attempts.success.all()),
    max_relative_improvement=float(audit.relative_improvement.max()),
    max_incumbent_residual=float(audit.incumbent_residual.max()),
    max_violation=float(attempts.violation.max()),
    max_response_distance=float(audit.response_distance.max()),
    max_three_path_spread=float(quality[quality['check']=='three_path_control_spread'].value.max()),
    fixed_control_replay_max_difference=max(r['integration_error'] for r in replayrows))
pd.DataFrame(checks).to_csv(OUT/'audit_checks.csv',index=False,float_format='%.17g')
summary=dict(passed=all(c['passed'] for c in checks),check_count=len(checks),diagnostics=diagnostics,
    missing_table2_recovery=float(orig[2,1,3]),sources=sources,
    scope='Saved-control replay and arithmetic only, no best-response reoptimization or new experiment')
(OUT/'audit_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='sources'},ensure_ascii=True,indent=2))
if not summary['passed']:raise SystemExit('Audit failed, see audit_checks.csv')
