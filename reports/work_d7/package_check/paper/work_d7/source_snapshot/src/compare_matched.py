"""Compare two independently executed four-cell pilots, excluding wall-clock data."""
import argparse
import json
from pathlib import Path
import numpy as np
from .experiments import write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--repeat',required=True)
    args=p.parse_args();original=Path(args.original);repeat=Path(args.repeat)
    meta=json.loads((repeat/'metadata.json').read_text())
    if meta['status']!='COMPLETED':raise ValueError('Repeat has not completed')
    rows=[]
    for case in sorted(repeat.glob('seed*/case_audit.json')):
        name=case.parent.name
        for label in ('uniform','zero','random','fine'):
            left=json.loads((original/name/label/'controls.json').read_text())
            right=json.loads((repeat/name/label/'controls.json').read_text())
            delta=max(float(np.max(np.abs(np.array(a)-np.array(b)))) for a,b in zip(left,right))
            rows.append(dict(case=name,initialization=label,max_control_difference=delta,exact_match=delta==0))
    result=dict(cases=len(rows)//4,comparisons=len(rows),all_controls_exact_match=all(r['exact_match'] for r in rows),
                max_control_difference=max(r['max_control_difference'] for r in rows),
                scope='Independent pilot reoptimization only; main batch not independently rerun',rows=rows)
    write_json(original/'pilot_reproduction.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
