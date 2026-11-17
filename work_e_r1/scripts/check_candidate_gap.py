"""Exact independent greedy LP / enclosure check on the fixed-candidate gradient."""
from pathlib import Path
from fractions import Fraction as F
import json,sys,shutil
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'work_e_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    path=BASE/'results/candidate_VI_interval_certificate.json';c=read(path);model=read(BASE/'run_config.json')['model']
    caps=[F(float(model['B']))]*6+[F(float(model['A']))]*6
    z=[F(v) for v in c['candidate']];boxes=[[F(v) for v in x] for x in c['gradient_intervals']]
    mid=[(l+h)/2 for l,h in boxes];radius=[(h-l)/2 for l,h in boxes]
    blocks=[list(range(k*12,(k+1)*12)) for k in range(6)]+[list(range(72+2*k,74+2*k)) for k in range(6)]
    assert all(0<=v<=1 for v in z)
    w=[F(0)]*84
    for ix,cap in zip(blocks,caps):
        assert sum((z[j] for j in ix),F(0))<=cap
        left=cap
        for j in sorted(ix,key=lambda j:mid[j]):
            if mid[j]>=0:break
            w[j]=min(F(1),left);left-=w[j]
            if not left:break
    gap=sum((v*(zz-ww) for v,zz,ww in zip(mid,z,w)),F(0));err=sum(radius,F(0))
    if c['capacities']!=[str(v) for v in caps]:
        # Preserve initial restricted-capacity LP result; interval integration
        # is unchanged. The full binary model's attack cap differs by <1 ulp.
        old=BASE/'results/candidate_VI_before_capacity_audit.json'
        if not old.exists():shutil.copyfile(path,old)
        c['feasibility_repair_capacities']=c['capacities'];c['capacities']=[str(v) for v in caps]
        c['linear_VI_gap_mid']=str(gap);c['linear_VI_gap_error']=str(err);c['linear_VI_gap_upper']=str(gap+err);c['linear_minimizer']=[str(v) for v in w]
        c['summary']['gap_upper']=float(gap+err)
        c['capacity_audit_note']='Feasibility repair used min(decimal,binary) caps; final LP now covers the full binary64-as-real model caps. No interval integration was repeated.'
        path.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
    assert c['linear_minimizer']==[str(v) for v in w] and F(c['linear_VI_gap_upper'])==gap+err
    assert gap+err<F(7,100000) and max(2*x for x in radius)<F(1,10**28)
    result=dict(passed=True,exact_feasibility=True,LP_full_binary_model_domain=True,linear_gap_upper=str(gap+err),numerical_upper=float(gap+err),gradient_enclosure_width_max=float(max(2*x for x in radius)),interval_integration_proof='integer outward arithmetic + differentiated exact RK4; not a formal proof assistant',certifies_Nash=False,certifies_ODE_VI=False)
    (BASE/'results/candidate_gap_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['numerical_upper'],flush=True)
if __name__=='__main__':main()
