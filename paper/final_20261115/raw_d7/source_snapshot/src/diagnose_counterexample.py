"""Recheck the old negative comparison at matched solver precision."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .core import simulate, synthetic_model_from_config
from .game_solver import ResponseProblem, response, observed_gaps
from .experiments import write_json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--equilibrium-root',default='results/equilibrium_audit/run01')
    parser.add_argument('--output',default='results/equilibrium_audit/counterexample01')
    args=parser.parse_args()
    case='seed33_business_cost_B0.6'
    src=Path('results/p3/fair01')/case
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    cfg=yaml.safe_load((src/'config.yaml').read_text(encoding='utf-8'))
    m=synthetic_model_from_config(cfg);T=cfg['T'];steps=cfg['rk4_substeps_per_slot']
    data=pd.read_csv(src/'Recovery-only_adaptive_attack/controls.csv')
    u=tuple(data.pivot(index='slot',columns='node',values=p).to_numpy() for p in ('a','s','r'))
    for i in range(41):
        gap,d,_=observed_gaps(m,u,T,steps,77000+i,starts=2,mode='recovery')
        residual=[]
        for p in ('D','A'):
            pr=ResponseProblem(m,*u,T,steps,p,'recovery')
            _,g=pr.value_gradient(pr.initial)
            residual.append(pr.projected_residual(pr.initial,g))
        gap.update(iteration=i,incumbent_residual=residual,controls=[x.tolist() for x in u])
        with (out/'trace.jsonl').open('a') as f:f.write(json.dumps(gap)+'\n')
        if max(gap['relative_D'],gap['relative_A'])<=1e-7 and max(residual)<=1e-4:break
        u=(u[0],d[1],d[2]);u,_=response(m,u,T,steps,'A',88000+i,2,mode='recovery')
    final,_,_=observed_gaps(m,u,T,48,99000,starts=12,mode='recovery')
    write_json(out/'strong_fine_audit.json',final)
    joint=tuple(np.array(a) for a in json.loads((Path(args.equilibrium_root)/case/'warm/controls.json').read_text()))
    j=simulate(m,*joint,T,48);r=simulate(m,*u,T,48)
    write_json(out/'controls.json',[x.tolist() for x in u])
    result=dict(case=case,recovery_iterations=i,recovery_J_D=r['J_D'],joint_J_D=j['J_D'],
                joint_reduction_pct=100*(r['J_D']-j['J_D'])/r['J_D'],
                recovery_max_relative_improvement=max(final['relative_D'],final['relative_A']),
                recovery_incumbent_residual=max(residual),label='Matched precision local candidates; no global certificate')
    write_json(out/'comparison.json',result);print(result)


if __name__=='__main__':main()
