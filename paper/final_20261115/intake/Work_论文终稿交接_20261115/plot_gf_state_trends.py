"""Plot empirically supplied G/F state trajectories WITHOUT inventing measurements.

Input CSV must contain columns:
scenario, plan, time, x1, x2, x3, x4, x5, x6
where plan is G or F and scenario defaults to aG.
The caller must ensure both G/F are evaluated under the SAME frozen execution attack.
Run after exporting trajectories from the original simulation:
  python plot_gf_state_trends.py figure_data/gf_states_common_attack.csv --scenario aG
No sample or synthetic data are bundled.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager,FontProperties

CJK='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if Path(CJK).exists():
    fontManager.addfont(CJK)
    plt.rcParams['font.family']=FontProperties(fname=CJK).get_name()
plt.rcParams['axes.unicode_minus']=False

p=argparse.ArgumentParser()
p.add_argument('csv',type=Path)
p.add_argument('--scenario',default='aG',help='Common execution attack scenario, not optimizer predicted attack')
p.add_argument('--output',type=Path,default=Path('figures/fig4_4_GF_state_trends.png'))
a=p.parse_args()
raw=pd.read_csv(a.csv)
needed=['scenario','plan','time']+[f'x{i}' for i in range(1,7)]
missing=[s for s in needed if s not in raw]
if missing: raise ValueError('Missing columns: '+str(missing))
data=raw[raw.scenario==a.scenario].copy()
plans={label:data[data.plan==label].sort_values('time') for label in ('G','F')}
for label, sub in plans.items():
    if sub.empty: raise ValueError(f'Missing plan {label} for {a.scenario}')
    if sub.time.duplicated().any(): raise ValueError(f'Duplicate timestamps: {label}')
    if not np.isfinite(sub[needed[2:]].to_numpy(dtype=float)).all():raise ValueError(f'Nonfinite input: {label}')
    xs=sub[[f'x{i}' for i in range(1,7)]].to_numpy(float)
    if xs.min()<-1e-10 or xs.max()>1+1e-10:raise ValueError(f'State out of [0,1]: {label}')
    sub['weighted']=(xs@np.array([1,1,1,1,4,1],dtype=float))/9
if len(plans['G'])!=len(plans['F']) or not np.allclose(plans['G'].time.to_numpy(),plans['F'].time.to_numpy(),atol=1e-9,rtol=0):
    raise ValueError('G/F must use the same time grid; interpolate only via independently validated simulation output')
if not np.allclose(plans['G'].iloc[0][[f'x{i}' for i in range(1,7)]].to_numpy(float),plans['F'].iloc[0][[f'x{i}' for i in range(1,7)]].to_numpy(float),atol=1e-8,rtol=0):
    raise ValueError('G/F initial states differ')
fig, axes=plt.subplots(1,3,figsize=(13,3.8),sharex=True)
labels=[('x1','API网关受损比例'),('x5','核心数据库受损比例'),('weighted','全网价值加权受损程度')]
for ax,(column,title) in zip(axes,labels):
    for label, color, ls in [('G','#376b9b','-'),('F','#c58e43','--')]:
        sub=plans[label]
        ax.plot(sub.time,sub[column],color=color,linestyle=ls,label=label,lw=1.8)
    ax.set_title(title);ax.set_xlabel('模型时间 t');ax.grid(alpha=.25);ax.legend(frameon=False)
axes[0].set_ylabel('归一化受损比例');fig.suptitle(f'公共攻击 {a.scenario} 下 G/F 状态轨迹（同一初态、同一执行攻击）')
fig.tight_layout()
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=240,bbox_inches='tight');plt.close(fig)
print('figure:',a.output)
