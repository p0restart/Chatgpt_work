"""Independent exact-rational checker: no eigenvalue routines or strategy samples."""
from pathlib import Path
from fractions import Fraction as F
from math import factorial
import json,sys,hashlib
sys.dont_write_bytecode=True;sys.set_int_max_str_digits(100000)
import numpy as np
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'work_e_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def mat(x):return np.array([[F(v) for v in r] for r in x],dtype=object)
def vec(x):return np.array([F(v) for v in x],dtype=object)
def zeros(a,b):return np.full((a,b),F(0),dtype=object)
def equal(a,b):assert np.array_equal(a,b)
def perron(B,vector,k,slack):
    v=vec(vector);r=F(k)*v-B@v
    assert all(t>0 for t in v) and all(t>=0 for t in r)
    equal(r,vec(slack));assert all(t>=0 for t in B.flat)
def check(mode,model):
    c=read(BASE/f'results/structured_bound_{mode}.json')
    cv=(lambda x:F(str(x))) if mode=='declared_decimal' else (lambda x:F(float(x)))
    B=np.array([[cv(x) for x in r] for r in model['beta']],dtype=object);L=B.T
    d=cv(model['delta'][0]);T=F(10);al=vec([str(cv(x)) for x in model['alpha']]);gm=vec([str(cv(x)) for x in model['gamma']]);q=vec([str(cv(x)) for x in model['q']]);g=vec([str(cv(x)) for x in model['g']])
    lo=sum(((-d*T)**i/F(factorial(i)) for i in range(42)),F(0));hi=sum(((-d*T)**i/F(factorial(i)) for i in range(41)),F(0))
    assert c['exp_lower']==str(lo) and c['exp_upper']==str(hi) and 0<d*T<2
    X=np.full(6,F(0),dtype=object)
    for i in [0,1,3,2,5,4]:
        z=al[i]*cv(model['A'])+sum((B[j,i]*X[j] for j in range(6)),F(0))
        X[i]=max(cv(model['x0'][i]),z/(d+z))
    equal(X,vec(c['state_upper']))
    P=np.array([[F(i==j) for j in range(6)] for i in range(6)],dtype=object);S=zeros(6,6);I=[]
    for k in range(4):
        I.append(F(factorial(k))/d**(k+1)*(1-lo*sum(((d*T)**j/F(factorial(j)) for j in range(k+1)),F(0))))
        S+=I[-1]/F(factorial(k))*P;P=P@L
    assert not any(P.flat);equal(S,mat(c['S_upper']));equal(np.array(I,dtype=object),vec(c['moment_uppers']))
    G=S@np.concatenate([L@np.diag(X),np.diag(gm*X)],axis=1)
    E=L@G+np.concatenate([L@np.diag(X),zeros(6,6)],axis=1);R=np.concatenate([zeros(6,6),np.diag(gm)],axis=1)
    ell=q+B@S.T@q;Z=np.concatenate([np.diag(B@ell),zeros(6,6)],axis=1)
    W=I[0]*(Z.T@G+G.T@Z)+I[1]*(2*E.T@np.diag(ell)@E+E.T@np.diag(ell)@R+R.T@np.diag(ell)@E)
    for arr,key in [(G,'G_defense'),(E,'E_exposure'),(R,'R_recovery'),(W,'negative_curvature_matrix')]:equal(arr,mat(c[key]))
    perron(W,c['perron_vector'],c['negative_state_curvature_L2_upper'],c['perron_slack'])
    assert F(c['defense_Euclidean_Hessian_lower'])==F(5,3)*(1-F(c['negative_state_curvature_L2_upper']))==-65
    EA=zeros(6,2);EA[0,0]=1;EA[1,1]=1;GA=S@np.diag(al)@EA
    for weight,key in [(q-g,'cross_difference'),(g,'attack_cost_mixed')]:
        cc=c[key];p=S.T@weight;D=np.diag(p)
        RD=np.concatenate([np.diag(B@p)+np.diag(X)@B@D,np.diag(gm*p)],axis=0)
        C=G.T@(D@L+B@D)@GA+RD@GA+G.T@np.diag(al*p)@EA
        equal(C,mat(cc['matrix']));perron(C@C.T,cc['perron_vector'],cc['norm_squared_upper'],cc['perron_slack'])
    assert F(c['cross_H_Euclidean_norm_squared_upper'])==F(25,36)*253
    return dict(mode=mode,all_exact_inequalities_passed=True,m_D_lower=-65,m_A_lower='5/3',cross_norm_squared_upper='6325/36')
