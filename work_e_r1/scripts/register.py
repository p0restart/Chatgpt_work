"""Read/fingerprint every Work E artifact and freeze R1 inputs, no mutations."""
from pathlib import Path
import sys,json,hashlib,platform,shutil
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work_e_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=json.loads((ROOT/'work_e/source_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in old.items())
    files=[p for p in (ROOT/'work_e').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    old.update({p.relative_to(ROOT).as_posix():sha(p) for p in files})
    for line in (ROOT/'work_e/SHA256SUMS').read_text(encoding='utf-8').splitlines():
        h,p=line.split('  ',1);assert sha(ROOT/'work_e'/p)==h
    # Consume all saved Work E text/JSON/CSV and array artifacts for inventory;
    # reports read by the researcher remain distinct from numerical proofs.
    inventory=[]
    for p in files:
        b=p.read_bytes()
        if p.suffix in ('.md','.py','.json','.jsonl','.csv'): b.decode('utf-8-sig')
        inventory.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(b),sha256=sha(p)))
    cfg=json.loads((ROOT/'work_e/run_config.json').read_text(encoding='utf-8'))
    r=dict(date='2026-11-15',timezone='Asia/Shanghai',object_priority=['B_exact_ODE_Kslot','C_exact_arithmetic_RK4_then_implementation'],N=6,K=6,T=10,B=1.2,A=.8,H=48,defense_dimension=72,attack_dimension=12,model=cfg['model'],new_stochastic_sampling=False,new_optimizations=0,certificate_arithmetic='Python Fraction exact rationals; Taylor exp remainder enclosures',parameter_interpretations=['declared_decimal','binary64_as_exact_reals'],python=sys.version,platform=platform.platform(),scope_authorization='User Work E-R1 instruction; not approval of conclusions',protected_files=len(old))
    for name,x in [('source_manifest.json',old),('run_config.json',r),('results/input_inventory.json',inventory)]:
        path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
    source=Path('C:/Users/Jin/.codex/attachments/6aa8177c-242d-4ea4-966d-305a5efea3ea/已粘贴的文本.txt')
    shutil.copyfile(source,OUT/'instruction_source.md')
    print('Protected inputs',len(old),'Work E files read',len(files),'Work E hashes passed',flush=True)
if __name__=='__main__':main()
