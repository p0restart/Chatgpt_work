"""Precision, independent ODE, boundary and source integrity checks for Work E."""
from pathlib import Path
import sys,json,time,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp,quad
from scipy.optimize import linprog
from diagnostics import load,OUT,fg,unpack,pack,jacobian,line_radius,dump
from src.core import simulate,check_controls
from src.game_solver import ResponseProblem

def independent(m,z):
    a,s,r=unpack(z);K=len(a);dt=10/K
    y=np.r_[m.x0,0.,0.]
    for k in range(K):
        def rhs(t,y):
            x=y[:6];exposure=m.alpha*a[k]
            # Deliberately use an explicit edge loop rather than dynamics().
            exposure=exposure.copy()
            for j,i in zip(*np.nonzero(m.beta)):
                exposure[i]+=m.beta[j,i]*(1-m.epsilon[j]*s[k,j])*x[j]
            f=(1-x)*exposure-(m.delta+m.gamma*r[k])*x
            jd=sum(m.q*x+m.h*s[k]+.5*m.c_s*s[k]**2+.5*m.c_r*r[k]**2)
            ma=sum(-m.g*x+.5*m.c_a*a[k]**2)
            return np.r_[f,jd,ma]
        sol=solve_ivp(rhs,(k*dt,(k+1)*dt),y,method='DOP853',rtol=1e-12,atol=1e-14)
        assert sol.success;y=sol.y[:,-1]
    return y[6:]+np.array([m.omega@y[:6],-m.nu@y[:6]])

def vi_metrics(m,z):
    vals,g=fg(m,z);a,s,r=unpack(z)
    d=ResponseProblem(m,a,s,r,10,48,'D');ap=ResponseProblem(m,a,s,r,10,48,'A')
    C=np.zeros((12,84));C[:6,:72]=d.C;C[6:,72:]=ap.C
    lp=linprog(g,A_ub=C,b_ub=np.r_[np.full(6,m.B),np.full(6,m.A)],bounds=[(0,1)]*84,method='highs')
    assert lp.success
    # Duality/linear VI gap, computable without solving nonconvex responses.
    linear_gap=float(g@(z-lp.x))
    return dict(J_D=vals[0],J_A=-vals[1],natural_residual_inf=max(d.projected_residual(d.initial,g[:72]),ap.projected_residual(ap.initial,g[72:])),linear_VI_gap=linear_gap,LP_success=lp.success,LP_status=lp.status)

