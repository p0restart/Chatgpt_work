"""Freeze original inputs and code; writes only this handoff directory."""
from pathlib import Path
import hashlib, json, shutil
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target = HERE/'inputs'
    target.mkdir(exist_ok=False)
    paths = ['paper/work_d7/results/static/B1.2/model.json',
             'paper/work_d7/results/static/B1.2/G_controls.json',
             'paper/work_d7/results/static/B1.2/G_evaluation.json',
             'paper/work_d7/results/static/B1.2/G/decision.json',
             'paper/work_d7/results/static/B1.2/G/warm/last.json',
             'paper/work_d7/results/static/environment_static_1.2.json',
             'paper/work_d7/config_new_topology.yaml',
             'paper/work_d7/03_experiment_protocol.md',
             'paper/work_d7/analysis/run_d7.py',
             'paper/work_d5/analysis/run_replanning.py',
             'paper/work_d7/sources/source_manifest.json', '02_MODEL_SPEC.md']
    manifest = {}
    for name in paths:
        p = ROOT/name
        dest = target/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
        manifest[name] = dict(sha256=sha(p), bytes=p.stat().st_size)
    source = HERE/'runtime/src'
    source.mkdir(parents=True,exist_ok=True)
    for name in ['core.py','game_solver.py','__init__.py']:
        p = ROOT/'src'/name
        shutil.copyfile(p,source/name)
        manifest['src/'+name] = dict(sha256=sha(p),bytes=p.stat().st_size)
    (HERE/'input_manifest.json').write_text(json.dumps(dict(
        created=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),sources=manifest),indent=2),encoding='utf-8')
    # Full paper tree fingerprint before execution, including manuscripts, references and figures.
    protected = {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'paper').rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts}
    (HERE/'paper_before.json').write_text(json.dumps(protected,indent=2),encoding='utf-8')
    print('Inputs and original solver frozen; paper tree fingerprint saved.',flush=True)
if __name__ == '__main__': main()
