"""Certified exact-ODE attack gradient brackets and strong-concavity dual gap."""
from common import *
from heuristics import search
def clip(x,l,h):return max(l,min(h,x))
def main():
    model,z=frozen();u,a=z[:72],z[72:];H=192;tau=F(1,1000);m=F(5,3);cap=F(float(model['A']))
    start=time.perf_counter();base=evaluate(model,u,a,H);dump(OUT/'results/candidate_payoff_enclosure.json',base)
    low0,high0=[F(x) for x in base['B_A']];grad=[];secants=[]
    for j in range(12):
        assert 0<a[j]-tau<a[j]+tau<cap
        plus=a.copy();minus=a.copy();plus[j]+=tau;minus[j]-=tau
        pv=evaluate(model,u,plus,H);mv=evaluate(model,u,minus,H)
        # Concavity of the exact ODE payoff extends to the positive per-entry
        # box; these derivative probes are not claimed feasible deviations.
        lower=(F(pv['B_A'][0])-high0)/tau+m*tau/2
        upper=(high0-F(mv['B_A'][0]))/tau-m*tau/2
        assert lower<=upper;grad.append((lower,upper))
        secants.append(dict(component=j,plus_attack=[str(x) for x in plus],minus_attack=[str(x) for x in minus],plus=pv,minus=mv,gradient_interval=[str(lower),str(upper)]))
        print('attack_gradient_component',j+1,12,'width',float(upper-lower),flush=True)
        dump(OUT/'results/attacker_secants.json',dict(H=H,step=str(tau),base=base,components=secants))
    mid=[(l+h)/2 for l,h in grad];rad=[(h-l)/2 for l,h in grad]
    slots=[];total=F(0);linear=F(0)
    for k in range(6):
        x0=a[2*k:2*k+2];gm=mid[2*k:2*k+2];rr=rad[2*k:2*k+2]
        yy=[x+g/m for x,g in zip(x0,gm)];x=[clip(y,F(0),F(1)) for y in yy]
        if sum(x)<=cap:lam=F(0)
        elif yy[0]-yy[1]>=cap:x=[cap,F(0)];lam=m*(yy[0]-cap)
        elif yy[1]-yy[0]>=cap:x=[F(0),cap];lam=m*(yy[1]-cap)
        else:
            x=[(cap+yy[0]-yy[1])/2,(cap+yy[1]-yy[0])/2];lam=m*(sum(yy)-cap)/2
        assert lam>=0 and sum(x)<=cap and lam*(cap-sum(x))==0
        for j in range(2):
            residual=gm[j]-m*(x[j]-x0[j])-lam
            assert residual==0 if x[j]>0 else residual<=0
        scalar=[];slot_bound=lam*(cap-sum(x0))
        for j in range(2):
            candidates=[]
            for sign,left,right in [(-1,-x0[j],F(0)),(1,F(0),1-x0[j])]:
                c=gm[j]-lam+sign*rr[j];d=clip(c/m,left,right);value=c*d-m*d*d/2
                candidates.append(dict(sign=sign,domain=[str(left),str(right)],maximizer=str(d),maximum=str(value)))
            best=max(F(v['maximum']) for v in candidates);slot_bound+=best;scalar.append(candidates)
        verts=[[F(0),F(0)],[cap,F(0)],[F(0),cap]]
        lb=max(sum((gm[j]*(v[j]-x0[j])+rr[j]*abs(v[j]-x0[j]) for j in range(2)),F(0)) for v in verts)
        assert slot_bound>=0;total+=slot_bound;linear+=lb
        slots.append(dict(slot=k,base=[str(x) for x in x0],gradient_mid=[str(x) for x in gm],gradient_radius=[str(x) for x in rr],QP_mid_maximizer=[str(v) for v in x],dual_lambda=str(lam),robust_scalar_terms=scalar,robust_gap_upper=str(slot_bound),linear_gap_upper=str(lb)))
    heuristic=search('A')
    bestlo=F(heuristic['validated']['B_A'][0]);discovered=max(F(0),bestlo-high0)
    original_eta=F(read(ROOT/'work_e_r1/results/uniform_rk4_error.json')['J_A_uniform_error_upper'])
    cert=dict(object='B exact ODE, fixed U0; binary64 constants as exact reals',frozen_candidate_sha256=sha(OUT/'results/frozen_candidate.json'),gradient_method='two-sided certified payoff secants + strong concavity; H192 rigorous RK4 defects',gradient_intervals=[[str(x) for x in v] for v in grad],m=str(m),capacity=str(cap),slots=slots,candidate_payoff_B=base['B_A'],best_known_response_B=heuristic['validated']['B_A'],global_BR_payoff_lower=str(max(low0,bestlo)),global_BR_payoff_upper=str(high0+total),gap_lower=str(discovered),gap_upper=str(total),linear_gap_upper=str(linear),normalized_gap_upper=str(total/(1+low0)),C0_gap_upper_by_transfer=str(total+2*original_eta),all_gradient_probe_entries_within_positive_box=True,probes_claimed_feasible_deviations=False,passed_1pct=total/(1+low0)<=F(1,100),passed_0_1pct=total/(1+low0)<=F(1,1000),floating_program_global_certificate=False,seconds=time.perf_counter()-start,summary=dict(gap_upper=float(total),linear_gap_upper=float(linear),normalized_gap_upper=float(total/(1+low0)),BR_payoff_upper=float(high0+total)))
    dump(OUT/'results/attacker_certificate.json',cert);print(cert['summary'],flush=True)
if __name__=='__main__':main()
