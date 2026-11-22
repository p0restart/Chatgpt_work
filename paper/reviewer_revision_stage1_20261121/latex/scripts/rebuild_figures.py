"""Redraw the four paper figures from frozen controls and saved trajectories."""
from pathlib import Path
import json,csv,hashlib,sys
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,FancyArrowPatch
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1]
DATA=R/'data';OUT=R/'figures';OUT.mkdir(exist_ok=True)
def require_matplotlib_panel_alignment(fig,json_out,strict=True):
    """Check equal plot sizes and shared edges for each comparable grid row."""
    fig.canvas.draw()
    axes=[ax for ax in fig.axes if ax.get_subplotspec() is not None]
    rows={}
    for ax in axes:
        spec=ax.get_subplotspec()
        rows.setdefault((spec.rowspan.start,spec.rowspan.stop),[]).append(ax)
    checks=[]
    for group in rows.values():
        if len(group)<2: continue
        boxes=[ax.get_position() for ax in group]
        for prop,scale in [('width',fig.get_figwidth()*72),('height',fig.get_figheight()*72),('y0',fig.get_figheight()*72)]:
            spread=(max(getattr(b,prop) for b in boxes)-min(getattr(b,prop) for b in boxes))*scale
            checks.append({'quantity':prop,'spread_pt':spread})
            assert spread<=1.5
    Path(json_out).write_text(json.dumps({'passed':True,'checks':checks},indent=2))
FONT=font_manager.findfont('Times New Roman',fallback_to_default=False)
mpl.rcParams.update({'font.family':'Times New Roman','font.size':8,'axes.titlesize':8,'axes.labelsize':8,
 'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,
 'svg.fonttype':'none','mathtext.fontset':'custom','mathtext.rm':'Times New Roman',
 'mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold',
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,'path.simplify':False})
names=['API gateway','Web application','Order processing','Identity authentication','Core database','Back-end management']
manifest={'font':Path(FONT).name,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.iterdir() if p.is_file()},'figures':{}}
def save(fig,name,alignment=True):
 fig.canvas.draw()
 if alignment:require_matplotlib_panel_alignment(fig,json_out=OUT/f'{name}_alignment.json',strict=True)
 for ext in ['pdf','svg','png']:
  fig.savefig(OUT/f'{name}.{ext}',dpi=600,facecolor='white')
 manifest['figures'][name]={'width_in':fig.get_figwidth(),'height_in':fig.get_figheight(),'base_font_pt':8}
 plt.close(fig)

# Figure 1: topology, all six assets and all eight directed edges retained.
fig,ax=plt.subplots(figsize=(3.18,2.40));fig.subplots_adjust(0,0,1,1)
pos={0:(.40,1.82),3:(1.56,1.82),5:(2.73,1.82),1:(.40,.50),2:(1.56,.50),4:(2.73,.50)}
edges=[(0,2,.08),(0,3,.09),(1,2,.10),(3,2,.11),(3,4,.07),(3,5,.12),(2,4,.10),(5,4,.05)]
for j,i,b in edges:
 start=np.array(pos[j]);end=np.array(pos[i]);v=(end-start)/np.linalg.norm(end-start)
 ax.add_patch(FancyArrowPatch(start+v*.31,end-v*.32,arrowstyle='-|>',mutation_scale=7,lw=.7,color='#444444'))
 midpoint=(start+end)/2
 shift=np.array([0,.14]) if abs(v[1])<.1 else np.array([.15,0]) if abs(v[0])<.1 else np.array([-v[1],v[0]])*.18
 ax.text(*(midpoint+shift),f'{b:.2f}',ha='center',va='center',fontsize=8)
labels={0:'API\ngateway',1:'Web\napplication',2:'Order\nprocessing',3:'Identity\nauth.',4:'Core\ndatabase',5:'Back-end\nmgmt.'}
for i,xy in pos.items():
 ax.add_patch(Circle(xy,.32,facecolor=('#eee7f8' if i<2 else '#fae5da' if i==4 else '#e4f1f7'),edgecolor='#555555',lw=.7))
 ax.text(xy[0],xy[1]+.17,f'$v_{i+1}$',ha='center',va='center',fontsize=8)
 ax.text(xy[0],xy[1]-.07,labels[i],ha='center',va='center',fontsize=8,linespacing=1.25)
ax.set(xlim=(0,3.18),ylim=(0,2.40));ax.set_aspect('equal');ax.axis('off');save(fig,'fig1_network_en',False)

