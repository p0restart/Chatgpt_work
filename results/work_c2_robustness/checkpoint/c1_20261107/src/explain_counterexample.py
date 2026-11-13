"""Cross-evaluate existing strict defenses against both existing strict attacks."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .core import simulate, synthetic_model_from_config
from .game_solver import response
from .experiments import write_json

parser=argparse.ArgumentParser()
parser.add_argument('--equilibrium-root',default='results/equilibrium_audit/run01')
parser.add_argument('--counterexample-root',default='results/equilibrium_audit/counterexample01')
args=parser.parse_args()
case='seed33_business_cost_B0.6'
out=Path(args.counterexample_root)
cfg=yaml.safe_load(Path(f'results/p3/fair01/{case}/config.yaml').read_text())
m=synthetic_model_from_config(cfg)
j=tuple(np.array(x) for x in json.loads((Path(args.equilibrium_root)/case/'warm/controls.json').read_text()))
r=tuple(np.array(x) for x in json.loads((out/'controls.json').read_text()))
rows=[]
for d,du in [('Joint',j),('Recovery',r)]:
    for a,au in [('Joint',j),('Recovery',r)]:
        sim=simulate(m,au[0],du[1],du[2],cfg['T'],48)
        rows.append(dict(defense=d,attack=a,J_D=sim['J_D'],J_A=sim['J_A']))
pd.DataFrame(rows).to_csv(out/'cross_evaluation.csv',index=False)
_,info=response(m,(j[0],r[1],r[2]),cfg['T'],48,'D',101001,3)
write_json(out/'recovery_start_joint_response.json',info)
print(pd.DataFrame(rows).to_string(index=False))
