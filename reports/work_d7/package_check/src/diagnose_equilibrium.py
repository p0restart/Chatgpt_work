"""Stricter local equilibrium diagnostics on four predeclared frozen cases."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .core import simulate, synthetic_model_from_config, check_controls
from .game_solver import ResponseProblem, local_best_response, observed_gaps, response
from .experiments import write_json

CASES=['seed11_separated_B1.2','seed22_separated_B1.2','seed33_separated_B1.2','seed33_business_cost_B0.6']


def residuals(m,u,T,steps):
    result={}
    for p in ('D','A'):
        pr=ResponseProblem(m,*u,T,steps,p)
        _,g=pr.value_gradient(pr.initial)
        result[p]=pr.projected_residual(pr.initial,g)
    return result


def solve(m,u,T,steps,seed,out):
    trace=[]
    for i in range(41):
        gap,d,a=observed_gaps(m,u,T,steps,seed+i*10,starts=1)
        res=residuals(m,u,T,steps)
        distance=max(float(np.max(np.abs(d[j]-u[j]))) for j in (1,2))
        distance=max(distance,float(np.max(np.abs(a[0]-u[0]))))
        passed=(max(gap['relative_D'],gap['relative_A'])<=1e-7 and max(res.values())<=1e-4 and distance<=1e-3
                and all(gap[p]['all_starts_success'] for p in ('D','A')))
        entry=dict(iteration=i,**gap,incumbent_residual=res,response_distance=distance,passed=passed,
                   controls=[x.tolist() for x in u])
        trace.append(entry)
        with (out/'trace.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        print(out.name,i,max(gap['relative_D'],gap['relative_A']),max(res.values()),flush=True)
        if passed or i==40:break
        u=(u[0],d[1],d[2])
        u,_=response(m,u,T,steps,'A',seed+i*10+2,1)
    write_json(out/'trace.json',trace)
    write_json(out/'controls.json',[x.tolist() for x in u])
    return u,trace[-1]


def strong_audit(m,u,T,steps,seed,out,label):
    gap,_,_=observed_gaps(m,u,T,steps,seed,starts=12)
    sparse=[]
    for p in ('D','A'):
        pr=ResponseProblem(m,*u,T,steps,p)
        base=pr.value_gradient(pr.initial)[0]
        best=gap[p]['objective']
        for j in range(pr.width):
            v=np.zeros((pr.K,pr.width));v[:,j]=min(1,pr.capacity/pr.weights[j])
            pu=pr.schedules(v.ravel())
            pp=ResponseProblem(m,*pu,T,steps,p)
            opt,tr=local_best_response(pp,seed+j,starts=1)
            val,g=pp.value_gradient(opt)
            best=min(best,val)
            sparse.append(dict(player=p,channel=j,raw=tr,value=val,
                               residual=pp.projected_residual(opt,g),violation=pp.violation(opt)))
        gap[f'strong_raw_improvement_{p}']=base-best
        gap[f'strong_relative_{p}']=(base-best)/(1+abs(base))
    gap['sparse']=sparse
    gap['global_gap_upper_bound_unknown']=True
    write_json(out/f'{label}.json',gap)
    return gap


def mechanism(m,u,T,steps,out):
    pr=ResponseProblem(m,*u,T,steps,'D');base,gradient=pr.value_gradient(pr.initial)
    g=gradient.reshape(pr.K,pr.width); a,s,r=u;dt=T/pr.K
    sim=simulate(m,*u,T,steps)
    highspread=int(m.beta.sum(axis=1).argmax());highvalue=int(m.q.argmax())
    rows=[];transfers=[]
    for k in range(pr.K):
        for i in range(m.n):
            for kind,col,cost,weight,control in [('s',i,dt*(m.h[i]+m.c_s[i]*s[k,i]),m.b_s[i],s[k,i]),
                                                ('r',m.n+i,dt*m.c_r[i]*r[k,i],m.b_r[i],r[k,i])]:
                rows.append(dict(slot=k,node=i,kind=kind,control=control,q=m.q[i],out_strength=m.beta[i].sum(),
                                  x_slot_start=sim['states'][k*steps,i],gradient=g[k,col],
                                  direct_cost_derivative=cost,security_benefit_derivative=cost-g[k,col],
                                  net_benefit_per_capacity=-g[k,col]/weight,
                                  budget_slack=m.B-s[k]@m.b_s-r[k]@m.b_r))
        # Compare both directions without silently violating bounds.
        for src,dst in [(m.n+highvalue,highspread),(highspread,m.n+highvalue)]:
            v=pr.initial.reshape(pr.K,pr.width)
            step=min(1e-5,.1*v[k,src]*pr.weights[src],.1*(1-v[k,dst])*pr.weights[dst])
            if step<1e-10:continue
            direction=np.zeros_like(v);direction[k,src]=-1/pr.weights[src];direction[k,dst]=1/pr.weights[dst]
            candidate=(v+step*direction).ravel()
            val,_=pr.value_gradient(candidate)
            analytic=float(np.sum(g*direction));fd=(val-base)/step
            transfers.append(dict(slot=k,source=src,destination=dst,capacity_step=step,
                                  analytic=analytic,finite_difference=fd,error=abs(fd-analytic),
                                  violation=pr.violation(candidate),cost_change=val-base))
    pd.DataFrame(rows).to_csv(out/'marginals.csv',index=False)
    pd.DataFrame(transfers).to_csv(out/'transfers.csv',index=False)
    return dict(highspread=highspread,highvalue=highvalue,transfer_count=len(transfers),
                max_direction_error=max((x['error'] for x in transfers),default=0))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    write_json(out/'metadata.json',dict(status='RUNNING',cases=CASES,relative_target=1e-7,
                incumbent_residual_target=1e-4,model_change=False,global_certificate=False))
    start=time.perf_counter();summary=[]
    for name in CASES:
        source=Path('results/p3/fair01')/name;dest=out/name;dest.mkdir()
        cfg=yaml.safe_load((source/'config.yaml').read_text(encoding='utf-8'))
        m=synthetic_model_from_config(cfg);T=cfg['T'];steps=cfg['rk4_substeps_per_slot'];K=cfg['K']
        (dest/'config.yaml').write_text(yaml.safe_dump(cfg),encoding='utf-8')
        c=pd.read_csv(source/'Joint-dynamic_adaptive_attack/controls.csv')
        old=tuple(c.pivot(index='slot',columns='node',values=p).to_numpy() for p in ('a','s','r'))
        rng=np.random.default_rng(cfg['seed']+20261027)
        random=[rng.uniform(0,1,(K,m.n)) for _ in range(3)];random[0][:,~m.entry]=0
        random[0]*=np.minimum(1,m.A/(random[0]@m.d_a))[:,None]
        du=random[1]@m.b_s+random[2]@m.b_r
        for j in (1,2):random[j]*=np.minimum(1,m.B/du)[:,None]
        solutions=[]
        for label,initial in [('warm',old),('zero',tuple(np.zeros_like(x) for x in old)),('random',tuple(random))]:
            run=dest/label;run.mkdir();check_controls(m,*initial)
            u,last=solve(m,initial,T,steps,cfg['seed']+10000,run);solutions.append(u)
            summary.append(dict(case=name,initialization=label,iterations=last['iteration'],passed=last['passed'],
                                J_D=last['J_D'],J_A=last['J_A'],relative_D=last['relative_D'],relative_A=last['relative_A'],
                                residual_D=last['incumbent_residual']['D'],residual_A=last['incumbent_residual']['A']))
            pd.DataFrame(summary).to_csv(out/'summary.csv',index=False)
        stable=max(float(np.max(np.abs(solutions[i][j]-solutions[0][j]))) for i in (1,2) for j in range(3))
        oldaudit=strong_audit(m,old,T,steps,cfg['seed']+70000,dest,'old_strong_audit')
        newaudit=strong_audit(m,solutions[0],T,steps,cfg['seed']+80000,dest,'new_strong_audit')
        fine,_,_=observed_gaps(m,solutions[0],T,48,cfg['seed']+90000,starts=3)
        write_json(dest/'fine_audit.json',fine)
        mech=mechanism(m,solutions[0],T,48,dest)
        write_json(dest/'case_audit.json',dict(control_difference_across_initializations=stable,
                   old_relative_max=max(oldaudit['strong_relative_D'],oldaudit['strong_relative_A']),
                   new_relative_max=max(newaudit['strong_relative_D'],newaudit['strong_relative_A']),
                   fine_relative_max=max(fine['relative_D'],fine['relative_A']),**mech))
    write_json(out/'metadata.json',dict(status='COMPLETED',cases=CASES,seconds=time.perf_counter()-start,
                relative_target=1e-7,model_change=False,global_certificate=False))


if __name__=='__main__':main()