# Figure 2: same stacked controls and capacity limits, common y scale.
fig,axes=plt.subplots(1,3,figsize=(6.76,2.25),sharey=True)
fig.subplots_adjust(left=.080,right=.995,bottom=.25,top=.78,wspace=.25)
for index,(ax,b) in enumerate(zip(axes,[.6,1.2,1.8])):
 a,s,r=np.array(json.loads((DATA/f'B{b}_G_controls.json').read_text()))
 model=json.loads((DATA/f'B{b}_model.json').read_text())
 iso=s@np.array(model['b_s']);rec=r@np.array(model['b_r'])
 ax.bar(np.arange(1,7),iso,.65,color='#356B8C',label='Source-side isolation',zorder=3)
 ax.bar(np.arange(1,7),rec,.65,bottom=iso,color='#D9AB62',label='Local recovery',zorder=3)
 ax.axhline(b,color='#333333',ls='--',lw=.8,label='Capacity limit')
 ax.set(title=f'({chr(97+index)}) $B_D={b:.1f}$',xticks=range(1,7),ylim=(0,1.96),yticks=[0,.6,1.2,1.8])
 ax.grid(axis='y',lw=.4,color='#dddddd',zorder=0)
axes[0].set_ylabel('Normalized resource use')
fig.supxlabel('Control interval',y=.025,fontsize=8)
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.53,.99),ncol=3,frameon=False)
save(fig,'fig2_capacity_en')

# Figure 3: all 72 original action intensities, rounded only for labels.
_,s,r=np.array(json.loads((DATA/'B1.2_G_controls.json').read_text()))
fig,axes=plt.subplots(1,2,figsize=(6.76,2.75))
fig.subplots_adjust(left=.17,right=.875,bottom=.18,top=.88,wspace=.68)
short=['API gateway','Web application','Order processing','Identity auth.','Core database','Back-end mgmt.']
for i,(ax,values,title) in enumerate(zip(axes,[s,r],['Source-side isolation','Local recovery'])):
 im=ax.imshow(values.T,vmin=0,vmax=.35,cmap='Blues',aspect='auto')
 ax.set(xticks=range(6),xticklabels=range(1,7),yticks=range(6),yticklabels=short,xlabel='Control interval',title=f'({chr(97+i)}) {title}')
 ax.tick_params(length=0)
 ax.set_xticks(np.arange(-.5,6,1),minor=True);ax.set_yticks(np.arange(-.5,6,1),minor=True)
 ax.grid(which='minor',color='white',lw=.8);ax.tick_params(which='minor',length=0)
 for k in range(6):
  for j in range(6):ax.text(k,j,f'{values[k,j]:.2f}',ha='center',va='center',fontsize=8,color='white' if values[k,j]>.20 else '#253c50')
cbax=fig.add_axes([.90,.18,.014,.70]);cb=fig.colorbar(im,cax=cbax);cb.set_label('Control intensity');cb.ax.tick_params(labelsize=8)
save(fig,'fig3_actions_en')

# Figure 4: all 289 samples of each saved plan, with no smoothing/subsampling.
rows=list(csv.DictReader((DATA/'fig4_states.csv').open(encoding='utf-8-sig')))
plans={n:[v for v in rows if v['plan']==n] for n in ['G','M','N']}
fig,axes=plt.subplots(2,2,figsize=(6.76,4.10),sharex=True)
fig.subplots_adjust(left=.085,right=.975,bottom=.13,top=.85,wspace=.24,hspace=.42)
titles=['API gateway','Identity authentication','Core database','Network value-weighted']
fields=['x_v1','x_v4','x_v5','X_q']
styles=[('G','G: Dynamic','#2166AC','-'),('M','M: Fixed mean','#AF5808','--'),('N','N: No defense','#AD2B46',':')]
for i,(ax,field) in enumerate(zip(axes.flat,fields)):
 for name,label,color,ls in styles:
  t=np.array([float(v['t']) for v in plans[name]]);v=np.array([float(q[field]) for q in plans[name]])
  assert len(t)==289
  line,=ax.plot(t,v,label=label,color=color,ls=ls,lw=1.15)
  np.testing.assert_array_equal(line.get_xydata(),np.column_stack((t,v)))
 ax.axvline(25/3,lw=.6,color='#888888',zorder=0)
 ax.set(title=f'({chr(97+i)}) {titles[i]}',xlim=(0,10),ylim=(0,None),xticks=range(0,11,2))
 ax.grid(axis='y',lw=.4,color='#dddddd')
fig.supylabel('Compromised fraction',x=.007,y=.49,fontsize=8)
fig.supxlabel('Normalized time $t$',y=.025,fontsize=8)
fig.legend(*axes[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.54,.99),ncol=3,frameon=False)
save(fig,'fig4_states_en')
(OUT/'figure_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Exported four figures; frozen samples retained')
