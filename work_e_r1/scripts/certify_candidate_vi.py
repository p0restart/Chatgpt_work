"""One fixed candidate, integer outward interval RK4+joint sensitivities.

This certifies an ideal RK4 VI gap, not an ODE Nash gap or an equilibrium.
"""
from pathlib import Path
from fractions import Fraction as F
import json,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work_e_r1'
P=120;SCALE=1<<P
class I:
    __slots__=('lo','hi')
    def __init__(self,lo,hi=None):self.lo=lo;self.hi=lo if hi is None else hi
    @staticmethod
    def of(v):
        if isinstance(v,I):return v
        f=F(v);return I((f.numerator*SCALE)//f.denominator,-((-f.numerator*SCALE)//f.denominator))
    def __add__(self,b):
        b=I.of(b);return I(self.lo+b.lo,self.hi+b.hi)
    __radd__=__add__
    def __neg__(self):return I(-self.hi,-self.lo)
    def __sub__(self,b):return self+-I.of(b)
    def __rsub__(self,b):return I.of(b)+-self
    def __mul__(self,b):
        b=I.of(b);t=(self.lo*b.lo,self.lo*b.hi,self.hi*b.lo,self.hi*b.hi)
        return I(min(t)//SCALE,-((-max(t))//SCALE))
    __rmul__=__mul__
    def box(self):return [str(F(self.lo,SCALE)),str(F(self.hi,SCALE))]
ZERO=I.of(0)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    start=time.perf_counter();cfg=read(OUT/'run_config.json')['model']
    assert all(v==1 for key in ('c_s','c_r','c_a','epsilon') for v in cfg[key])
    raw=read(ROOT/'paper/work_d7/results/static/B1.2/G_controls.json')
    a,s,r=[[[F(float(v)) for v in row] for row in arr] for arr in raw]
    orig=[x for k in range(6) for x in s[k]+r[k]]+[x for k in range(6) for x in a[k][:2]]
    z=[max(F(0),min(F(1),x)) for x in orig]
    caps=[min(F(6,5),F(float(cfg['B'])))]*6+[min(F(4,5),F(float(cfg['A'])))]*6
    caps_eval=[F(float(cfg['B']))]*6+[F(float(cfg['A']))]*6
    blocks=[list(range(k*12,(k+1)*12)) for k in range(6)]+[list(range(72+k*2,72+(k+1)*2)) for k in range(6)]
    for ix,cap in zip(blocks,caps):
        excess=max(F(0),sum((z[j] for j in ix),F(0))-cap)
        if excess:
            j=max(ix,key=lambda j:z[j]);assert z[j]>=excess;z[j]-=excess
        assert sum((z[j] for j in ix),F(0))<=cap
    repair=max(abs(x-y) for x,y in zip(orig,z));assert repair<F(1,10**12)
    B=[[I.of(F(float(v))) for v in row] for row in cfg['beta']]
    alpha=[I.of(F(float(x))) for x in cfg['alpha']];delta=[I.of(F(float(x))) for x in cfg['delta']];gamma=[I.of(F(float(x))) for x in cfg['gamma']]
    q=[I.of(F(float(x))) for x in cfg['q']];g=[I.of(F(float(x))) for x in cfg['g']];hh=[I.of(F(float(x))) for x in cfg['h']]
    parents=[[j for j in range(6) if cfg['beta'][j][i]] for i in range(6)]
    y=[I.of(F(float(x))) for x in cfg['x0']]+[ZERO,ZERO]
    sens=[[ZERO for _ in range(84)] for _ in range(8)]
    h=I.of(F(5,144));half=I.of(F(1,2));sixth=I.of(F(1,6))
    def combine(y,sy,f,sg,c):
        return [x+c*v for x,v in zip(y,f)],[[x+c*v for x,v in zip(row,gr)] for row,gr in zip(sy,sg)]
    for k in range(6):
        sk=[I.of(v) for v in z[k*12:k*12+6]];rk=[I.of(v) for v in z[k*12+6:k*12+12]];ak=[I.of(v) for v in z[72+2*k:74+2*k]]+[ZERO]*4
        def rhs(y,sy):
            ex=[alpha[i]*ak[i]+sum((B[j][i]*(1-sk[j])*y[j] for j in parents[i]),ZERO) for i in range(6)]
            f=[(1-y[i])*ex[i]-(delta[i]+gamma[i]*rk[i])*y[i] for i in range(6)]
            f += [sum((q[i]*y[i]+hh[i]*sk[i]+half*(sk[i]*sk[i]+rk[i]*rk[i]) for i in range(6)),ZERO),sum((-g[i]*y[i]+half*ak[i]*ak[i] for i in range(6)),ZERO)]
            ds=[]
            for i in range(6):
                diag=-ex[i]-delta[i]-gamma[i]*rk[i]
                off=[(j,(1-y[i])*B[j][i]*(1-sk[j])) for j in parents[i]]
                row=[diag*sy[i][c]+sum((v*sy[j][c] for j,v in off),ZERO) for c in range(84)]
                for j in parents[i]:row[k*12+j]=row[k*12+j]-(1-y[i])*B[j][i]*y[j]
                row[k*12+6+i]=row[k*12+6+i]-gamma[i]*y[i]
                if i<2:row[72+2*k+i]=row[72+2*k+i]+alpha[i]*(1-y[i])
                ds.append(row)
            dr=[sum((q[i]*sy[i][c] for i in range(6)),ZERO) for c in range(84)]
            ar=[sum((-g[i]*sy[i][c] for i in range(6)),ZERO) for c in range(84)]
            for i in range(6):dr[k*12+i]=dr[k*12+i]+hh[i]+sk[i];dr[k*12+6+i]=dr[k*12+6+i]+rk[i]
            for i in range(2):ar[72+2*k+i]=ar[72+2*k+i]+ak[i]
            return f,ds+[dr,ar]
        for _ in range(48):
            f1,g1=rhs(y,sens);y2,s2=combine(y,sens,f1,g1,h*half)
            f2,g2=rhs(y2,s2);y3,s3=combine(y,sens,f2,g2,h*half)
            f3,g3=rhs(y3,s3);y4,s4=combine(y,sens,f3,g3,h)
            f4,g4=rhs(y4,s4)
            y=[yy+h*sixth*(u+2*v+2*w+t) for yy,u,v,w,t in zip(y,f1,f2,f3,f4)]
            sens=[[yy+h*sixth*(u+2*v+2*w+t) for yy,u,v,w,t in zip(ry,r1,r2,r3,r4)] for ry,r1,r2,r3,r4 in zip(sens,g1,g2,g3,g4)]
        print('interval_slot',k+1,flush=True)
    grad=sens[6][:72]+sens[7][72:]
    mid=[F(v.lo+v.hi,2*SCALE) for v in grad];rad=[F(v.hi-v.lo,2*SCALE) for v in grad]
    w=[F(0)]*84
    for ix,cap in zip(blocks,caps_eval):
        left=cap
        for j in sorted(ix,key=lambda j:mid[j]):
            if mid[j]>=0:break
            w[j]=min(F(1),left);left-=w[j]
            if not left:break
    gap=sum((v*(x-ww) for v,x,ww in zip(mid,z,w)),F(0));err=sum(rad,F(0))
    upper=gap+err;assert 0<=gap and err<F(1,10**16)
    obj=dict(object='C0 exact-arithmetic RK4, binary64 coefficients interpreted as reals',precision_fractional_bits=P,candidate_source='D7 G_controls.json retained unmodified',exact_feasibility_repair_max=str(repair),candidate=[str(x) for x in z],capacities=[str(x) for x in caps_eval],feasibility_repair_capacities=[str(x) for x in caps],gradient_intervals=[v.box() for v in grad],gradient_width_max=str(max(2*x for x in rad)),objective_D_interval=y[6].box(),objective_minus_A_interval=y[7].box(),linear_VI_gap_mid=str(gap),linear_VI_gap_error=str(err),linear_VI_gap_upper=str(upper),linear_minimizer=[str(x) for x in w],floating_program_execution_certified=False,Nash_gap_certified=False,ODE_VI_gap_certified=False,seconds=time.perf_counter()-start,summary=dict(gap_upper=float(upper),repair_max=float(repair),gradient_width_max=float(max(2*x for x in rad))))
    (OUT/'results/candidate_VI_interval_certificate.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8');print(obj['summary'],flush=True)
if __name__=='__main__':main()
