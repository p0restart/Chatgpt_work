"""Original SLSQP interface: feasible incumbents only, never global certificates."""
from common import ROOT,OUT,read,dump,F,frozen,repair,evaluate
import sys,time
sys.path.insert(0,str(ROOT))
import numpy as np
from src.core import Model,simulate
from src.game_solver import ResponseProblem,local_best_response
def search(player):
    model,z=frozen();m=Model(**{k:np.array(v,dtype=bool if k=='entry' else float) if isinstance(v,list) else v for k,v in model.items()})
    zz=np.array([float(v) for v in z]);ud=zz[:72].reshape(6,12);aa=np.zeros((6,6));aa[:,:2]=zz[72:].reshape(6,2)
    pair=(aa,ud[:,:6],ud[:,6:]);pr=ResponseProblem(m,*pair,10,48,player)
    start=time.perf_counter();v,raw=local_best_response(pr,seed=2026111502+(player=='D'),starts=3)
    cap=F(float(model['B'] if player=='D' else model['A']));width=12 if player=='D' else 2
    feasible=repair(v,cap,width)
    u=feasible if player=='D' else z[:72];a=feasible if player=='A' else z[72:]
    validated=evaluate(model,u,a,192)
    obj=dict(player=player,seed=2026111502+(player=='D'),starts=3,H_search=48,H_validation=192,seconds=time.perf_counter()-start,raw=raw,strict_feasible_response=[str(x) for x in feasible],strict_fixed_opponent=[str(x) for x in (z[72:] if player=='D' else z[:72])],validated=validated,global_optimality_claim=False)
    dump(OUT/f'results/heuristic_{player}.json',obj)
    # Fixed repaired response trajectories retain original numerical outputs;
    # their values are heuristic data, distinct from outward ODE enclosures.
    nr=np.array([float(x) for x in u]).reshape(6,12);ar=np.zeros((6,6));ar[:,:2]=np.array([float(x) for x in a]).reshape(6,2)
    sim=simulate(m,ar,nr[:,:6],nr[:,6:],10,48)
    import pandas as pd
    pd.DataFrame(dict(time=sim['times'],**{f'x{i}':sim['states'][:,i] for i in range(6)})).to_csv(OUT/f'results/heuristic_{player}_states.csv',index=False)
    dump(OUT/f'results/heuristic_{player}_controls.json',dict(a=ar.tolist(),s=nr[:,:6].tolist(),r=nr[:,6:].tolist(),slot_defense=(nr[:,:6]+nr[:,6:]).sum(axis=1).tolist(),slot_attack=ar.sum(axis=1).tolist()))
    return obj
if __name__=='__main__':
    player=sys.argv[1];print(search(player)['validated'],flush=True)