def rk():
    c=read(BASE/'results/uniform_rk4_error.json');h=F(c['step']);M=F(c['M']);L=F(c['L']);Q=F(c['second_derivative_norm_bound'])
    # Independently reconstruct scalar-majorant polynomial using SymPy.
    import sympy as sp
    t=sp.Symbol('t');sf=lambda f:sp.Rational(f.numerator,f.denominator)
    k1=sf(M);k2=k1+sf(L)*t*k1/2+sf(Q)*(t*k1/2)**2/2
    k3=k1+sf(L)*t*k2/2+sf(Q)*(t*k2/2)**2/2
    k4=k1+sf(L)*t*k3+sf(Q)*(t*k3)**2/2
    poly=sp.Poly(t*(k1+2*k2+2*k3+k4)/6,t)
    coeff=[F(str(poly.nth(i))) for i in range(poly.degree()+1)]
    assert coeff==[F(v) for v in c['rk_majorant_coefficients']]
    tail=sum((v*h**(i-5) for i,v in enumerate(coeff) if i>=5),F(0))
    D5=L**4*M+11*Q*L**2*M**2+4*Q**2*M**3
    C=tail+D5/120
    assert C==F(c['local_error_coefficient'])
    assert 48*C*h**4==F(c['state_error_upper'])<F(1,1000)
    assert 9*162*C*h**4==F(c['J_D_uniform_error_upper'])
    assert 6*162*C*h**4==F(c['J_A_uniform_error_upper'])
    eupper=F(c['exp_2_5_upper']);x=F(5,2)
    assert eupper==sum((x**j/F(factorial(j)) for j in range(31)),F(0))+(x**31/F(factorial(31)))/(1-x/32)<13
    # Rational relaxed parameter enclosures cover decimal and exact binary64.
    for mode in ('declared_decimal','binary64_as_exact_reals'):
        model=read(BASE/'run_config.json')['model'];cv=(lambda x:F(str(x))) if mode=='declared_decimal' else (lambda x:F(float(x)))
        b=max(sum(cv(model['beta'][j][i]) for j in range(6)) for i in range(6))
        assert b<F(2901,10000)
        assert min(cv(x) for x in model['delta'])>F(999,10000)
        assert max(cv(x) for x in model['delta'])<F(1001,10000)
        assert max(cv(x) for x in model['gamma'])<F(3001,10000)
        assert max(cv(x) for x in model['alpha'])*cv(model['A'])<F(2001,10000)
        assert all(cv(x)==1 for x in model['epsilon'])
    assert F(11,10)*(F(11,10)*F(2901,10000)+F(4002,10000))<M
    assert F(4002,10000)+2*F(11,10)*F(2901,10000)<L
    assert 2*F(2901,10000)<Q
    assert -F(999,10000)+F(6,5)*F(2901,10000)<F(1,4)
    return dict(rational_RK4_bound_verified=True,uniform_objective_bounds_valid_for_exact_arithmetic=True,floating_implementation_certificate=False)
def main():
    model=read(BASE/'run_config.json')['model']
    checks=[check(mode,model) for mode in ('declared_decimal','binary64_as_exact_reals')];checks.append(rk())
    src=read(BASE/'source_manifest.json');changed=[p for p,h in src.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert not changed
    out=dict(passed=True,arithmetic='exact rational comparisons; no numerical eigenvalues used by checker',checks=checks,protected_files=len(src),changed_files=changed,formal_proof_assistant_verification=False,random_samples=0,optimizer_runs=0)
    (BASE/'results/certificate_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
