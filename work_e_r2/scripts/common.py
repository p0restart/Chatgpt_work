"""Shared exact inputs and outward-integer RK4 evaluator for R2."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,hashlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work_e_r2'
sys.path.insert(0,str(ROOT/'work_e_r1/scripts'))
from certify_candidate_vi import I, ZERO, SCALE

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
    cfg=read(OUT/'run_config.json');z=[F(x) for x in read(OUT/'results/frozen_candidate.json')['candidate']]
    assert all(v==1 for key in ('c_s','c_r','c_a','epsilon','b_s','b_r','d_a') for v in cfg['model'][key])
    assert cfg['model']['q'][:2]==[1,1] and all(v==1 for v in cfg['model']['g'])
    return cfg['model'],z
def endpoints(v):return F(v.lo,SCALE),F(v.hi,SCALE)
def box(v):return [str(x) for x in endpoints(v)]
def rk_error(H):
    c=read(ROOT/'work_e_r1/results/uniform_rk4_error.json');h=F(5,3*H)
    coeff=[F(x) for x in c['rk_majorant_coefficients']]
    C=F(c['fifth_time_derivative_bound'])/120+sum((x*h**(j-5) for j,x in enumerate(coeff) if j>=5),F(0))
    estate=48*C*h**4;emean=162*C*h**4
    assert h*F(6,5)<F(9,100) and estate<F(1,1000)
    return dict(H=H,h=h,C=C,state=estate,mean=emean,D=9*emean,A=6*emean)
def direct_cost(model,u):
    total=F(0)
    for k in range(6):
        for i in range(6):
            s,r=u[12*k+i],u[12*k+6+i]
            total+=F(5,3)*(F(float(model['h'][i]))*s+(s*s+r*r)/2)
    return total
def evaluate(model,u,a,H=48):
    """Enclose exact RK4 node integrals; add rigorous ODE error separately."""
    assert len(u)==72 and len(a)==12
    beta=[[I.of(F(float(v))) for v in row] for row in model['beta']]
    al=[I.of(F(float(v))) for v in model['alpha']];de=[I.of(F(float(v))) for v in model['delta']];ga=[I.of(F(float(v))) for v in model['gamma']]
    parents=[[j for j in range(6) if model['beta'][j][i]] for i in range(6)]
    x=[I.of(F(float(v))) for v in model['x0']];ints=[ZERO]*6
    h=I.of(F(5,3*H));half=I.of(F(1,2));sixth=I.of(F(1,6))
    for k in range(6):
        ss=[I.of(v) for v in u[12*k:12*k+6]];rr=[I.of(v) for v in u[12*k+6:12*k+12]];aa=[I.of(v) for v in a[2*k:2*k+2]]+[ZERO]*4
        def rhs(y):
            return [(1-y[i])*(al[i]*aa[i]+sum((beta[j][i]*(1-ss[j])*y[j] for j in parents[i]),ZERO))-(de[i]+ga[i]*rr[i])*y[i] for i in range(6)]
        for _ in range(H):
            k1=rhs(x);x2=[v+h*half*f for v,f in zip(x,k1)];k2=rhs(x2)
            x3=[v+h*half*f for v,f in zip(x,k2)];k3=rhs(x3)
            x4=[v+h*f for v,f in zip(x,k3)];k4=rhs(x4)
            ints=[v+h*sixth*(y1+2*y2+2*y3+y4) for v,y1,y2,y3,y4 in zip(ints,x,x2,x3,x4)]
            x=[v+h*sixth*(f1+2*f2+2*f3+f4) for v,f1,f2,f3,f4 in zip(x,k1,k2,k3,k4)]
    q=[F(float(v)) for v in model['q']];g=[F(float(v)) for v in model['g']]
    sec=sum((I.of(qi)*v for qi,v in zip(q,ints)),ZERO)
    av=sum((I.of(gi)*v for gi,v in zip(g,ints)),ZERO)-I.of(F(5,6)*sum((v*v for v in a),F(0)))
    jd=sec+I.of(direct_cost(model,u));err=rk_error(H)
    dl,dh=endpoints(jd);alow,ahigh=endpoints(av)
    return dict(H=H,node_integrals=[box(v) for v in ints],states_final=[box(v) for v in x],C0_D=box(jd),C0_A=box(av),B_D=[str(dl-err['D']),str(dh+err['D'])],B_A=[str(alow-err['A']),str(ahigh+err['A'])],error_D=str(err['D']),error_A=str(err['A']))
def repair(values,cap,width):
    v=[max(F(0),min(F(1),F(float(x)))) for x in values]
    for k in range(len(v)//width):
        ix=list(range(k*width,(k+1)*width));ex=max(F(0),sum((v[j] for j in ix),F(0))-cap)
        if ex:
            j=max(ix,key=lambda j:v[j]);v[j]-=ex
        assert all(0<=v[j]<=1 for j in ix) and sum((v[j] for j in ix),F(0))<=cap
    return v
