"""Summarize paired evaluations, budgets, and four-cell effects, including failures."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from handoffs.C2_prepare import ROOT, sha

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def main():
    run=ROOT/'k_refinement'/sys.argv[1]
    meta=read(run/'metadata.json')
    if meta['status']=='RUNNING':
        raise ValueError('Run in progress')
    tab=run/'tables'; tab.mkdir(exist_ok=True)
    figdir=run/'figures'; figdir.mkdir(exist_ok=True)
    quality=[]; paths=[]; paired=[]; controls=[]; budgets=[]; averages=[]; deviations=[]; interactions=[]
    for r in meta['cases']:
        root=run/r['case']
        base=dict(seed=r['seed'],B=r['B'],cell=r['cell'],case_pass=r['passed'])
        inputs=read(root/'inputs.json')
        old=read(Path(inputs['history'])/'fine_audit.json')
        for K,ev in [(6,read(root/'baseline.json')),(12,read(root/'warm/evaluation.json'))]:
            krow={**base,'K':K}
            G=old if K==6 else r['paths'][0]
            quality.append(dict(**krow,J_D=ev['J_D'],J_A=ev['J_A'],
                gap_D=G['gap_D'],gap_A=G['gap_A'],relative_D=G['relative_D'],relative_A=G['relative_A'],
                residual_D=ev['residual']['D'],residual_A=ev['residual']['A'],
                violation=max(ev['violation'].values()),**{f'integration_{p}':v for p,v in ev['errors'].items()},
                optimizer_success=(all(G[p]['all_starts_success'] for p in ('D','A')) if K==6 else G['optimizer_failures']==0)))
            a,s,rr=map(np.array,ev['controls'])
            du=np.array(ev['defense_use']); au=np.array(ev['attack_use'])
            bound=np.abs(du-r['B'])<=1e-6
            for j in range(K):
                time=dict(slot=j,t_start=j*10/K,t_end=(j+1)*10/K)
                budgets.append(dict(**krow,**time,defense_use=du[j],attack_use=au[j],
                                    defense_binding=bool(bound[j]),attack_binding=bool(abs(au[j]-.8)<=1e-6)))
                for node in (2,3):
                    controls.append(dict(**krow,**time,node=node,s=s[j,node],r=rr[j,node]))
            for window,sl in [('all',slice(None)),('early',slice(0,K*2//3)),('late',slice(K*2//3,None))]:
                averages.append(dict(**krow,window=window,binding_fraction=float(bound[sl].mean()),
                      defense_use=float(du[sl].mean()),s2=s[sl,2].mean(),s3=s[sl,3].mean(),
                      r2=rr[sl,2].mean(),r3=rr[sl,3].mean()))
        for path in r['paths']:
            paths.append(dict(**base,**{k:v for k,v in path.items() if k!='errors'},
                              **{f'integration_{p}':v for p,v in path['errors'].items()}))
        for player,values in r['cross'].items():
            deviations.append(dict(**base,player=player,optimizer_success=r['cross_success'],**values))
        pair=quality[-2:]
        paired.append(dict(**base,**{f'{p}_K{k}':row[p] for k,row in zip((6,12),pair) for p in ('J_D','J_A')},
                      delta_J_D=pair[1]['J_D']-pair[0]['J_D'],delta_J_A=pair[1]['J_A']-pair[0]['J_A'],
                      stable_distance=r['stable_distance'],**read(root/'cross_evaluation.json')))
    for name,rows in [('solver_quality',quality),('all_paths',paths),('paired_objectives',paired),
                      ('controls',controls),('budgets',budgets),('allocations',averages),('cross_class',deviations)]:
        pd.DataFrame(rows).to_csv(tab/f'{name}.csv',index=False)
    if not quality:
        return
    al=pd.DataFrame(averages)
    for (seed,b),p in pd.DataFrame(paired).groupby(['seed','B']):
        if len(p)!=4:
            continue
        p=p.set_index('cell')
        def did(x):
            return float((x.D-x.C)-(x.B-x.A))
        v6,v12=[did(p[f'J_D_K{k}']) for k in (6,12)]
        a=al[(al.seed==seed)&(al.B==b)]
        checks=[]
        for (window,k),g in a.groupby(['window','K']):
            for c in ('s2','s3','r2','r3'):
                checks.append(dict(window=window,K=k,channel=c,interaction=did(g.set_index('cell')[c])))
        ch=pd.DataFrame(checks).pivot(index=['window','channel'],columns='K',values='interaction').reset_index()
        ch['above_resolution_K6']=abs(ch[6])>.001
        ch['above_resolution_K12']=abs(ch[12])>.001
        ch['reversal']=ch.above_resolution_K6&(ch[6]*ch[12]<0)
        reversals=ch[ch.reversal]
        ch.to_csv(tab/f'allocation_interaction_seed{seed}_B{b}.csv',index=False)
        sign=lambda v: 0 if abs(v)<=4e-6 else int(np.sign(v))
        interactions.append(dict(seed=int(seed),B=float(b),I6=v6,I12=v12,delta=v12-v6,
                     relative_change=(v12-v6)/abs(v6) if abs(v6)>1e-6 else None,
                     sign6=sign(v6),sign12=sign(v12),allocation_reversals=len(reversals),
                     effects_below_resolution_after_refinement=int((ch.above_resolution_K6&~ch.above_resolution_K12).sum()),
                     effects_above_resolution_after_refinement=int((~ch.above_resolution_K6&ch.above_resolution_K12).sum()),
                     numerical_pass=bool(p.case_pass.all()),
                     stable=bool(p.case_pass.all() and sign(v6)==sign(v12)!=0 and len(reversals)==0)))
    pd.DataFrame(interactions).to_csv(tab/'interactions.csv',index=False)
    df=pd.DataFrame(controls)
    palette={6:'#656970',12:'#176d89'}
    for (seed,b),data in df.groupby(['seed','B']):
        fig,axs=plt.subplots(4,4,figsize=(10,7),sharex=True,sharey='col',layout='constrained')
        for i,cell in enumerate('ABCD'):
            for j,(kind,node) in enumerate([('s',2),('s',3),('r',2),('r',3)]):
                ax=axs[i,j]
                for k in (6,12):
                    x=data[(data.cell==cell)&(data.node==node)&(data.K==k)].sort_values('slot')
                    if not x.empty:
                        ax.stairs(x[kind],np.r_[x.t_start,10],baseline=None,color=palette[k],linestyle='--' if k==6 else '-',
                                  linewidth=1.5,label=f'K = {k}')
                ax.spines[['top','right']].set_visible(False)
                ax.set_xticks([0,5,10])
                if i==0: ax.set_title(f'${kind}_{node}(t)$')
                if j==0: ax.set_ylabel(f'Cell {cell}')
                if i==3: ax.set_xlabel('Time')
        axs[0,3].legend(frameon=False,fontsize=8)
        fig.suptitle(f'Control trajectories | seed {seed}, B = {b}')
        for j,(kind,node) in enumerate([('s',2),('s',3),('r',2),('r',3)]):
            ymax=max(.001,float(data.loc[data.node==node,kind].max())*1.12)
            axs[0,j].set_ylim(-.03*ymax,ymax)
        fig.canvas.draw()
        rect=np.array([ax.get_position().bounds for ax in axs.flat]).reshape(4,4,4)
        alignment=max(float(np.ptp(rect[:,:,0],axis=0).max())*fig.get_figwidth()*72,
                      float(np.ptp(rect[:,:,1],axis=1).max())*fig.get_figheight()*72,
                      float(np.ptp(rect[:,:,2]))*fig.get_figwidth()*72,
                      float(np.ptp(rect[:,:,3]))*fig.get_figheight()*72)
        (figdir/f'controls_seed{seed}_B{b}.alignment.json').write_text(
            json.dumps(dict(max_alignment_error_pt=float(alignment),passed=bool(alignment<=1.5))))
        if alignment>1.5:
            raise RuntimeError(f'Panel alignment failed: {alignment:.3g} pt')
        for ext in ('png','pdf'): fig.savefig(figdir/f'controls_seed{seed}_B{b}.{ext}',dpi=300)
        plt.close(fig)
    if interactions:
        fig,ax=plt.subplots(figsize=(5,3.3),layout='constrained')
        for row in interactions:
            ax.plot([6,12],[row['I6'],row['I12']],marker='o',label=f"Seed {row['seed']}, B = {row['B']}")
        ax.set(xlabel='Control slots K',ylabel='$I_J$',xticks=[6,12])
        ax.axhline(0,color='.6',lw=.8)
        ax.spines[['top','right']].set_visible(False)
        ax.legend(frameon=False)
        for ext in ('png','pdf'): fig.savefig(figdir/f'interaction.{ext}',dpi=300)
        plt.close(fig)
    print(pd.DataFrame(interactions).to_string(index=False))
    print(pd.DataFrame(deviations).groupby('player')[['improvement','relative']].max())
    files=[p for p in run.rglob('*') if p.is_file() and p.name!='manifest.json']
    files.extend([Path(__file__),Path('reviews/APPROVAL_LOG.md')])
    (run/'manifest.json').write_text(json.dumps({str(p):sha(p) for p in files},indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
