"""Symbolically verify all six original-model first/second derivative formulas."""
from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
import sympy as s
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work_e_r1'
def main():
    x=s.symbols('x0:6');ss=s.symbols('s0:6');r=s.symbols('r0:6');a=s.symbols('a0:6');y=s.symbols('y0:6');vs=s.symbols('vs0:6');vr=s.symbols('vr0:6')
    cfg=json.loads((OUT/'run_config.json').read_text(encoding='utf-8'))['model'];b=s.Matrix([[s.Symbol(f'b{j}_{i}') if cfg['beta'][j][i] else 0 for i in range(6)] for j in range(6)]);checks=[]
    al=s.symbols('alpha0:6');de=s.symbols('delta0:6');ga=s.symbols('gamma0:6')
    for i in range(6):
        z=al[i]*a[i]+sum(b[j,i]*(1-ss[j])*x[j] for j in range(6));d=de[i]+ga[i]*r[i]
        f=(1-x[i])*z-d*x[i]
        fx=sum(s.diff(f,x[j])*y[j] for j in range(6));fu=sum(s.diff(f,ss[j])*vs[j]+s.diff(f,r[j])*vr[j] for j in range(6))
        expected_fx=-(z+d)*y[i]+(1-x[i])*sum(b[j,i]*(1-ss[j])*y[j] for j in range(6))
        expected_fu=-(1-x[i])*sum(b[j,i]*x[j]*vs[j] for j in range(6))-ga[i]*x[i]*vr[i]
        fxx=sum(s.diff(fx,x[j])*y[j] for j in range(6));fxu=sum(s.diff(fx,ss[j])*vs[j]+s.diff(fx,r[j])*vr[j] for j in range(6))
        expected_fxx=-2*y[i]*sum(b[j,i]*(1-ss[j])*y[j] for j in range(6))
        expected_fxu=y[i]*sum(b[j,i]*x[j]*vs[j] for j in range(6))-(1-x[i])*sum(b[j,i]*y[j]*vs[j] for j in range(6))-ga[i]*y[i]*vr[i]
        for label,expr in [('fx',fx-expected_fx),('fu',fu-expected_fu),('fxx',fxx-expected_fxx),('fxu',fxu-expected_fxu)]:
            assert s.expand(expr)==0;checks.append(dict(node=i,formula=label,symbolic_identity=True))
    obj=dict(passed=True,identities=checks,count=len(checks),random_points=0,scope='algebraic derivative identities with symbolic coefficients on the actual edge support; not Hessian convexity proof')
    (OUT/'results/symbolic_derivative_verification.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8');print('Symbolic identities passed',len(checks),flush=True)
if __name__=='__main__':main()
