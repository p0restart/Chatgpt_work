"""Independent trajectory/cost replay and source/feasibility checks (no optimization)."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.supplement_c2 import load_model,load_controls
from src.core import check_controls
BASE=ROOT/'paper/work_d7';rows=[]
def add(name,val,tol):rows.append(dict(check=name,value=float(val),tolerance=tol,passed=bool(val<=tol)))
def replay(pre,post,u):
    # Independently written augmented ODE; no core.dynamics/cost_rates/RK4 calls.
    y=np.r_[pre.x0,np.zeros(6)];boundary=[pre.x0.copy()]
    for k in range(6):
        m=pre if k<3 else post;a,s,r=[v[k] for v in u]
        def fun(t,z):
            x=z[:6];exposure=m.alpha*a
            for j in range(6):
                for i in range(6):exposure[i]+=m.beta[j,i]*(1-m.epsilon[j]*s[j])*x[j]
            dx=(1-x)*exposure-(m.delta+m.gamma*r)*x
            costs=[sum(m.q*x),sum(m.h*s),sum(m.c_s*s*s)/2,sum(m.c_r*r*r)/2,sum(m.g*x),sum(m.c_a*a*a)/2]
            return np.r_[dx,costs]
        sol=solve_ivp(fun,(k*5/3,(k+1)*5/3),y,method='DOP853',rtol=1e-11,atol=1e-13)
        assert sol.success;y=sol.y[:,-1];boundary.append(y[:6].copy())
    return np.array(boundary),y[6:]

for B in [1.2,.6,1.8]:
    f=BASE/f'results/static/B{B}';m=load_model(f/'model.json')
    assert json.loads((f/'static_gate.json').read_text())['passed']
    for method in ['G','F']:
        u=load_controls(f/f'{method}_controls.json');check_controls(m,*u)
        x,c=replay(m,m,u);s=pd.read_csv(f/f'{method}_states.csv');d=json.loads((f/f'{method}_evaluation.json').read_text())
        add(f'static_{B}_{method}_states',np.max(abs(x-s[[f'x{i}' for i in range(6)]].to_numpy()[::48])),1e-6)
        add(f'static_{B}_{method}_cost',max(abs(c[j]-d[p]) for j,p in enumerate(['security','business','isolation','recovery','attacker_value','attacker_effort'])),1e-6)
        add(f'static_{B}_{method}_database_isolation',np.max(abs(u[1][:,4])),1e-8)

for folder in sorted((BASE/'results').glob('rolling_*_B*')):
    B=float(folder.name.rsplit('B',1)[1]);f=folder/f'B{B}'
    assert json.loads((f/'budget_gate.json').read_text())['passed']
    pre=load_model(f/'model_pre.json');post=load_model(f/'model_post.json')
    obj=pd.read_csv(folder/'objectives.csv');tr=pd.read_csv(folder/'trajectories.csv')
    quality=pd.read_csv(folder/'quality.csv');assert quality.passed.all()
    attempts=pd.read_csv(folder/'optimizer_attempts.csv');assert attempts.success.all()
    audit=pd.read_csv(folder/'solver_audit.csv');assert audit.passed.all()
    for E in ['E0','E1']:
        pairs=[]
        for method in ['P','G','R']:
            u=load_controls(f/f'{E}_{method}_executed.json');check_controls(pre,*u);pairs.append(u)
            x,c=replay(pre,post,u)
            state=tr[(tr.evaluation==E)&(tr.method==method)&(tr.H==48)]
            o=obj[(obj.evaluation==E)&(obj.method==method)&(obj.H==48)&(obj.period=='full')].iloc[0]
            add(f'{folder.name}_{E}_{method}_states',np.max(abs(x-state[[f'x{i}' for i in range(6)]].to_numpy()[::48])),1e-6)
            add(f'{folder.name}_{E}_{method}_cost',max(abs(c[j]-o[p]) for j,p in enumerate(['security','business','isolation','recovery','attacker_value','attacker_effort'])),1e-6)
            add(f'{folder.name}_{E}_{method}_JD',abs(sum(c[:4])-o.J_D),1e-6)
            add(f'{folder.name}_{E}_{method}_database_isolation',abs(u[1][:,4]).max(),1e-8)
        assert all(np.array_equal(pairs[0][0],u[0]) for u in pairs[1:])
        assert all(np.array_equal(pairs[0][j][:3],u[j][:3]) for u in pairs[1:] for j in [1,2])
assert len(list((BASE/'results').glob('rolling_*_B*')))==4
manifest=json.loads((BASE/'sources/source_manifest.json').read_text())
for p,info in manifest.items():
    normalized=p.replace('\\','/')
    if normalized.startswith('src/') or normalized=='02_MODEL_SPEC.md' or normalized=='paper/work_d5/analysis/run_replanning.py':
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==info['sha256'],p
pd.DataFrame(rows).to_csv(BASE/'results/independent_checks.csv',index=False)
result=dict(passed=all(r['passed'] for r in rows),checks=len(rows),max_replay_error=max(r['value'] for r in rows),scope='Independent DOP853 fixed-control replay, feasibility and saved audit checks; not independent optimization or external review')
(BASE/'results/verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
assert result['passed']
