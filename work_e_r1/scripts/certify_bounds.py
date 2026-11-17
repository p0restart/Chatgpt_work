"""Exact rational DAG bounds, not strategy sampling or equilibrium search."""
from pathlib import Path
from fractions import Fraction as F
from math import factorial,ceil
import sys,json,hashlib,platform
sys.dont_write_bytecode=True
sys.set_int_max_str_digits(100000)
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work_e_r1'

def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def rat(x):
    if isinstance(x,np.ndarray):return [[str(v) for v in row] for row in x] if x.ndim==2 else [str(v) for v in x]
    return str(x)
def eye(n):return np.array([[F(i==j) for j in range(n)] for i in range(n)],dtype=object)
def zeros(n,m):return np.full((n,m),F(0),dtype=object)
def ceil_rat(x):return -(-x.numerator//x.denominator)
def exp_neg(x):
    # Alternating-series remainders after order>=2, 0<=x<2.
    assert 0<=x<2
    terms=[(-x)**k/F(factorial(k)) for k in range(42)]
    lo=sum(terms,F(0));hi=sum(terms[:-1],F(0))
    assert 0<lo<hi
    return lo,hi
def proposed_perron(B):
    # Floating arithmetic proposes a vector only; every inequality is exact.
    _,v=np.linalg.eigh(np.array(B,dtype=float))
    v=np.abs(v[:,-1]);v/=max(v)
    return np.array([max(F(1,10**8),F(int(round(x*10**8)),10**8)) for x in v],dtype=object)
def perron_bound(B):
    assert all(x>=0 for x in B.flat)
    w=proposed_perron(B);r=B@w
    k=F(max(ceil_rat(x/y) for x,y in zip(r,w)))
    margin=k*w-r
    assert all(x>=0 for x in margin)
    return k,w,margin

def compute(model,mode):
    cast=(lambda x:F(str(x))) if mode=='declared_decimal' else (lambda x:F(float(x)))
    ar=lambda k:np.array([[cast(x) for x in row] for row in model[k]],dtype=object) if k=='beta' else np.array([cast(x) for x in model[k]],dtype=object)
    beta=ar('beta');q=ar('q');g=ar('g');alpha=ar('alpha');delta=ar('delta');gamma=ar('gamma')
    assert all(x==delta[0] for x in delta)
    d=delta[0];T=F(10);Delta=F(5,3);A=cast(model['A']);n=6
    order=[0,1,3,2,5,4];X=np.full(6,F(0),dtype=object)
    for i in order:
        b=alpha[i]*A+sum((beta[j,i]*X[j] for j in range(n)),F(0))
        X[i]=max(cast(model['x0'][i]),b/(b+delta[i]))
    L=beta.T;P=eye(n);elo,ehi=exp_neg(d*T);S=zeros(n,n)
    moments=[]
    for ell in range(4):
        poly=sum(((d*T)**k/F(factorial(k)) for k in range(ell+1)),F(0))
        upper=F(factorial(ell))/d**(ell+1)*(1-elo*poly)
        moments.append(upper);S+=P*(upper/F(factorial(ell)));P=P@L
    assert all(x==0 for x in P.flat) # no paths of length four
    Dinput=np.concatenate([L@np.diag(X),np.diag(gamma*X)],axis=1)
    G=S@Dinput
    exposure=L@G+np.concatenate([L@np.diag(X),zeros(6,6)],axis=1)
    recovery=np.concatenate([zeros(6,6),np.diag(gamma)],axis=1)
    p=S.T@q;ell=q+beta@p
    Z=np.concatenate([np.diag(beta@ell),zeros(6,6)],axis=1)
    W=moments[0]*(Z.T@G+G.T@Z)+moments[1]*(2*exposure.T@np.diag(ell)@exposure+exposure.T@np.diag(ell)@recovery+recovery.T@np.diag(ell)@exposure)
    assert all(x==0 for x in (W-W.T).flat)
    k,w,margin=perron_bound(W)
    EA=zeros(6,2);EA[0,0]=1;EA[1,1]=1
    GA=S@np.diag(alpha)@EA
    def mixed(weight):
        p=S.T@weight;Dp=np.diag(p)
        RD=np.concatenate([np.diag(beta@p)+np.diag(X)@beta@Dp,np.diag(gamma*p)],axis=0)
        M=G.T@(Dp@L+beta@Dp)@GA+RD@GA+G.T@np.diag(alpha*p)@EA
        bsq,v,slack=perron_bound(M@M.T)
        return dict(matrix=rat(M),norm_squared_upper=rat(bsq),perron_vector=rat(v),perron_slack=rat(slack))
    # q-g is nonnegative and supported only at the database in this model.
    assert list(q-g)==[0,0,0,0,3,0]
    cross=mixed(q-g);attack_cross=mixed(g)
    return dict(mode=mode,domain='all feasible U_K x A_K; bounding superset described in proof',topological_order=order,nilpotency_index=4,delta=rat(d),T=rat(T),Delta=rat(Delta),exp_lower=rat(elo),exp_upper=rat(ehi),state_upper=rat(X),moment_uppers=rat(np.array(moments,dtype=object)),S_upper=rat(S),G_defense=rat(G),E_exposure=rat(exposure),R_recovery=rat(recovery),effective_weights=rat(ell),negative_curvature_matrix=rat(W),perron_vector=rat(w),perron_slack=rat(margin),negative_state_curvature_L2_upper=rat(k),defense_Euclidean_Hessian_lower=rat(Delta*(1-k)),attack_Euclidean_Hessian_lower=rat(Delta),cross_difference=cross,cross_H_Euclidean_norm_squared_upper=rat(Delta**2*F(cross['norm_squared_upper'])/4),attack_cost_mixed=attack_cross,attack_BR_Euclidean_Lipschitz_squared_upper=attack_cross['norm_squared_upper'],convexity_certified=bool(k<1),summary=dict(kappa=float(k),m_D=float(Delta*(1-k)),m_A=float(Delta),c_DA_squared_upper=float(Delta**2*F(cross['norm_squared_upper'])/4)))

def main():
    cfg=json.loads((ROOT/'work_e/run_config.json').read_text(encoding='utf-8'))
    out=[]
    for mode in ('declared_decimal','binary64_as_exact_reals'):
        existing=OUT/f'results/structured_bound_{mode}.json'
        if existing.exists():
            cert=json.loads(existing.read_text(encoding='utf-8'));out.append(cert['summary']);print('RETAINED',mode,cert['summary'],flush=True);continue
        cert=compute(cfg['model'],mode);save(OUT/f'results/structured_bound_{mode}.json',cert)
        out.append(cert['summary']);print(mode,cert['summary'],flush=True)
    save(OUT/'results/structured_bound_summary.json',out)

if __name__=='__main__':main()
