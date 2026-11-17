"""Frozen-control D7 replay and publication figures. No reoptimization or tuning."""
from pathlib import Path
import sys, json, hashlib, shutil, platform
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
RAW = BASE / 'raw_d7'
def numerical_copy_ignore(directory,names):
    ignored={name for name in names if name in ['__pycache__','figures']}
    p=Path(directory)
    if p.name=='papers' and p.parent.name=='sources':ignored.update(name for name in names if name.endswith('.txt'))
    if p.name=='sources':ignored.add('Hu2023_extracted.txt')
    return ignored
if not RAW.exists():
    shutil.copytree(ROOT/'paper/work_d7', RAW, ignore=numerical_copy_ignore)
sys.path.insert(0, str(RAW/'source_snapshot'))
from src.supplement_c2 import load_model, load_controls
from src.core import simulate, check_controls
OUT=BASE/'results'; OUT.mkdir(exist_ok=True)
FIG=BASE/'figures'; FIG.mkdir(exist_ok=True)
QA=FIG/'qa';QA.mkdir(exist_ok=True)
sys.path.insert(0,str(RAW/'analysis/figure_qa'))
from audit_panel_alignment import require_matplotlib_panel_alignment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],'font.size':8,'axes.titlesize':9,
    'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':8,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False})
COL={'G':'#0072B2','F':'#D55E00','R':'#D55E00','P':'#777777'}
PARTS=['security','business','isolation','recovery','attacker_value','attacker_effort']
checks=[];objectives=[];controls=[];differences=[]

def add(name,error,tolerance=1e-8):
    checks.append(dict(check=name,error=float(error),tolerance=tolerance,passed=bool(error<=tolerance)))

def independent(pre,post,u):
    """Independent augmented DOP853, explicit source-row/destination-column loop."""
    y=np.r_[pre.x0,np.zeros(6)];times=[0.];states=[y[:6].copy()];cum=[y[6:].copy()]
    for k in range(6):
        m=pre if k<3 else post;a,s,r=[v[k] for v in u]
        def rhs(t,z):
            x=z[:6];exposure=m.alpha*a
            for j in range(6):
                for i in range(6):exposure[i]+=m.beta[j,i]*(1-m.epsilon[j]*s[j])*x[j]
            dx=(1-x)*exposure-(m.delta+m.gamma*r)*x
            c=[sum(m.q*x),sum(m.h*s),sum(m.c_s*s*s)/2,sum(m.c_r*r*r)/2,sum(m.g*x),sum(m.c_a*a*a)/2]
            return np.r_[dx,c]
        t=np.linspace(k*10/6,(k+1)*10/6,193)
        sol=solve_ivp(rhs,(t[0],t[-1]),y,method='DOP853',t_eval=t,rtol=1e-12,atol=1e-14)
        if not sol.success:raise RuntimeError(sol.message)
        times.extend(t[1:]);states.extend(sol.y[:6,1:].T);cum.extend(sol.y[6:,1:].T);y=sol.y[:,-1]
    return np.array(times),np.array(states),np.array(cum)

def save(fig,name,axes):
    require_matplotlib_panel_alignment(fig,json_out=QA/f'{name}.alignment.json',
        overlay_svg=QA/f'{name}.alignment.svg',axes=list(np.asarray(axes).ravel()),strict=True)
    for ext in ['png','pdf','svg']:fig.savefig(FIG/f'{name}.{ext}',dpi=400,facecolor='white')
    plt.close(fig)

