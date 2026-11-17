"""Small three-start rerun using unchanged strict_solve; final same-pair audits."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
from diagnostics import load,pack,dump,SEED,OUT
from src.matched_mechanism import strict_solve,control_distance
from src.game_solver import observed_gaps,ResponseProblem
from src.core import simulate,check_controls

def metrics(m,u,H=48):
    sim=simulate(m,*u,10,H)
    res={}
    for player in ('D','A'):
        p=ResponseProblem(m,*u,10,H,player);_,g=p.value_gradient(p.initial)
        res[player]=dict(violation=p.violation(p.initial),residual=p.projected_residual(p.initial,g))
    return sim,res

def save_fixed_outputs(folder,m,u):
    a,s,r=u
    pd.DataFrame([dict(slot=k,defense=float((s[k]+r[k]).sum()),attack=float(a[k].sum()),defense_capacity=m.B,attack_capacity=m.A,passed=bool((s[k]+r[k]).sum()<=m.B+1e-10 and a[k].sum()<=m.A+1e-10)) for k in range(len(a))]).to_csv(folder/'per_slot_budgets.csv',index=False)
    for H in (48,96):
        sim,_=metrics(m,u,H)
        pd.DataFrame(dict(time=sim['times'],**{f'x{i}':sim['states'][:,i] for i in range(6)})).to_csv(folder/f'states_H{H}.csv',index=False)
        dump(folder/f'objectives_H{H}.json',dict(J_D=sim['J_D'],J_A=sim['J_A'],parts=sim['parts']))

def main():
    m,saved=load();K=6;rng=np.random.default_rng(SEED)
    a=np.zeros((K,6));a[:,:2]=.4
    uniform=(a,np.full((K,6),m.B/12),np.full((K,6),m.B/12))
    random=[rng.uniform(0,1,(K,6)) for _ in range(3)]
    random[0][:,2:]=0;random[0]*=(m.A/random[0].sum(axis=1))[:,None]
    factor=m.B/(random[1]+random[2]).sum(axis=1)
    random[1]*=factor[:,None];random[2]*=factor[:,None]
    folder=OUT/'results/new_multistart';folder.mkdir(exist_ok=True)
    summary=OUT/'results/new_multistart_summary.csv'
    rows=pd.read_csv(summary).to_dict('records') if summary.exists() else []
    solutions=[tuple(np.array(x) for x in json.loads((folder/r['path']/'controls.json').read_text())) for r in rows]
    for idx,(name,u) in enumerate([('uniform',uniform),('zero',tuple(np.zeros_like(x) for x in saved)),('random',tuple(random))]):
        if name in [r['path'] for r in rows]:
            # Continue only after completed optimization and audits; never rerun
            # an already stored path merely because a later CSV export failed.
            assert (folder/name/'final_same_pair_audits.json').exists()
            traces=[json.loads(line) for line in (folder/name/'trace.jsonl').read_text().splitlines()]
            attempts=[]
            for tr in traces:
                for player in ('D','A'):attempts+=tr[player]['raw']
                attempts+=tr.get('sequential_attack',{}).get('raw',[])
            pd.DataFrame([dict(attempt_index=j,**{k:v for k,v in t.items() if k not in ('control','initial_control')}) for j,t in enumerate(attempts)]).to_csv(folder/name/'optimizer_attempts.csv',index=False)
            print('REUSED_COMPLETED_PATH',name,flush=True)
            save_fixed_outputs(folder/name,m,solutions[[r['path'] for r in rows].index(name)])
            continue
        check_controls(m,*u);dump(folder/f'initial_{name}.json',dict(seed=SEED+100*idx,controls=u))
        start=time.perf_counter();sol,last=strict_solve(m,u,10,48,SEED+100*idx,folder/name)
        elapsed=time.perf_counter()-start
        # Retain every optimizer attempt in strict trace. On abnormal exit stop,
        # do not silently select a different run to obtain a passing result.
        traces=[json.loads(line) for line in (folder/name/'trace.jsonl').read_text().splitlines()]
        attempts=[]
        for tr in traces:
            for player in ('D','A'): attempts+=tr[player]['raw']
            attempts+=tr.get('sequential_attack',{}).get('raw',[])
        all_success=all(t['success'] for t in attempts)
        sim,res=metrics(m,sol);sim96,res96=metrics(m,sol,96)
        audits={}
        for H in (48,96):
            gaps,dr,ar=observed_gaps(m,sol,10,H,SEED+1000+idx,starts=3)
            audits[str(H)]=gaps
        dump(folder/name/'final_same_pair_audits.json',audits)
        history=[pack(tuple(np.array(x) for x in tr['controls'])) for tr in traces]
        cycle=min([float(np.max(abs(history[-1]-h))) for h in history[:-2]] or [float('inf')])
        changes=[float(np.max(abs(b-a))) for a,b in zip(history[:-1],history[1:])]
        row=dict(path=name,seed=SEED+100*idx,iterations=last['iteration'],passed=last['passed'],all_iteration_optimizer_success=all_success,optimizer_attempts=len(attempts),J_D=sim['J_D'],J_A=sim['J_A'],gap_D=audits['48']['gap_D'],gap_A=audits['48']['gap_A'],relative_D=audits['48']['relative_D'],relative_A=audits['48']['relative_A'],incumbent_residual_D=res['D']['residual'],incumbent_residual_A=res['A']['residual'],max_violation=max(r['violation'] for r in res.values()),integration_error=max(abs(sim['J_D']-sim96['J_D']),abs(sim['J_A']-sim96['J_A']),np.max(abs(sim['states']-sim96['states'][::2]))),distance_saved=control_distance(sol,saved),seconds=elapsed,nonadjacent_cycle_distance=cycle,consecutive_change_max=max(changes or [0]),termination='registered_local_threshold' if last['passed'] else 'iteration_limit')
        rows.append(row);solutions.append(sol)
        pd.DataFrame(rows).to_csv(OUT/'results/new_multistart_summary.csv',index=False)
        pd.DataFrame([dict(attempt_index=j,**{k:v for k,v in t.items() if k not in ('control','initial_control')}) for j,t in enumerate(attempts)]).to_csv(folder/name/'optimizer_attempts.csv',index=False)
        print(row,flush=True)
        save_fixed_outputs(folder/name,m,sol)
        if not last['passed'] or not all_success:break
    distances=[dict(left=rows[i]['path'],right=rows[j]['path'],distance=control_distance(solutions[i],solutions[j])) for i in range(len(solutions)) for j in range(i)]
    dump(folder/'comparison.json',dict(distances=distances,completed=len(solutions)==3,unique_equilibrium_proven=False))
    # Historical evidence re-analysis, never labelled a fresh optimization.
    hist=[]
    for label in ('warm','zero','random'):
        p=ROOT/f'paper/work_d7/results/static/B1.2/G/{label}'
        last=json.loads((p/'last.json').read_text())
        u=tuple(np.array(x) for x in json.loads((p/'controls.json').read_text()))
        hist.append(dict(path=label,source=str(p.relative_to(ROOT)),iteration=last['iteration'],J_D=last['J_D'],J_A=last['J_A'],gap_D=last['gap_D'],gap_A=last['gap_A'],passed=last['passed'],distance_saved=control_distance(u,saved),evidence='historical_reanalysis'))
    pd.DataFrame(hist).to_csv(OUT/'results/historical_multistart.csv',index=False)

if __name__=='__main__':main()
