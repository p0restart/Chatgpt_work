from pathlib import Path
import sys,json,platform,shutil
sys.dont_write_bytecode=True
from common import ROOT,OUT,read,dump,sha
def main():
    old=read(ROOT/'work_e_r1/source_manifest.json')
    assert all(sha(ROOT/p)==h for p,h in old.items())
    for folder in ['work_e','work_e_r1']:
        for line in (ROOT/folder/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            h,p=line.split('  ',1);assert sha(ROOT/folder/p)==h
    files=[p for p in (ROOT/'work_e_r1').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    old.update({p.relative_to(ROOT).as_posix():sha(p) for p in files})
    cfg=read(ROOT/'work_e_r1/run_config.json');cfg.update(date='2026-11-15',timezone='Asia/Shanghai',stage='E-R2',seed=2026111502,model_parameter_interpretation='binary64 input constants as exact reals; capacities inherited exactly',parameter_interpretations=['binary64_as_exact_reals'],object_priority=['B_direct_global_deviation_certificates','C0_error_transfer','C_heuristic_only'],attacker_gradient_H=192,attacker_secant_step='1/1000',branch_generated_region_budget=1999,branch_integration_H=24,heuristic_starts=3,heuristic_steps=48,new_optimizations=6,new_stochastic_sampling=True,random_initializations=2,unstructured_global_random_search=False,protected_files=len(old),scope_authorization='User Work E-R2 instruction; not approval of conclusions',certificate_arithmetic='exact Fraction comparisons and 120-bit outward integer intervals',normalized_target='1/100',secondary_target='1/1000',hard_scope='fixed candidate; no candidate replacement or formal solver/model edits',python=sys.version,platform=platform.platform())
    c=read(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json')
    dump(OUT/'run_config.json',cfg);dump(OUT/'source_manifest.json',old)
    dump(OUT/'results/frozen_candidate.json',dict(candidate=c['candidate'],capacities=c['capacities'],source='work_e_r1/results/candidate_VI_interval_certificate.json',source_sha256=sha(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json'),original_repair_max=c['exact_feasibility_repair_max'],unchanged_for_R2=True))
    shutil.copyfile('C:/Users/Jin/.codex/attachments/8e29a309-2c85-442c-a5e1-50cd41a849e1/已粘贴的文本.txt',OUT/'instruction_source.md')
    print('Protected',len(old),'Frozen candidate inherited exactly',flush=True)
if __name__=='__main__':main()