def state_figure(data,scenario,diff=False):
    fig,axs=plt.subplots(1,3,figsize=(7.2,2.9))
    fig.subplots_adjust(left=.085,right=.99,bottom=.23,top=.72,wspace=.43)
    cols=['x1','x5','xq'];titles=['(a) API网关','(b) 核心数据库','(c) 全网价值加权受损']
    for ax,col,title in zip(axs,cols,titles):
        if diff:
            g=data[data.plan=='G'];f=data[data.plan=='F']
            ax.plot(g.time,(g[col].to_numpy()-f[col].to_numpy())*1000,color=COL['G'],lw=1.3)
            ax.axhline(0,color='#777777',lw=.6)
        else:
            for p,ls in [('G','-'),('F','--')]:
                d=data[data.plan==p];ax.plot(d.time,d[col],label=p,color=COL[p],ls=ls,lw=1.3)
            ax.set_ylim(0, max(data[col])*1.10)
        ax.set(xlabel='模型时间',ylabel='1000 × (G − F)' if diff else '受损比例',title=title,xlim=(0,10),xticks=[0,5,10])
        ax.grid(alpha=.15)
    fig.text(.5,.96,f'公共执行攻击：{scenario}；防御控制固定；B = 1.2',ha='center',fontsize=8)
    if not diff:fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.91),ncol=2,frameon=False)
    name=('figA2_GF_state_difference_' if diff else 'fig4_3_GF_state_common_' if scenario=='aG' else 'figA1_GF_state_common_')+scenario
    save(fig,name,axs)

# Replay all 18 static cross-evaluations; main trajectories retained at H=192.
for B in [.6,1.2,1.8]:
    folder=RAW/f'results/static/B{B}';m=load_model(folder/'model.json')
    attacks=json.loads((folder/'cross_attacks.json').read_text())
    source=pd.read_csv(folder/'cross_evaluation.csv')
    for p in ['G','F']:
        original=load_controls(folder/f'{p}_controls.json');_,s,r=original
        for k in range(6):
            for i in range(6):controls.append(dict(B=B,plan=p,slot=k+1,asset=i+1,t_start=k*10/6,t_end=(k+1)*10/6,s=s[k,i],r=r[k,i],resource=s[k,i]+r[k,i]))
        for scenario in ['a0','aG','aBR_F']:
            a=np.array(attacks[scenario]);u=(a,s,r);check_controls(m,*u)
            t,x,c=independent(m,m,u);d=source[(source.method==p)&(source.attack==scenario)].iloc[0]
            parts=dict(zip(PARTS,c[-1]));jd=sum(c[-1,:4]);ja=c[-1,4]-c[-1,5]
            add(f'static_{B}_{p}_{scenario}_JD',abs(jd-d.J_D))
            for j,key in enumerate(PARTS):add(f'static_{B}_{p}_{scenario}_{key}',abs(c[-1,j]-d[key]))
            objectives.append(dict(B=B,scenario=scenario,plan=p,**parts,J_D=jd,J_A=ja,saved_J_D=d.J_D,JD_error=jd-d.J_D))
            if B==1.2 and scenario in ['aG','a0']:
                df=pd.DataFrame(x,columns=[f'x{i}' for i in range(1,7)])
                df.insert(0,'time',t);df.insert(0,'plan',p);df.insert(0,'scenario',scenario);df['xq']=x@m.q/sum(m.q)
                for j,key in enumerate(PARTS):df['cumulative_'+key]=c[:,j]
                df['cumulative_J_D']=c[:,:4].sum(axis=1)
                path=OUT/f'gf_state_common_{scenario}_{p}.csv';df.to_csv(path,index=False,float_format='%.17g')
                runs={h:simulate(m,*u,10,h) for h in [48,96,192]}
                for h,run in runs.items():
                    stride=192//h
                    add(f'main_{p}_{scenario}_RK4_H{h}_state_vs_DOP853',np.max(abs(run['states']-x[::stride])))
                    add(f'main_{p}_{scenario}_RK4_H{h}_JD_vs_DOP853',abs(run['J_D']-jd))
                for h in [48,96]:
                    add(f'main_{p}_{scenario}_RK4_H{h}_H{2*h}_state',np.max(abs(runs[h]['states']-runs[2*h]['states'][::2])))
                    add(f'main_{p}_{scenario}_RK4_H{h}_H{2*h}_JD',abs(runs[h]['J_D']-runs[2*h]['J_D']))
                add(f'main_{p}_{scenario}_state_domain',max(0,-x.min(),x.max()-1),1e-12)

