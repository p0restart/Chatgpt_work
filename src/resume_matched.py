"""Resume only a clean wall-time boundary; never retry failed G1-C1 cases."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time
import yaml
from .matched_mechanism import run_case,summarize
from .experiments import write_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);args=parser.parse_args()
    out=Path(args.root);meta=json.loads((out/'metadata.json').read_text())
    if meta['status']!='STOPPED_AT_GROUP_BOUNDARY_30MIN':
        raise ValueError('Only a clean time boundary may resume; failed or running cases are not retried')
    for name,digest in meta['source_hashes'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Input changed: {name}')
    gate=json.loads((out/'pilot_gate.json').read_text())
    if not gate['passed']:raise ValueError('Pilot did not pass')
    rows=[json.loads(p.read_text()) for p in sorted(out.glob('seed*/case_audit.json'))]
    if not all(r['numerical_pass'] for r in rows):raise ValueError('A previous case failed')
    design=yaml.safe_load(Path('configs/proposed_mechanism_identification.yaml').read_text(encoding='utf-8'))
    base=yaml.safe_load(Path(design['base_config']).read_text(encoding='utf-8'))
    previous_seconds=meta['seconds'];start=time.perf_counter()
    meta.setdefault('segments',[]).append(dict(resumed_at=datetime.now(timezone.utc).isoformat(),
        cases_at_start=len(rows),launcher_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    meta['status']='RUNNING_EXPANSION';write_json(out/'metadata.json',meta)
    groups=[(11,1.2)]+[(s,b) for s in design['seeds'] for b in design['B_values'] if (s,b)!=(11,1.2)]
    for index,(seed,budget) in enumerate(groups):
        existing=[r for r in rows if (r['seed'],r['B'])==(seed,budget)]
        if len(existing)==4:continue
        if existing:raise ValueError('Incomplete group: manual inspection required')
        group=[]
        for outgoing in ('equal','unequal'):
            for value in ('high_at_node2','high_at_node3'):
                cfg={**base,'seed':seed,'B':budget}
                row=run_case(cfg,design,outgoing,value,out/f'seed{seed}_B{budget}_{outgoing}_{value}')
                group.append(row);rows.append(row);summarize(out,rows)
        meta.update(completed_cases=len(rows),seconds=previous_seconds+time.perf_counter()-start)
        if not all(r['numerical_pass'] for r in group):
            meta['status']='NUMERICAL_GATE_FAILED';break
        if time.perf_counter()-start>1800 and index<len(groups)-1:
            meta['status']='STOPPED_AT_GROUP_BOUNDARY_30MIN';break
        write_json(out/'metadata.json',meta)
    else:meta['status']='COMPLETED'
    write_json(out/'metadata.json',meta);print(json.dumps(meta),flush=True)


if __name__=='__main__':main()
