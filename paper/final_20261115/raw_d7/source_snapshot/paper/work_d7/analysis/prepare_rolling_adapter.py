"""Create a reviewable D5 adapter by exact source substitutions; no solver edits."""
from pathlib import Path
import difflib
base=Path(__file__).resolve().parents[1]
root=base.parents[1]
source=(root/'paper/work_d5/analysis/run_replanning.py').read_text(encoding='utf-8')
function=source[source.index('def run_budget('):source.index('\ndef main():')]
replacements={
    "source=Path(f'results/matched_mechanism/run01/seed11_B{B}_unequal_high_at_node3')":"source=BASE/f'results/static/B{B}'",
    "load_controls(source/'fine/controls.json')":"load_controls(source/'G_controls.json')",
    "alpha=np.array([.5,.25,0,0,0,0])":"alpha=np.array([EVENT_ALPHA,.25,0,0,0,0])",
    '20261112':'20261114',
    'alpha0=.25 if k<3 else .5':'alpha0=.25 if k<3 else EVENT_ALPHA',
}
adapted=function
for old,new in replacements.items():
    assert old in adapted,old
    adapted=adapted.replace(old,new)
header='''"""D7 execution adapter: D5 run_budget with audited input/event/seed substitutions."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from paper.work_d5.analysis.run_replanning import *
BASE=ROOT/'paper/work_d7'
EVENT_ALPHA=.5
'''
footer='''
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
'''
(base/'analysis/run_rolling.py').write_text(header+adapted+footer,encoding='utf-8')
(base/'sources/D5_D7_execution_adapter.diff').write_text(''.join(difflib.unified_diff(function.splitlines(True),adapted.splitlines(True),fromfile='D5.run_budget',tofile='D7.run_budget')),encoding='utf-8')