# Replay all 24 saved rolling executions, including unperturbed control.
for folder in sorted((RAW/'results').glob('rolling_*_B*')):
    B=float(folder.name.rsplit('B',1)[1]);f=folder/f'B{B}'
    pre=load_model(f/'model_pre.json');post=load_model(f/'model_post.json')
    saved=pd.read_csv(folder/'objectives.csv');tr=pd.read_csv(folder/'trajectories.csv')
    for E in ['E0','E1']:
        pairs=[]
        for p in ['P','G','R']:
            u=load_controls(f/f'{E}_{p}_executed.json');pairs.append(u);check_controls(pre,*u)
            t,x,c=independent(pre,post,u)
            for period,cc in [('full',c[-1]),('post',c[-1]-c[576])]:
                d=saved[(saved.evaluation==E)&(saved.method==p)&(saved.H==48)&(saved.period==period)].iloc[0]
                add(f'{folder.name}_{E}_{p}_{period}_JD',abs(sum(cc[:4])-d.J_D))
                for j,key in enumerate(PARTS):add(f'{folder.name}_{E}_{p}_{period}_{key}',abs(cc[j]-d[key]))
            old=tr[(tr.evaluation==E)&(tr.method==p)&(tr.H==48)]
            add(f'{folder.name}_{E}_{p}_state',np.max(abs(x[::4]-old[[f'x{i}' for i in range(6)]].to_numpy())))
        assert all(np.array_equal(pairs[0][0],v[0]) for v in pairs[1:])
        assert all(np.array_equal(pairs[0][j][:3],v[j][:3]) for v in pairs[1:] for j in [1,2])

pd.DataFrame(objectives).to_csv(OUT/'objective_recalculation.csv',index=False,float_format='%.17g')
co=pd.DataFrame(controls);co.to_csv(OUT/'complete_static_defense_controls.csv',index=False,float_format='%.17g')
for scenario in ['aG','a0']:
    data=pd.concat([pd.read_csv(OUT/f'gf_state_common_{scenario}_{p}.csv') for p in ['G','F']],ignore_index=True)
    data.to_csv(OUT/f'gf_state_common_{scenario}.csv',index=False,float_format='%.17g')
    state_figure(data,scenario);state_figure(data,scenario,True)
    g=data[data.plan=='G'];f=data[data.plan=='F'];t=g.time.to_numpy()
    for col in [*[f'x{i}' for i in range(1,7)],'xq']:
        delta=g[col].to_numpy()-f[col].to_numpy()
        differences.append(dict(scenario=scenario,metric=col,G_final=g[col].iloc[-1],F_final=f[col].iloc[-1],final_delta=delta[-1],min_delta=delta.min(),max_delta=delta.max(),t_min=t[delta.argmin()],t_max=t[delta.argmax()],G_lower_count=int((delta<-1e-10).sum()),G_higher_count=int((delta>1e-10).sum()),points=len(t)))
pd.DataFrame(differences).to_csv(OUT/'state_differences.csv',index=False,float_format='%.17g')
# Retain the D7 topology artwork; its numeric edge labels match the copied model.
for ext in ['png','pdf','svg']:
    source=RAW/f'figures/fig1_topology.{ext}'
    if not source.exists():
        source.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT/f'paper/work_d7/figures/fig1_topology.{ext}',source)
    shutil.copyfile(source,FIG/f'fig4_1_topology.{ext}')

df=pd.DataFrame(objectives)
fig,ax=plt.subplots(figsize=(6.2,2.8));fig.subplots_adjust(left=.13,right=.98,bottom=.22,top=.89)
for scenario,color,ls,mark in [('a0','#666666',':','s'),('aG',COL['G'],'-','o'),('aBR_F',COL['F'],'--','^')]:
    vals=[]
    for B in [.6,1.2,1.8]:
        d=df[(df.B==B)&(df.scenario==scenario)].set_index('plan');vals.append((d.loc['G','J_D']-d.loc['F','J_D'])*1000)
    ax.plot([.6,1.2,1.8],vals,label=scenario,color=color,ls=ls,marker=mark,lw=1.2,ms=4)
