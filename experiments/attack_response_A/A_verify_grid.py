import json
import sys
from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
sys.path.insert(0, str(root/'A_source'))
from src.core import Model, simulate

cfg = json.loads((root/'A_run_config.json').read_text(encoding='utf-8'))
params = cfg['model']
model = Model(**{field.name: np.asarray(params[field.name]) if isinstance(params[field.name], list)
                 else params[field.name] for field in fields(Model)})
rows = pd.read_csv(root/'A_results.csv', float_precision='round_trip')
normal = rows[rows.label == 'C0']
coarse_controls = [normal[key].to_numpy().reshape(6, 2, 6).mean(axis=1) for key in ('a', 's', 'r')]
split_controls = [np.repeat(control, 2, axis=0) for control in coarse_controls]
base = simulate(model, *coarse_controls, cfg['T'], 48)
same_step = simulate(model, *coarse_controls, cfg['T'], 96)
split = simulate(model, *split_controls, cfg['T'], 48)
errors = {}
for name, coarser, stride, limit in (('K6_H48_vs_K12_H48', base, 2, 1e-6),
                                     ('K6_H96_vs_K12_H48', same_step, 1, 1e-12)):
    state_error = float(np.max(np.abs(coarser['states']-split['states'][::stride])))
    time_error = float(np.max(np.abs(coarser['times']-split['times'][::stride])))
    loss_error = abs(coarser['J_D']-split['J_D'])
    part_error = max(abs(coarser['parts'][key]-split['parts'][key])
                     for key in ('security', 'business', 'isolation', 'recovery', 'terminal_defense'))
    errors[name] = dict(state_error=state_error, time_error=time_error, loss_error=loss_error,
                        part_error=part_error, limit=limit, passed=max(state_error, time_error, loss_error, part_error) <= limit)
(root/'A_grid_bridge.json').write_text(json.dumps(errors, indent=2)+'\n', encoding='utf-8')
if not all(record['passed'] for record in errors.values()):
    raise SystemExit('fixed-control grid bridge failed')
print('Two fixed-control K6/K12 integration bridge checks passed')