def finish():
    manifest=json.loads((OUT/'source_manifest.json').read_text(encoding='utf-8'));changed=[p for p,h in manifest.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    dump(OUT/'results/source_immutability.json',dict(files_checked=len(manifest),changed=changed,passed=not changed))
    assert not changed
    df=pd.read_csv(OUT/'E3_experiment_results.csv')
    worst=str(df.loc[df.lambda_H.idxmin(),'point'])
    dump(OUT/'results/refinement_completed.json',dict(completed=True,worst_point=worst))

def main():
    # Resume only final source verification after a post-computation error;
    # never recompute or overwrite already retained precision experiments.
    ready=['hessian_refinement.csv','integration_checks.csv','feasible_direction_checks.csv','VI_residuals.csv','coarse_global_bound.json']
    if all((OUT/'results'/p).exists() for p in ready):
        assert len(pd.read_csv(OUT/'results/hessian_refinement.csv'))==2
        assert len(pd.read_csv(OUT/'results/integration_checks.csv'))==15
        finish();print('REUSED_COMPLETED_PRECISION_RESULTS; source verification completed',flush=True);return
    m,pair=load();df=pd.read_csv(OUT/'E3_experiment_results.csv')
    assert len(df)==5
    worst=str(df.loc[df.lambda_H.idxmin(),'point']);stored=np.load(OUT/f'results/{worst}.npz');z=stored['z']
    refinements=[]
    for eps,H in [(1e-5,48),(1e-4,96)]:
        J,seconds=jacobian(m,z,eps,H);S=(J+J.T)/2
        row=dict(point=worst,fd_step=eps,H_steps=H,lambda_D=np.linalg.eigvalsh(S[:72,:72])[0],lambda_A=np.linalg.eigvalsh(S[72:,72:])[0],lambda_H=np.linalg.eigvalsh(S)[0],J_max_difference=np.max(abs(J-stored['J'])),hessian_seconds=seconds)
        refinements.append(row);np.savez(OUT/f'results/refine_{H}_{eps}.npz',J=J,H=S)
        pd.DataFrame(refinements).to_csv(OUT/'results/hessian_refinement.csv',index=False)
        print(row,flush=True)
    checks=[];boundary=[]
    for name in df.point:
        data=np.load(OUT/f'results/{name}.npz');zz=data['z'];base=fg(m,zz)[0];ode=independent(m,zz)
        sims={H:simulate(m,*unpack(zz),10,H) for H in (48,96,192)}
        for H in (48,96,192):
            vals,grad=fg(m,zz,H)
            checks.append(dict(point=name,kind='objective',H=H,step=0,value_D=vals[0],value_minus_A=vals[1],error_DOP853=float(np.max(abs(vals-ode))),error_simulate=float(np.max(abs(vals-np.array([sims[H]['J_D'],-sims[H]['J_A']])))),gradient_difference_H48=float(np.max(abs(grad-fg(m,zz,48)[1])))))
        # Check curvature in eigen-directions. Boundary candidate uses feasible
        # active-face transfer directions instead of infeasible eigenvectors.
        dirs=[]
        if name!='saved_candidate':
            dirs=[('D_min',np.r_[data['vd'][:,0],np.zeros(12)],0),('A_min',np.r_[np.zeros(72),data['va'][:,0]],1),('H_min',data['vh'][:,0],None)]
        else:
            for k in range(6):
                inds=k*12+np.arange(12);free=inds[zz[inds]>1e-5]
                if len(free)>1:
                    v=np.zeros(84);v[free[0]]=1/np.sqrt(2);v[free[1]]=-1/np.sqrt(2);dirs.append((f'face_D{k}',v,0))
        for label,v,player in dirs:
            radius=line_radius(m,zz,v)
            pred=float(v@data['H']@v)
            for eps in (1e-3,1e-4,1e-5):
                step=min(eps,.1*radius)
                if step<1e-10:continue
                check_controls(m,*unpack(zz+step*v));check_controls(m,*unpack(zz-step*v))
                gp=fg(m,zz+step*v)[1];gm=fg(m,zz-step*v)[1]
                rayleigh=float(v@(gp-gm)/(2*step))
                # Scalar second difference has cancellation, so retain both.
                scalar=None;ind=None
                if player is not None:
                    scalar=float((fg(m,zz+step*v)[0][player]-2*base[player]+fg(m,zz-step*v)[0][player])/step**2)
                    if eps==1e-3:
                        ind=float((independent(m,zz+step*v)[player]-2*ode[player]+independent(m,zz-step*v)[player])/step**2)
                boundary.append(dict(point=name,direction=label,step=step,feasible_radius=radius,predicted=pred,gradient_difference=rayleigh,error=abs(rayleigh-pred),scalar_second_difference=scalar,DOP853_second_difference=ind))
        print('precision_checked',name,flush=True)
    pd.DataFrame(checks).to_csv(OUT/'results/integration_checks.csv',index=False)
    pd.DataFrame(boundary).to_csv(OUT/'results/feasible_direction_checks.csv',index=False)
    vis=[]
    for name in df.point:
        zz=np.load(OUT/f'results/{name}.npz')['z'];vis.append(dict(point=name,**vi_metrics(m,zz)))
    pd.DataFrame(vis).to_csv(OUT/'results/VI_residuals.csv',index=False)
    # A valid but deliberately coarse B-object global curvature lower bound.
    b=float(np.max(m.beta.sum(axis=0)));bn=float(np.max(np.sqrt((m.beta**2).sum(axis=0))))
    ell=b-float(m.delta.min());M=float(np.sqrt(bn**2+max(m.gamma)**2));N=2*bn+float(max(m.gamma))
    y=lambda t:M*np.expm1(ell*t)/ell
    w=lambda t:quad(lambda tau:np.exp(ell*(t-tau))*(2*b*y(tau)**2+2*N*y(tau)),0,t,epsabs=1e-8)[0]
    state_bound=float(sum(m.q)*quad(w,0,10,epsabs=1e-6)[0])
    dump(OUT/'results/coarse_global_bound.json',dict(object='B',matrix_measure_infty_bound=ell,f_u_row_2_bound=M,f_xu_bound=N,defense_direct_modulus=10/6,state_hessian_norm_bound=state_bound,defense_lower_bound=10/6-state_bound,certifies_convexity=False,reason='bound is too conservative; not a negative-curvature example'))
    finish()

if __name__=='__main__':main()
