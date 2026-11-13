"""Read-only history audit and immutable C1 checkpoint for Work C2."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from src.core import Model, simulate

ROOT = Path('results/work_c2_robustness')
EXPECTED = {'src/core.py': 'ef2c675252d5fc8e00bc7103dd542a40bbf9c7714412207dd4e0b20966859419',
            'src/game_solver.py': '8a5469467d5028077f6b83f7c9bb2dde5be6e0ff46790c07d252f0d70dbd1d87'}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, x):
    p.write_text(json.dumps(x, indent=2, allow_nan=False), encoding='utf-8')

def main():
    checkpoint = ROOT/'checkpoint'/'c1_20261107'
    checkpoint.mkdir(exist_ok=False)
    actual = {p: sha(p) for p in EXPECTED}
    write(checkpoint/'version_check.json', dict(expected=EXPECTED, actual=actual, match=actual == EXPECTED))
    if actual != EXPECTED:
        raise RuntimeError('C1 source mismatch: no calculation permitted')
    paths = sorted(set([p for folder in ('src', 'tests', 'configs') for p in Path(folder).rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts] +
                       [Path(p) for p in ('02_MODEL_SPEC.md', '04_EXPERIMENT_PROTOCOL.md',
                        'DECISIONS.md', 'reviews/APPROVAL_LOG.md', 'reports/MATCHED_MECHANISM_PROTOCOL.md',
                        'reports/WORK_C2_ROBUSTNESS_PROTOCOL.md', 'reviews/G1_WORK_C2_submission.md',
                        'handoffs/C1_fix_report.md', 'handoffs/C2_prepare.py')]))
    manifest = {}
    for p in paths:
        target = checkpoint/p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        manifest[p.as_posix()] = sha(p)
    for label, args in [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--short']),
                        ('diff', ['diff', '--', 'src/core.py', 'src/game_solver.py'])]:
        result = subprocess.run(['git', *args], capture_output=True, text=True, check=True)
        (checkpoint/f'git_{label}.txt').write_text(result.stdout, encoding='utf-8')
    write(checkpoint/'manifest.json', manifest)
    write(checkpoint/'environment.json', dict(time_utc=datetime.now(timezone.utc).isoformat(),
          executable=sys.executable, python=sys.version, platform=platform.platform(), command=sys.argv,
          checkpoint_kind='file snapshot; not a new Git commit'))
    rows = []
    provenance = {}
    history = Path('results/matched_mechanism/run01')
    for seed, budget in [(11, .6), (33, 1.2), (11, 1.2)]:
        for letter, outgoing, value in [('A','equal','high_at_node2'), ('B','equal','high_at_node3'),
                                        ('C','unequal','high_at_node2'), ('D','unequal','high_at_node3')]:
            case = history/f'seed{seed}_B{budget}_{outgoing}_{value}'
            mp, cp = case/'model.json', case/'fine/controls.json'
            raw = json.loads(mp.read_text())
            m = Model(**{k: np.array(v) if isinstance(v, list) else v for k,v in raw.items()})
            u = tuple(np.array(v) for v in json.loads(cp.read_text()))
            sims = {h: simulate(m, *u, 10., h) for h in (48, 96)}
            for p in (mp, cp, case/'fine_audit.json', case/'case_audit.json'):
                provenance[p.as_posix()] = sha(p)
            gap = json.loads((case/'fine_audit.json').read_text())
            audit = json.loads((case/'case_audit.json').read_text())
            du = u[1]@m.b_s + u[2]@m.b_r
            rows.append(dict(seed=seed,B=budget,cell=letter,K=6,H=48,J_D=sims[48]['J_D'],
                             J_A=sims[48]['J_A'], gap_D_historical=gap['gap_D'], gap_A_historical=gap['gap_A'],
                             relative_D_historical=gap['relative_D'],relative_A_historical=gap['relative_A'],
                             historical_numerical_pass=audit['numerical_pass'],
                             integration_error=max(abs(sims[48][p]-sims[96][p]) for p in ('J_D','J_A')),
                             defense_binding_slots=int(np.sum(abs(du-m.B)<=1e-6)),
                             s2_mean=float(u[1][:,2].mean()),s3_mean=float(u[1][:,3].mean()),
                             r2_mean=float(u[2][:,2].mean()),r3_mean=float(u[2][:,3].mean()),
                             source=case.as_posix(), status='HISTORY_REINTEGRATED_NOT_RESOLVED'))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT/'tables/baseline_k6.csv', index=False)
    effects=[]
    for (seed,b), group in df.groupby(['seed','B']):
        j = group.set_index('cell').J_D
        effects.append(dict(seed=int(seed), B=float(b), K=6, H=48,
                            I_J=float((j.D-j.C)-(j.B-j.A)), status='BASELINE_ONLY'))
    write(ROOT/'tables/baseline_interactions.json', effects)
    write(ROOT/'logs/history_input_hashes.json', provenance)
    print(json.dumps(dict(checkpoint=str(checkpoint),baseline_cases=len(rows),interactions=effects)))

if __name__ == '__main__':
    main()
