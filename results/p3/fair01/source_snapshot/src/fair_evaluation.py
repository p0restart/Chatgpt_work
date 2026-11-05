"""Common full local attacker-response evaluation of saved final defenses.

Original alternating-pair records remain untouched; this produces a derived run.
"""
import argparse
import json
from pathlib import Path
import shutil
import time
import numpy as np
import pandas as pd
import yaml
from .core import synthetic_model_from_config, simulate
from .game_solver import response
from .experiments import METHODS, write_json, save_evaluation


def finalize(case,out):
    cfg=yaml.safe_load((case/'config.yaml').read_text(encoding='utf-8'))
    m=synthetic_model_from_config(cfg)
    folder=out/case.name; folder.mkdir()
    for name in ('config.yaml','model.json','edges.csv'):
        shutil.copy2(case/name,folder/name)
    rows=[]
    for method in METHODS:
        fixed=case/f'{method}_fixed_attack'
        shutil.copytree(fixed,folder/fixed.name)
        rows.append(json.loads((fixed/'summary.json').read_text()))
        source=case/f'{method}_adaptive_attack'
        if method in METHODS[:3]:
            shutil.copytree(source,folder/source.name)
            shutil.copy2(case/f'{method}_adaptive_response.json',folder/f'{method}_adaptive_response.json')
            rows.append(json.loads((source/'summary.json').read_text()))
            continue
        data=pd.read_csv(source/'controls.csv')
        controls=tuple(data.pivot(index='slot',columns='node',values=c).to_numpy() for c in ('a','s','r'))
        mode={'Isolation-only':'isolation','Recovery-only':'recovery'}.get(method,'joint')
        final,ai=response(m,controls,cfg['T'],cfg['rk4_substeps_per_slot'],'A',cfg['seed']+9000,3,mode)
        _,di=response(m,final,cfg['T'],cfg['rk4_substeps_per_slot'],'D',cfg['seed']+9001,3,mode)
        sim=simulate(m,*final,cfg['T'],cfg['rk4_substeps_per_slot'])
        gd=max(0.,sim['J_D']-di['objective'])
        # A is exactly the selected local response to this unchanged defense.
        ga=max(0.,-ai['objective']-sim['J_A'])
        gap=dict(gap_D=gd,gap_A=ga,relative_D=gd/(1+abs(sim['J_D'])),relative_A=ga/(1+abs(sim['J_A'])))
        gap['target_met']=max(gap['relative_D'],gap['relative_A'])<=.01
        gap['quality_met']=all(i['all_starts_success'] and i['residual']<=1e-4 and i['violation']<=1e-10 for i in (ai,di))
        write_json(folder/f'{method}_adaptive_response.json',ai)
        write_json(folder/f'{method}_defense_audit_response.json',di)
        row=save_evaluation(folder/source.name,m,cfg,final,method,'adaptive_attack',gap)
        row['candidate_J_D']=json.loads((source/'summary.json').read_text())['J_D']
        rows.append(row)
    pd.DataFrame(rows).to_csv(folder/'summary.csv',index=False)
    print(f'{case.name}: fair evaluation completed',flush=True)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    args=p.parse_args(); source=Path(args.source);out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter(); done=set();rows=[]
    write_json(out/'metadata.json',dict(status='RUNNING',source=str(source),
               scope='Derived full local attacker response; final defense frozen; original candidates retained'))
    while len(done)<27:
        for case in sorted(source.glob('seed*')):
            table=case/'summary.csv'
            if case.name in done or not table.exists(): continue
            try:
                ready=len(pd.read_csv(table))==12
            except pd.errors.EmptyDataError:
                ready=False
            if not ready: continue
            rows.extend(finalize(case,out));done.add(case.name)
            pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
        if time.perf_counter()-start>1800:
            raise TimeoutError('Fair evaluation 30 minute timeout; partial results preserved')
        if len(done)<27: time.sleep(2)
    write_json(out/'metadata.json',dict(status='COMPLETED',source=str(source),seconds=time.perf_counter()-start,
               scope='Full local attacker response to each final defense; restricted D-deviation audit'))


if __name__=='__main__':main()
