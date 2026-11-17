"""Sequential gates; halt on the first failing subprocess, preserving all outputs."""
from pathlib import Path
import subprocess,sys,json,time
root=Path(__file__).resolve().parents[3]
base=root/'paper/work_d7'
commands=[
 ['analysis/run_d7.py','static','--budget','0.6'],
 ['analysis/run_d7.py','cross','--budget','0.6'],
 ['analysis/run_d7.py','static','--budget','1.8'],
 ['analysis/run_d7.py','cross','--budget','1.8'],
 ['analysis/run_rolling.py','--budget','1.2'],
 ['analysis/run_rolling.py','--budget','1.2','--no-event'],
 ['analysis/run_rolling.py','--budget','0.6'],
 ['analysis/run_rolling.py','--budget','1.8'],
]
assert (base/'results/static/B1.2/static_gate.json').exists()
log=base/'results/pipeline.jsonl'
assert not log.exists()
for args in commands:
    command=[sys.executable,str(base/args[0]),*args[1:]]
    start=time.time();print('START',args,flush=True)
    try: result=subprocess.run(command,cwd=root,timeout=1900);code=result.returncode
    except subprocess.TimeoutExpired: code=124
    with log.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(command=command,returncode=code,elapsed=time.time()-start))+'\n')
    if code:sys.exit(code)
print('ALL_REGISTERED_NUMERICAL_STAGES_FINISHED',flush=True)
