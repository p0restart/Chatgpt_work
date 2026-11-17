"""Exact scalar-source convex relaxation, evaluated with outward intervals."""
from common import *
from math import factorial
def divide(a,b):
    assert b.lo>0
    inv=I((SCALE*SCALE)//b.hi,-((-SCALE*SCALE)//b.lo))
    return a*inv
def expminus(v):
    assert v.lo>=0 and F(v.hi,SCALE)<F(11,10)
    term=I.of(1);total=term
    for k in range(1,41):term=term*(-v)*I.of(F(1,k));total=total+term
    remainder=I.of(F(11,10)**41/F(factorial(41)))
    return I(total.lo-remainder.hi,total.hi)
def objective(model,a,r):
    x=[I.of(F(float(v))) for v in model['x0'][:2]];total=ZERO;D=I.of(F(5,3))
    for k in range(6):
        for j in range(2):
            attack=I.of(F(float(model['alpha'][j]))*a[2*k+j]);d=I.of(F(float(model['delta'][j])))+I.of(F(float(model['gamma'][j]))*r[2*k+j]);lam=attack+d
            equi=divide(attack,lam);e=expminus(lam*D)
            integ=equi*D+divide((x[j]-equi)*(1-e),lam)
            total=total+integ+I.of(F(5,6)*r[2*k+j]**2)
            x[j]=equi+(x[j]-equi)*e
    return endpoints(total)
def make():
    model,z=frozen();u,a=z[:72],z[72:];r=[u[k*12+6+j] for k in range(6) for j in range(2)]
    ref=objective(model,a,r);t=F(1,100000);m=F(5,3);grad=[];probes=[]
    for j in range(12):
        p=r.copy();n=r.copy();p[j]+=t;n[j]-=t
        pv=objective(model,a,p);nv=objective(model,a,n)
        lo=(ref[0]-nv[1])/t+m*t/2
        hi=(pv[1]-ref[0])/t-m*t/2
        assert lo<=hi;grad.append([str(lo),str(hi)])
        probes.append(dict(component=j,plus=[str(x) for x in pv],minus=[str(x) for x in nv]))
    obj=dict(object='B scalar-source relaxation, original fixed A0',reference=[str(v) for v in r],reference_value=[str(x) for x in ref],gradient_intervals=grad,step=str(t),strong_convexity=str(m),probes=probes,whole_network_convexity_claim=False)
    dump(OUT/'results/source_relaxation_certificate.json',obj);return obj
def lower_box(cert,low,high):
    ref=[F(v) for v in cert['reference']];m=F(cert['strong_convexity']);ans=F(cert['reference_value'][0])
    for k in range(6):
        for j in range(2):
            t=2*k+j;idx=12*k+6+j;l=low[idx]-ref[t];h=high[idx]-ref[t]
            gl,gh=[F(x) for x in cert['gradient_intervals'][t]];gm=(gl+gh)/2;rad=(gh-gl)/2
            vals=[]
            for a,b,c in [(l,min(h,F(0)),gm+rad),(max(l,F(0)),h,gm-rad)]:
                if a>b:continue
                d=max(a,min(b,-c/m));vals.append(c*d+m*d*d/2)
            assert vals;ans+=min(vals)
    return max(F(0),ans)
if __name__=='__main__':
    c=make();print('Source relaxation global lower',float(lower_box(c,[F(0)]*72,[F(1)]*72)),flush=True)
