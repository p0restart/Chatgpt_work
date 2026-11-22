"""R2 fixed protocol. Run as a script from any directory."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
import pandas as pd
import scipy
from src.core import Model, simulate, check_controls
from src.game_solver import ResponseProblem, local_best_response

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/'code/input'
OUT = ROOT/'results'
K, T, H, SEED = 6, 10, 48, 20261114
zero = np.zeros((K, 6))
params = json.loads((INPUT/'B1.2_model.json').read_text())
m = Model(**{k: np.array(v) if isinstance(v, list) else v for k,v in params.items()})


def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2), encoding='utf8')


class StaticProblem(ResponseProblem):
    """Single capacity row; sum RK4 derivatives across the six tied slots."""
    def __init__(self, full):
        self.full = full
        self.K, self.width = 1, full.width
        self.weights, self.capacity = full.weights, full.capacity
        self.initial = full.initial[:self.width].copy()
        self.upper = np.ones(self.width)
        self.C = self.weights[None, :]

    def value_gradient(self, v):
        value, grad = self.full.value_gradient(np.tile(v, K))
        return value, grad.reshape(K, self.width).sum(axis=0)

    def schedules(self, v):
        return self.full.schedules(np.tile(v, K))


def solve(label, a, s, r, player, static=False):
    p = ResponseProblem(m, a, s, r, T, H, player)
    # Source routine uses initial, zero and seeded random. Start 1 uses half capacity.
    p.initial[:] = min(.5, .5*p.capacity/p.weights.sum())
    if static:
        p = StaticProblem(p)
    v, attempts = local_best_response(p, SEED, 3)
    save(label+'_solver.json', attempts)
    print(label, [t['status'] for t in attempts], flush=True)
    return p.schedules(v)


def run():
    nom = solve('nominal', zero, zero, zero, 'A')[0]
    frozen = OUT/'a_nom.json'
    if frozen.exists():
        np.testing.assert_allclose(json.loads(frozen.read_text()), nom, atol=1e-12, rtol=0)
        nom = np.array(json.loads(frozen.read_text()))
    else:
        save(frozen.name, nom.tolist())
    plans = {k: solve(k, nom, zero, zero, 'D', k=='S')[1:] for k in ('S','O')}
    old = pd.read_csv(INPUT/'fig4_controls.csv', float_precision='round_trip')
    old_attack = old.query("plan=='G'").a.to_numpy().reshape(K,6)
    for name in ('G','M','N'):
        df = old[old.plan==name].sort_values(['slot','asset_id'])
        plans[name] = tuple(df[col].to_numpy().reshape(K,6) for col in ('s','r'))
    historical = json.loads((INPUT/'verification.json').read_text())['plans']
    rows, trajectories, controls, checks = [], [], [], []
    for scene, names in [('A','GSOMN'),('B','GSO')]:
        for name in names:
            s,r = plans[name]
            a = nom if scene=='A' else solve('BR_'+name, zero,s,r,'A')[0]
            check_controls(m,a,s,r)
            sim = simulate(m,a,s,r,T,H)
            fine = simulate(m,a,s,r,T,4*H)
            parts = sim['parts']
            x = sim['states']
            action = sum(parts[k] for k in ('business','isolation','recovery'))
            rows.append(dict(scene=scene,plan=name,**parts,action=action,JD=sim['J_D'],JA=sim['J_A'],
                             Xq=x[-1]@m.q/m.q.sum(), **{f'x{i+1}':v for i,v in enumerate(x[-1])}))
            checks.append(dict(scene=scene,plan=name,JD_error=abs(sim['J_D']-fine['J_D']),
                               state_error=abs(x-fine['states'][::4]).max()))
            for k in range(K):
                for i in range(m.n):
                    controls.append((scene,name,k+1,i+1,a[k,i],s[k,i],r[k,i],a[k,i]*m.d_a[i],
                                     s[k,i]*m.b_s[i],r[k,i]*m.b_r[i]))
            for t,state in zip(sim['times'],x):
                trajectories.append([scene,name,t,*state])
    for name in 'GMN':
        rep = simulate(m,old_attack,*plans[name],T,H)
        p = rep['parts']
        values = [p['security'],sum(p[k] for k in ('business','isolation','recovery')),rep['J_D'],rep['states'][-1]@m.q/m.q.sum()]
        np.testing.assert_allclose(values,historical[name]['table_3_metrics'],rtol=0,atol=1e-10)
    pd.DataFrame(rows).to_csv(OUT/'metrics.csv',index=False)
    df = pd.DataFrame(controls,columns='scene plan slot asset a s r attack_use isolation_use recovery_use'.split())
    df.to_csv(OUT/'controls.csv',index=False)
    df.groupby(['scene','plan','slot'])[['attack_use','isolation_use','recovery_use']].sum().to_csv(OUT/'capacity.csv')
    pd.DataFrame(trajectories,columns=['scene','plan','time',*[f'x{i+1}' for i in range(6)]]).to_csv(OUT/'states.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'grid.csv',index=False)
    save('environment.json',dict(seed=SEED,T=T,K=K,H=H,refined_H=4*H,python=sys.version,platform=platform.platform(),
         numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,historical_GMN_replay='passed',
         sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [*INPUT.glob('*'),*(ROOT/'code/src').glob('*.py'),Path(__file__).resolve(),frozen]}))


if __name__ == '__main__':
    run()
