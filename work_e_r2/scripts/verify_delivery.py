"""Final R2 integrity, arithmetic transfer and package checks; no optimization."""
from common import *
import argparse,csv
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seal',action='store_true');args=ap.parse_args()
    original=read(OUT/'source_manifest.json');changed=[p for p,h in original.items() if sha(ROOT/p)!=h];assert not changed
    model,z=frozen();r1=read(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json');fr=read(OUT/'results/frozen_candidate.json')
    assert fr['candidate']==r1['candidate'] and fr['capacities']==r1['capacities']
    assert fr['source_sha256']==sha(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json')
    cfg=read(OUT/'run_config.json');assert model==read(ROOT/'work_e_r1/run_config.json')['model']
    assert (cfg['N'],cfg['K'],cfg['T'],cfg['B'],cfg['A'],cfg['H'])==(6,6,10,1.2,.8,48)
    av=read(OUT/'results/attacker_verification.json');dv=read(OUT/'results/defender_verification.json')
    assert av['passed'] and av['full_interval_reintegration'] and dv['passed'] and dv['full_interval_reintegration']
    assert dv['every_branch_pair_covers_parent'] and dv['retained_frontier']==1000
    ac=read(OUT/'results/attacker_certificate.json');dc=read(OUT/'results/defender_certificate.json');base=read(OUT/'results/candidate_payoff_enclosure.json')
    assert ac['frozen_candidate_sha256']==sha(OUT/'results/frozen_candidate.json')
    optimizer_calls=0;all_zero=True;max_v=0.
    for p,width,cap in [('A',2,F(float(model['A']))),('D',12,F(float(model['B'])))]:
        h=read(OUT/f'results/heuristic_{p}.json');optimizer_calls+=len(h['raw'])
        all_zero=all_zero and all(r['success'] and r['status']==0 for r in h['raw']);max_v=max(max_v,max(r['violation'] for r in h['raw']))
        v=[F(x) for x in h['strict_feasible_response']]
        for k in range(6):assert all(0<=x<=1 for x in v[k*width:(k+1)*width]) and sum(v[k*width:(k+1)*width],F(0))<=cap
        assert [F(x) for x in h['strict_fixed_opponent']]==(z[:72] if p=='A' else z[72:])
    assert optimizer_calls==cfg['new_optimizations']==6 and cfg['random_initializations']==2 and all_zero
    assert F(dc['gap_upper'])==F(base['B_D'][1])-F(dc['global_BR_lower'])
    assert F(dc['normalized_gap_upper'])==F(dc['gap_upper'])/(1+F(base['B_D'][0]))>F(1,100)
    assert F(ac['normalized_gap_upper'])==F(ac['gap_upper'])/(1+F(base['B_A'][0]))<F(1,1000)
    combined=read(OUT/'results/combined_assessment.json');origeta=read(ROOT/'work_e_r1/results/uniform_rk4_error.json')
    for p,c in [('D',dc),('A',ac)]:
        ep=F(c['gap_upper']);tr=F(combined['players'][p]['epsilon_C0_by_transfer']);eta=F(origeta[f'J_{p}_uniform_error_upper'])
        assert tr==ep+2*eta and F(combined['players'][p]['epsilon_B'])==ep
    assert not combined['joint_one_percent_certified'] and combined['classification']=='B_partial_attacker_certification'
    assert read(OUT/'results/R1_C0_crosscheck.json')['passed']
    qa=read(OUT/'figures/qa/summary.json');assert all(r['returncode']==0 for r in qa)
    for stem in ['fig1_defender_global_bounds','fig2_attacker_response_certificate','fig3_nash_gap_targets']:
        for ext in ['pdf','svg','png']:assert (OUT/f'figures/{stem}.{ext}').exists()
        assert read(OUT/f'figures/qa/{stem}_collisions.json')['verdict']=='PASS'
    required=['R2_00_candidate_and_object.md','R2_01_attacker_global_response.md','R2_02_defender_global_response.md','R2_03_error_transfer.md','R2_04_epsilon_nash_assessment.md','R2_final_report.md','run_config.json','README.md','results/attacker_certificate.json','results/defender_certificate.json','results/defender_bounds.csv','results/objective_bounds.csv']
    assert all((OUT/f).exists() for f in required)
    obj=dict(passed=True,status='WAITING_USER_E_R2_REVIEW',classification='B_partial_attacker_certification',protected_files=len(original),changed_files=changed,frozen_candidate_exactly_inherited=True,optimizer_calls=optimizer_calls,all_optimizer_exit_codes_zero=all_zero,maximum_float_optimizer_capacity_violation=max_v,strict_repaired_responses_feasible=True,attack_full_interval_check=True,defender_full_interval_and_tree_check=True,defender_regions=dv['generated_regions'],retained_frontier=dv['retained_frontier'],attacker_epsilon_B=float(F(ac['gap_upper'])),defender_epsilon_B=float(F(dc['gap_upper'])),attacker_normalized_percent_B=100*float(F(ac['normalized_gap_upper'])),defender_normalized_percent_B=100*float(F(dc['normalized_gap_upper'])),joint_one_percent_certified=False,C0_transfer_exact=True,machine_C_global_certificate=False,figure_count=3,all_final_PDF_checks_passed=True,external_expert_review=False,formal_proof_assistant_check=False)
    if args.seal:
        dump(OUT/'results/verification_results.json',obj)
        files=sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS')
        (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in files),encoding='utf-8')
    else:
        for line in (OUT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            h,p=line.split('  ',1);assert sha(OUT/p)==h,p
        obj['package_hashes_verified']=True
    print(json.dumps(obj,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
