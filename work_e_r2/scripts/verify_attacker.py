"""Independent rational checks of the secant/dual attack certificate."""
from common import *
import argparse
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');args=ap.parse_args()
    model,z=frozen();u,a=z[:72],z[72:];c=read(OUT/'results/attacker_certificate.json');s=read(OUT/'results/attacker_secants.json');tau=F(s['step']);m=F(5,3);cap=F(float(model['A']))
    assert c['frozen_candidate_sha256']==sha(OUT/'results/frozen_candidate.json')
    base=s['base'];H=s['H'];e=rk_error(H)
    def enclosure(ev):
        assert F(ev['B_A'][0])==F(ev['C0_A'][0])-e['A']
        assert F(ev['B_A'][1])==F(ev['C0_A'][1])+e['A']
    enclosure(base)
    if args.full:assert evaluate(model,u,a,H)==base
    gradient=[]
    for j,rec in enumerate(s['components']):
        pp=[F(x) for x in rec['plus_attack']];nn=[F(x) for x in rec['minus_attack']]
        assert pp[j]==a[j]+tau and nn[j]==a[j]-tau
        assert all(pp[k]==nn[k]==a[k] for k in range(12) if k!=j)
        assert all(0<=x<=cap for x in pp+nn)
        enclosure(rec['plus']);enclosure(rec['minus'])
        lo=(F(rec['plus']['B_A'][0])-F(base['B_A'][1]))/tau+m*tau/2
        hi=(F(base['B_A'][1])-F(rec['minus']['B_A'][0]))/tau-m*tau/2
        assert [str(lo),str(hi)]==c['gradient_intervals'][j] and lo<=hi;gradient.append((lo,hi))
        if args.full:
            assert evaluate(model,u,pp,H)==rec['plus'];assert evaluate(model,u,nn,H)==rec['minus']
        print('verified_attack_component',j+1,flush=True)
    upper=F(0);linear=F(0)
    for k,rec in enumerate(c['slots']):
        gm=[sum(gradient[2*k+j])/2 for j in range(2)];r=[(gradient[2*k+j][1]-gradient[2*k+j][0])/2 for j in range(2)];lam=F(rec['dual_lambda']);assert lam>=0
        value=lam*(cap-sum(a[2*k:2*k+2]))
        for j in range(2):
            x0=a[2*k+j];values=[]
            for sign,l,h in [(-1,-x0,F(0)),(1,F(0),1-x0)]:
                cc=gm[j]-lam+sign*r[j];t=max(l,min(h,cc/m));values.append(cc*t-m*t*t/2)
            value+=max(values)
        assert value==F(rec['robust_gap_upper']);upper+=value
        vertices=[(0,0),(cap,0),(0,cap)]
        lin=max(sum((gm[j]*(v[j]-a[2*k+j])+r[j]*abs(v[j]-a[2*k+j]) for j in range(2)),F(0)) for v in vertices)
        assert lin==F(rec['linear_gap_upper']);linear+=lin
    assert upper==F(c['gap_upper']) and linear==F(c['linear_gap_upper'])
    assert F(c['global_BR_payoff_upper'])==F(base['B_A'][1])+upper
    assert upper/(1+F(base['B_A'][0]))==F(c['normalized_gap_upper'])<F(1,1000)
    obj=dict(passed=True,full_interval_reintegration=args.full,rational_secant_and_dual_checks=True,attacker_gap_B_upper=str(upper),normalized_upper=str(F(c['normalized_gap_upper'])),candidate_unchanged=True)
    dump(OUT/'results/attacker_verification.json',obj);print('ATTACK CERTIFICATE PASSED',float(upper),flush=True)
if __name__=='__main__':main()
