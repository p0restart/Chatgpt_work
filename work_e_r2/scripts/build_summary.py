"""Build exact-objective/gap tables from completed certificates, no optimization."""
from common import *
import csv
def csvwrite(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    ac=read(OUT/'results/attacker_certificate.json');dc=read(OUT/'results/defender_certificate.json');base=read(OUT/'results/candidate_payoff_enclosure.json');f48=read(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json');orig=read(ROOT/'work_e_r1/results/uniform_rk4_error.json')
    rows=[];vals={}
    for player,cert,key in [('D',dc,'D'),('A',ac,'A')]:
        candidate=[F(x) for x in base[f'B_{key}']]
        best=[F(x) for x in cert['best_known_response_B']]
        low=F(cert['global_BR_lower'] if player=='D' else cert['global_BR_payoff_lower']);high=F(cert['global_BR_upper'] if player=='D' else cert['global_BR_payoff_upper'])
        eps=F(cert['gap_upper']);den=1+candidate[0];eta=F(orig[f'J_{player}_uniform_error_upper'])
        # Direct B certificates avoid paying baseline H48 error twice.
        epsC=eps+2*eta
        vals[player]=dict(candidate_B=[str(x) for x in candidate],best_response_B=[str(x) for x in best],BR_bounds_B=[str(low),str(high)],epsilon_B=str(eps),normalized_B=str(eps/den),epsilon_C0_by_transfer=str(epsC),eta_H48=str(eta))
        rows.append(dict(player=player,object='B',candidate_lower=float(candidate[0]),candidate_upper=float(candidate[1]),best_known_response_lower=float(best[0]),best_known_response_upper=float(best[1]),global_BR_lower=float(low),global_BR_upper=float(high),certified_found_gain_lower=float(F(cert['gap_lower'])),certified_gain_upper=float(eps),normalized_gain_upper=float(eps/den),normalized_upper_percent=100*float(eps/den),passed_1pct=eps/den<=F(1,100),passed_0_1pct=eps/den<=F(1,1000),heuristic_only=False))
        rows.append(dict(player=player,object='C0_from_B',candidate_lower=float(F(f48['objective_D_interval'][0]) if player=='D' else -F(f48['objective_minus_A_interval'][1])),candidate_upper=float(F(f48['objective_D_interval'][1]) if player=='D' else -F(f48['objective_minus_A_interval'][0])),best_known_response_lower=float(best[0]-eta),best_known_response_upper=float(best[1]+eta),global_BR_lower=float(low-eta),global_BR_upper=float(high+eta),certified_found_gain_lower=0.,certified_gain_upper=float(epsC),normalized_gain_upper=float(epsC/(1+(F(f48['objective_D_interval'][0]) if player=='D' else -F(f48['objective_minus_A_interval'][1])))),normalized_upper_percent=100*float(epsC/(1+(F(f48['objective_D_interval'][0]) if player=='D' else -F(f48['objective_minus_A_interval'][1])))),passed_1pct=epsC/(1+(F(f48['objective_D_interval'][0]) if player=='D' else -F(f48['objective_minus_A_interval'][1])))<=F(1,100),passed_0_1pct=epsC/(1+(F(f48['objective_D_interval'][0]) if player=='D' else -F(f48['objective_minus_A_interval'][1])))<=F(1,1000),heuristic_only=False))
    csvwrite('results/objective_bounds.csv',rows)
    dump(OUT/'results/combined_assessment.json',dict(classification='B_partial_attacker_certification',players=vals,epsilon_max_B=str(max(F(vals['D']['epsilon_B']),F(vals['A']['epsilon_B']))),joint_one_percent_certified=False,significant_profitable_deviation_found=False,actual_floating_program_global_certificate=False,defender_budget_stop=True))
    print(rows[0]);print(rows[2]);print('Classification B partial',flush=True)
if __name__=='__main__':main()
