"""Seal/verify original sources and the final R1 review package without research runs."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,argparse
sys.dont_write_bytecode=True;sys.set_int_max_str_digits(100000)
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'work_e_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seal',action='store_true');args=ap.parse_args()
    original=read(BASE/'source_manifest.json');changed=[p for p,h in original.items() if sha(ROOT/p)!=h]
    required=[f'R1_0{i}_{s}.md' for i,s in enumerate(['mathematical_foundation','defense_convexity_proof','equilibrium_existence','equilibrium_uniqueness','certification_results','solver_equilibrium_connection'],start=1)]+['R1_final_report.md','run_config.json','README.md']
    assert not changed and all((BASE/p).is_file() for p in required)
    assert read(BASE/'results/certificate_verification.json')['passed']
    assert read(BASE/'results/symbolic_derivative_verification.json')['count']==24
    vi=read(BASE/'results/candidate_gap_verification.json');assert vi['passed'] and not vi['certifies_Nash']
    cert=read(BASE/'results/candidate_VI_interval_certificate.json');assert F(cert['linear_VI_gap_upper'])<F(7,100000)
    assert not cert['ODE_VI_gap_certified'] and not cert['Nash_gap_certified']
    for mode in ('declared_decimal','binary64_as_exact_reals'):
        c=read(BASE/f'results/structured_bound_{mode}.json')
        assert F(c['defense_Euclidean_Hessian_lower'])==-65 and not c['convexity_certified']
    # Ensure no output outside requested directory is listed as a new artifact.
    cfg=read(BASE/'run_config.json');assert cfg['new_optimizations']==0 and not cfg['new_stochastic_sampling']
    assert cfg['model']==read(ROOT/'work_e/run_config.json')['model']
    assert (cfg['N'],cfg['K'],cfg['T'],cfg['B'],cfg['A'],cfg['H'])==(6,6,10,1.2,.8,48)
    obj=dict(passed=True,protected_files=len(original),changed_protected_files=changed,work_e_files_preserved=len([p for p in original if p.startswith('work_e/')]),required_deliverables=len(required),symbolic_identities=24,exact_rational_cases=2,full_strategy_grid=False,new_optimizations=0,new_random_samples=0,defense_convexity_proven=False,pure_Nash_existence_proven=False,pure_Nash_uniqueness_proven=False,C0_VI_gap_upper=float(F(cert['linear_VI_gap_upper'])),uniform_B_C0_objective_bound_certified=True,machine_roundoff_global_certificate=False,status='WAITING_USER_E_R1_REVIEW')
    if args.seal:
        (BASE/'delivery_checks.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
        files=sorted(p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS')
        (BASE/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(BASE).as_posix()}\n' for p in files),encoding='utf-8')
    else:
        for line in (BASE/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            h,p=line.split('  ',1);assert sha(BASE/p)==h,p
        obj['package_hashes_verified']=True
    print(json.dumps(obj,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
