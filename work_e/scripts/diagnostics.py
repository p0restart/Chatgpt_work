"""Read-only Work E diagnostics of the frozen D7 game (all outputs in work_e)."""
from pathlib import Path
import sys, json, time, hashlib, platform, argparse, os
from dataclasses import asdict
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import numpy as np
import scipy
import pandas as pd
from scipy.optimize import linprog
from src.core import Model, validate_model, check_controls, simulate
from src.game_solver import ResponseProblem

OUT = Path(os.environ.get('WORK_E_OUTPUT',str(ROOT/'work_e')))
SEED = 20261115
T = 10.

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)), encoding='utf-8')

def load():
    d = json.loads((ROOT/'paper/work_d7/results/static/B1.2/model.json').read_text(encoding='utf-8'))
    m = Model(**{k: np.array(v, dtype=bool if k=='entry' else float) if isinstance(v,list) else v for k,v in d.items()})
    validate_model(m)
    pair = tuple(np.array(v) for v in json.loads((ROOT/'paper/work_d7/results/static/B1.2/G_controls.json').read_text(encoding='utf-8')))
    return m,pair

def pack(pair):
    a,s,r=pair
    return np.r_[np.c_[s,r].ravel(),a[:,:2].ravel()]

def unpack(z):
    K=len(z)//14
    u=z[:12*K].reshape(K,12)
    a=np.zeros((K,6)); a[:,:2]=z[12*K:].reshape(K,2)
    return a,u[:,:6].copy(),u[:,6:].copy()

def fg(m,z,H=48):
    pair=unpack(z)
    vals=[];grads=[]
    # Perturbed joint points can be outside the capacity polytope. The smooth
    # polynomial objective extension is evaluated by perturbing the response
    # vector from a feasible opponent baseline, then replacing the opponent.
    _,base=load_cached()
    K=len(pair[0])
    base=base if len(base[0])==K else tuple(np.repeat(x,2,axis=0) for x in base)
    for player in ('D','A'):
        p=ResponseProblem(m,*base,T,H,player)
        p.a,p.s,p.r=[x.copy() for x in pair]
        v=np.c_[pair[1],pair[2]].ravel() if player=='D' else pair[0][:,:2].ravel()
        value,g=p.value_gradient(v)
        vals.append(value);grads.append(g)
    return np.array(vals),np.concatenate(grads)

_CACHE=None
def load_cached():
    global _CACHE
    if _CACHE is None: _CACHE=load()
    return _CACHE

def jacobian(m,z,eps=1e-4,H=48):
    start=time.perf_counter()
    J=np.empty((len(z),len(z)))
    for j in range(len(z)):
        e=np.zeros_like(z);e[j]=eps
        J[:,j]=(fg(m,z+e,H)[1]-fg(m,z-e,H)[1])/(2*eps)
    return J,time.perf_counter()-start

def points(m,pair):
    K=len(pair[0]);rng=np.random.default_rng(SEED)
    ans={'interior_uniform':pack((np.tile([.2,.2,0,0,0,0],(K,1)),np.full((K,6),.04),np.full((K,6),.04))),
         'saved_candidate':pack(pair)}
    for name,duse,ause in [('near_capacity',.999,.999),('random_allocation',.65,.7)]:
        d=rng.uniform(.1,1,(K,12));d*= (m.B*duse/d.sum(axis=1))[:,None]
        a=rng.uniform(.1,1,(K,2));a*= (m.A*ause/a.sum(axis=1))[:,None]
        ans[name]=np.r_[d.ravel(),a.ravel()]
    # Large transmission at low defense, still strictly interior.
    ans['low_defense_high_attack']=pack((np.tile([.395,.395,0,0,0,0],(K,1)),np.full((K,6),.001),np.full((K,6),.001)))
    return ans

def feasibility(m,z):
    pair=unpack(z);check_controls(m,*pair)
    a,s,r=pair
    return dict(defense_usage=(s+r).sum(axis=1).tolist(),attack_usage=a.sum(axis=1).tolist(),box_min=float(z.min()),box_max=float(z.max()))

def line_radius(m,z,v):
    """Symmetric feasible radius along v, all box and budget inequalities."""
    K=len(z)//14;C=np.zeros((2*K,len(z)))
    for k in range(K): C[k,12*k:12*(k+1)]=1; C[K+k,12*K+2*k:12*K+2*(k+1)]=1
    margins=np.r_[z,1-z,np.r_[np.full(K,m.B),np.full(K,m.A)]-C@z]
    slopes=np.abs(np.r_[v,-v,C@v]);active=slopes>1e-10
    return float(max(0,np.min(margins[active]/slopes[active])))

