"""Read archived histories only; no optimization or simulation."""
from pathlib import Path
import json,csv,shutil
out=Path(__file__).resolve().parent
root=out.parents[1]
hist=[]
for b in ['0.6','1.2','1.8']:
    source=root/f'paper/work_d7/results/static/B{b}/G/warm/trace.jsonl'
    target=out/'evidence'/f'B{b}_uniform_trace.jsonl'
    target.parent.mkdir(exist_ok=True)
    if source.exists(): shutil.copy2(source,target)
    hist.append([json.loads(line) for line in target.read_text().splitlines() if line.strip()])
rows=[]
for i in range(6):
    batch=[next(x for x in h if x['iteration']==i) for h in hist]
    eta=max(x[f'relative_{p}'] for x in batch for p in ['D','A'])
    residual=max(x['incumbent_residual'][p] for x in batch for p in ['D','A'])
    # Inspect archived keys before treating a field as a metric.
    dist=max(x['distance'] for x in batch)
    rows.append([i,eta,residual,dist])
with (out/'evidence/iteration_summary.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['update','max_eta','max_stat','max_dist']);w.writerows(rows)
print(rows)