ax.axhline(0,color='#444444',lw=.7);ax.grid(axis='y',alpha=.15)
ax.set(xlabel='Defense capacity B',ylabel='1000 x [JD(G) - JD(F)]',xticks=[.6,1.2,1.8],ylim=(-.9,.8))
ax.legend(loc='upper right',ncol=3,frameon=False)
save(fig,'fig4_2_common_attack_difference',[ax])

roll=pd.read_csv(RAW/'results/derived/rolling_summary.csv')
d=roll[(roll['case']=='event')&(roll.period=='post')].copy()
d['G_gain_percent']=100*(d.J_D_P-d.J_D_G)/d.J_D_P
d['R_gain_percent']=100*(d.J_D_P-d.J_D_R)/d.J_D_P
d.to_csv(OUT/'rolling_event_post_verified.csv',index=False,float_format='%.17g')
fig,axs=plt.subplots(1,2,figsize=(7.2,2.8));fig.subplots_adjust(left=.11,right=.99,bottom=.23,top=.82,wspace=.35)
for ax,E,title in zip(axs,['E0','E1'],['(a) Fixed executed attack E0','(b) Frozen P-response attack E1']):
    sub=d[d.evaluation==E].sort_values('B')
    for p,ls,mark in [('G','-','o'),('R','--','s')]:
        ax.plot(sub.B,sub[f'{p}_gain_percent'],ls=ls,marker=mark,color=COL[p],lw=1.3,ms=4,label=p)
    ax.set(title=title,xlabel='Defense capacity B',ylabel='Post-event loss reduction (%)',xticks=[.6,1.2,1.8],ylim=(0,.19))
    ax.grid(alpha=.15)
fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.99),ncol=2,frameon=False)
save(fig,'fig4_4_rolling_gain',axs)

fig,axs=plt.subplots(2,2,figsize=(7.2,4.9));fig.subplots_adjust(left=.09,right=.88,bottom=.13,top=.90,wspace=.34,hspace=.49)
for row,p in enumerate(['G','F']):
    sub=co[(co.B==1.2)&(co.plan==p)]
    for col,key in enumerate(['s','r']):
        ax=axs[row,col];z=sub.pivot(index='asset',columns='slot',values=key).to_numpy()
        im=ax.imshow(z,vmin=0,vmax=.4,cmap='Blues',interpolation='nearest',aspect='auto')
        ax.set(title=f'({"abcd"[row*2+col]}) {p}: '+('source isolation s' if key=='s' else 'local recovery r'),
            xlabel='Control interval',ylabel='Asset',xticks=range(6),xticklabels=range(1,7),yticks=range(6),yticklabels=[f'v{i}' for i in range(1,7)])
cax=fig.add_axes([.92,.13,.017,.77]);fig.colorbar(im,cax=cax,label='Normalized intensity')
save(fig,'figA4_GF_defense_actions',axs)

pd.DataFrame(checks).to_csv(OUT/'recalculation_checks.csv',index=False,float_format='%.17g')
summary=dict(passed=all(d['passed'] for d in checks),checks=len(checks),max_error=max(d['error'] for d in checks),static_cross_pairs=18,rolling_pairs=24,
    main_points_per_plan=1153,solver='DOP853 rtol=1e-12 atol=1e-14; RK4 H=48/96/192',
    environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__),scope='Frozen-control replay only. No independent reoptimization or external review.')
(OUT/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
manifest={str(p.relative_to(BASE)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in RAW.rglob('*') if p.is_file() and '__pycache__' not in str(p)}
(BASE/'raw_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2));assert summary['passed']