def run():
    OUT.mkdir(exist_ok=True);(OUT/'results').mkdir(exist_ok=True)
    if (OUT/'results/diagnostics_completed.json').exists():
        raise FileExistsError('Completed diagnostics exist; set WORK_E_OUTPUT to a fresh project subdirectory')
    m,pair=load_cached();ps=points(m,pair)
    # Fingerprint all original papers/results and core sources before any work.
    tracked=[ROOT/'AGENTS.md',ROOT/'DECISIONS.md',ROOT/'reviews/APPROVAL_LOG.md',ROOT/'02_MODEL_SPEC.md']
    tracked += list((ROOT/'src').glob('*.py'))
    for folder in ['paper/work_d7','paper/work_d8_1','paper/work_d8_2']:
        tracked += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    dump(OUT/'source_manifest.json',hashes)
    dump(OUT/'run_config.json',dict(seed=SEED,T=T,K=6,H=48,steps=[1e-3,1e-4,1e-5],python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),model=asdict(m),points={k:unpack(v) for k,v in ps.items()}))
    rows=[]
    for name,z in ps.items():
        print('START',name,flush=True)
        feas=feasibility(m,z);t=time.perf_counter();vals,g=fg(m,z);gradient_seconds=time.perf_counter()-t
        # Directional central differences entirely feasible at interior points;
        # saved boundary candidate uses its feasible-line directions below.
        rng=np.random.default_rng(SEED);directions=[]
        if name=='saved_candidate':
            # Two-sided directions on the relative interior of the active face:
            # hold near-zero/near-one variables fixed, and conserve each budget.
            for block,width in [(0,12),(72,2)]:
                for k in range(6):
                    inds=block+k*width+np.arange(width)
                    free=inds[(z[inds]>1e-5)&(z[inds]<1-1e-5)]
                    if len(free)>=2:
                        v=np.zeros_like(z);v[free[0]]=1/np.sqrt(2);v[free[1]]=-1/np.sqrt(2);directions.append(v)
        else:
            for block,dim in [(0,72),(72,12)]:
                v=np.zeros_like(z);v[block:block+dim]=rng.normal(size=dim);v/=np.linalg.norm(v);directions.append(v)
        checks=[]
        for v in directions:
            player=0 if np.any(v[:72]) else 1
            radius=line_radius(m,z,v)
            for eps in (1e-3,1e-4,1e-5):
                step=min(eps,.2*radius)
                if step<1e-10:continue
                plus,minus=fg(m,z+step*v)[0],fg(m,z-step*v)[0]
                fd=(plus[player]-minus[player])/(2*step)
                checks.append(dict(player=player,step=step,analytic=float(g@v),finite_difference=fd,error=abs(fd-g@v),feasible_radius=radius))
        J,seconds=jacobian(m,z);D=(J[:72,:72]+J[:72,:72].T)/2;A=(J[72:,72:]+J[72:,72:].T)/2;H=(J+J.T)/2
        eig_start=time.perf_counter();ed,vd=np.linalg.eigh(D);ea,va=np.linalg.eigh(A);eh,vh=np.linalg.eigh(H);eig_seconds=time.perf_counter()-eig_start
        cross=H[:72,72:]
        row=dict(point=name,H_steps=48,fd_step=1e-4,J_D=vals[0],J_A=-vals[1],lambda_D=ed[0],lambda_A=ea[0],lambda_H=eh[0],cross_norm=np.linalg.norm(cross,2),D_asymmetry=np.max(abs(J[:72,:72]-J[:72,:72].T)),A_asymmetry=np.max(abs(J[72:,72:]-J[72:,72:].T)),gradient_max_error=max(c['error'] for c in checks),gradient_seconds=gradient_seconds,hessian_seconds=seconds,eigen_seconds=eig_seconds)
        rows.append(row)
        np.savez(OUT/f'results/{name}.npz',z=z,J=J,D=D,A=A,H=H,ed=ed,ea=ea,eh=eh,vd=vd,va=va,vh=vh)
        dump(OUT/f'results/{name}.json',dict(metrics=row,feasibility=feas,gradient_checks=checks))
        pd.DataFrame(rows).to_csv(OUT/'E3_experiment_results.csv',index=False)
        print(row,flush=True)
    dump(OUT/'results/diagnostics_completed.json',dict(completed=True,points=len(rows)))

def benchmark():
    m,pair=load_cached();z=points(m,pair)['interior_uniform'];start=time.perf_counter()
    for _ in range(3):vals,g=fg(m,z)
    print(dict(joint_gradient_seconds=(time.perf_counter()-start)/3,values=vals.tolist(),norm=float(np.linalg.norm(g))),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['benchmark','run']);args=ap.parse_args()
    benchmark() if args.mode=='benchmark' else run()
