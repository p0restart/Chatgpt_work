"""D7 execution adapter: D5 run_budget with audited input/event/seed substitutions."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from paper.work_d5.analysis.run_replanning import *
BASE=ROOT/'paper/work_d7'
EVENT_ALPHA=.5
def run_budget(run, B, b):
    start=time.perf_counter(); out=run.out/f'B{B}';out.mkdir()
    source=BASE/f'results/static/B{B}'
    mpre=load_model(source/'model.json'); old=load_controls(source/'G_controls.json')
    mpost=replace(mpre,alpha=np.array([EVENT_ALPHA,.25,0,0,0,0]))
    dump_model(out/'model_pre.json',mpre);dump_model(out/'model_post.json',mpost)
    prefix=simulate(mpre,*(v[:3] for v in old),5,48)
    xevent=prefix['states'][-1].copy();sub=replace(mpost,x0=xevent)
    write_json(out/'common_prefix.json',dict(x_event=xevent.tolist(),parts=prefix['parts'],
        J_D=prefix['J_D'],J_A=prefix['J_A'],controls=[v[:3].tolist() for v in old]))
    run.context=dict(B=B,evaluation='E1',method='E1_generator',update=0)
    tail=tuple(v[3:].copy() for v in old)
    e1folder=out/'E1_generation';e1folder.mkdir()
    e1,attackpass=run.unilateral(sub,tail,'A',20261114+1000*b+100,e1folder,strong=True)
    evaluations={'E0':np.tile([.4,.4,0,0,0,0],(3,1)), 'E1':e1[0].copy()}
    write_json(out/'frozen_attacks.json',{k:v.tolist() for k,v in evaluations.items()})
    passed=attackpass
    for e,(ename,attack) in enumerate(evaluations.items()):
        for k in range(3):
            for node in range(6):
                run.attacks.append(dict(B=B,evaluation=ename,slot=k+3,node=node,a_actual=attack[k,node],
                    source='uniform' if ename=='E0' else 'local_response_to_P'))
        values={}
        for method in ('P','G','R'):
            run.context=dict(B=B,evaluation=ename,method=method,update=-1)
            u=[v.copy() for v in old];u[0][3:]=attack
            x=xevent.copy();warm=tail;ok=True
            for j in range(3):
                if method=='P':
                    break
                run.context=dict(B=B,evaluation=ename,method=method,update=j)
                folder=out/f'{ename}_{method}'/f'update{j}';folder.mkdir(parents=True)
                model=replace(mpost,x0=x.copy());dump_model(folder/'model_restart.json',model)
                seed=20261114+1000*b+100*e+10*j
                if method=='G':
                    plan,taskpass=run.game(model,warm,seed,folder,j)
                else:
                    observed=old[0][2] if j==0 else attack[j-1]
                    prediction=np.tile(observed,(3-j,1))
                    warm=(prediction,warm[1],warm[2])
                    plan,taskpass=run.unilateral(model,warm,'D',seed,folder,j)
                run.tasks.append(dict(**run.context,passed=taskpass,absolute_time=(3+j)*DT,K=3-j))
                run.save()
                if not taskpass:
                    ok=False;passed=False;break
                u[1][3+j],u[2][3+j]=plan[1][0],plan[2][0]
                sim=simulate(model,attack[j:j+1],plan[1][:1],plan[2][:1],DT,48)
                x=sim['states'][-1].copy();warm=tuple(v[1:].copy() for v in plan)
                if time.perf_counter()-start>1800:
                    write_json(out/'timeout.json',dict(status='GROUP_TIME_LIMIT',seconds=time.perf_counter()-start))
                    run.save();return False
            if not ok:
                write_json(out/f'{ename}_{method}_failed.json',dict(status='NUMERICAL_FAIL',
                    reason='No qualified decision; trajectory stopped; no fallback counted'))
                continue
            run.context=dict(B=B,evaluation=ename,method=method,update=-1,phase='execution_evaluation')
            ts=time.perf_counter();sims={H:execute(mpre,mpost,u,H) for H in (48,96,192)}
            run.timing.append(dict(**run.context,item='fixed_execution_reintegration_total',seconds=time.perf_counter()-ts))
            primary=sims[48];err=0.
            for H in (96,192):
                fine=sims[H]
                err=max(err,float(np.max(abs(primary['states']-fine['states'][::H//48]))),
                    max(abs(primary['parts'][p]-fine['parts'][p]) for p in PARTS),
                    max(abs(a-bb) for a,bb in zip(objective(primary['parts']),objective(fine['parts']))))
            state_error=max(0.,float(-primary['states'].min()),float(primary['states'].max()-1))
            check_controls(mpre,*u)
            violation=max(0.,float((u[1]@mpre.b_s+u[2]@mpre.b_r-B).max()),
                float((u[0]@mpre.d_a-mpre.A).max()),max(float((-v).max()) for v in u),
                max(float((v-1).max()) for v in u),float(abs(u[0][:,~mpre.entry]).max()))
            for check,value,threshold in [('reintegration',err,1e-6),('state_domain',state_error,1e-10),
                    ('continuity',primary['continuity'],1e-12),('control_violation',violation,1e-10)]:
                run.quality.append(dict(**run.context,check=check,value=value,threshold=threshold,passed=value<=threshold))
                passed=passed and value<=threshold
            for k in range(6):
                use=float(u[1][k]@mpre.b_s+u[2][k]@mpre.b_r)
                for node in range(6):
                    run.executed.append(dict(B=B,evaluation=ename,method=method,slot=k,node=node,
                        t_start=k*DT,t_end=(k+1)*DT,a_actual=u[0][k,node],s=u[1][k,node],r=u[2][k,node],
                        resource_use=use,budget_slack=B-use,alpha0=.25 if k<3 else EVENT_ALPHA))
            for H,sim in sims.items():
                for t,state in zip(sim['times'],sim['states']):
                    run.trajectories.append(dict(B=B,evaluation=ename,method=method,H=H,t=t,
                        **{f'x{i}':float(state[i]) for i in range(6)}))
                pre=sim['slot_costs'][2]
                for period,parts in [('pre',pre),('post',{p:sim['parts'][p]-pre[p] for p in PARTS}),('full',sim['parts'])]:
                    jd,ja=objective(parts)
                    run.objectives.append(dict(B=B,evaluation=ename,method=method,H=H,period=period,
                        J_D=jd,J_A=ja,**parts))
                    if H==48:
                        values[(method,period)]=jd
                csv(out/f'{ename}_{method}_cumulative_costs_H{H}.csv',
                    [dict(slot=k,t_end=(k+1)*DT,**p) for k,p in enumerate(sim['slot_costs'])])
            write_json(out/f'{ename}_{method}_executed.json',[v.tolist() for v in u])
            print('EXECUTED',B,ename,method,objective(primary['parts'])[0],flush=True)
            run.save()
        if all((m,'full') in values for m in ('P','G','R')):
            for period in ('post','full'):
                jp,jg,jr=(values[(m,period)] for m in ('P','G','R'))
                run.comparisons.append(dict(B=B,evaluation=ename,period=period,J_D_P=jp,J_D_G=jg,J_D_R=jr,
                    delta_P_to_G=jp-jg,delta_R_to_G=jr-jg,
                    percent_P_to_G=100*(jp-jg)/jp,percent_R_to_G=100*(jr-jg)/jr))
    # Fairness from saved actual schedules, including the identical prefix.
    for ename in evaluations:
        arrays=[load_controls(out/f'{ename}_{method}_executed.json') for method in ('P','G','R')
            if (out/f'{ename}_{method}_executed.json').exists()]
        fair=len(arrays)==3 and all(np.array_equal(arrays[0][0],a[0]) for a in arrays[1:])
        fair=fair and all(all(np.array_equal(arrays[0][v][:3],a[v][:3]) for v in (1,2)) for a in arrays[1:])
        run.quality.append(dict(B=B,evaluation=ename,check='common_attack_and_prefix',passed=fair))
        passed=passed and fair
    write_json(out/'budget_gate.json',dict(passed=bool(passed),seconds=time.perf_counter()-start,
        decision='EXPANSION_ALLOWED' if passed else 'STOP_NO_EXPANSION'))
    run.save();return bool(passed)


def main():
    global EVENT_ALPHA
    ap=argparse.ArgumentParser()
    ap.add_argument('--budget',type=float,required=True)
    ap.add_argument('--no-event',action='store_true')
    args=ap.parse_args()
    B=args.budget; b=[1.2,.6,1.8].index(B)
    EVENT_ALPHA=.25 if args.no_event else .5
    assert (BASE/f'results/static/B{B}/static_gate.json').exists()
    if b:
        pilot=BASE/'results/rolling_event_B1.2/B1.2/budget_gate.json'
        assert pilot.exists() and json.loads(pilot.read_text())['passed']
    if args.no_event: assert B==1.2
    out=BASE/f'results/rolling_{"control" if args.no_event else "event"}_B{B}'
    out.mkdir(exist_ok=False)
    write_json(out/'environment.json',dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),argv=sys.argv,event_alpha=EVENT_ALPHA,source_hash=sha(__file__)))
    run=Run(out)
    try:
        good=run_budget(run,B,b)
        if not good: raise RuntimeError('D7 rolling numerical gate failed')
    except Exception as exc:
        run.save();write_json(out/'FAILED.json',dict(error=repr(exc)));raise
    finally: gs.local_best_response=run.original_br

if __name__=='__main__': main()
