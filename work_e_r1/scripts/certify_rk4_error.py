"""Exact rational majorants for uniform RK4 objective error, not point tests."""
from fractions import Fraction as F
from math import factorial
from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work_e_r1'
def add(a,b):
    return [(a[i] if i<len(a) else F(0))+(b[i] if i<len(b) else F(0)) for i in range(max(len(a),len(b)))]
def scale(a,k):return [v*k for v in a]
def shift(a,k):return [F(0)]*k+a
def mul(a,b):
    out=[F(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out
def evaluate(a,h):return sum((x*h**i for i,x in enumerate(a)),F(0))
def main():
    h=F(5,144);M=F(6,5);L=F(11,10);Q=F(3,5)
    def stage(c,k):
        disp=shift(scale(k,c),1)
        return add([M],add(scale(disp,L),scale(mul(disp,disp),Q/2)))
    k1=[M];k2=stage(F(1,2),k1);k3=stage(F(1,2),k2);k4=stage(F(1),k3)
    rk=shift(scale(add(add(k1,scale(k2,2)),add(scale(k3,2),k4)),F(1,6)),1)
    tail=sum((v*h**(i-5) for i,v in enumerate(rk) if i>=5),F(0))
    D5=L**4*M+11*Q*L**2*M**2+4*Q**2*M**3
    C=tail+D5/120
    # e^(5/2)<13: Taylor sum plus geometric upper bound on its tail.
    x=F(5,2);N=30;s=sum((x**k/F(factorial(k)) for k in range(N+1)),F(0))
    eupper=s+(x**(N+1)/F(factorial(N+1)))/(1-x/F(N+2))
    assert eupper<13
    estate=48*C*h**4
    emean=162*C*h**4
    assert estate<F(1,1000)
    # State RK4 stages remain in [-.1,1.1] if starting in [-.001,1.001].
    assert max(h/2*M,h*M)<F(9,100)
    jd=9*emean;ja=6*emean
    obj=dict(object='exact-arithmetic RK4 polynomial map C0 versus exact ODE B',domain='all U_K x A_K, K6 B1.2 A.8 T10 H48',step=str(h),M=str(M),L=str(L),second_derivative_norm_bound=str(Q),fifth_time_derivative_bound=str(D5),rk_majorant_coefficients=[str(v) for v in rk],rk_tail_coefficient=str(tail),local_error_coefficient=str(C),exp_2_5_upper=str(eupper),state_error_upper=str(estate),normalized_integrated_state_error_upper=str(emean),J_D_uniform_error_upper=str(jd),J_A_uniform_error_upper=str(ja),state_tube='[-1/10,11/10]',bootstrap_closed=True,code_state_guard_all_domain_certified=False,floating_roundoff_certified=False,summary=dict(local_error_coefficient=float(C),state_error_upper=float(estate),J_D_error=float(jd),J_A_error=float(ja)))
    (OUT/'results').mkdir(parents=True,exist_ok=True)
    (OUT/'results/uniform_rk4_error.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    print(obj['summary'],flush=True)
if __name__=='__main__':main()
