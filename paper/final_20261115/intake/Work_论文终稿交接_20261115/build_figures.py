from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.font_manager import FontProperties, fontManager
F=Path(__file__).parent/'figures'; F.mkdir(exist_ok=True)
CJK='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fontManager.addfont(CJK)
FONT=FontProperties(fname=CJK).get_name()
plt.rcParams.update({'font.family':FONT,'axes.unicode_minus':False,'font.size':10,'savefig.dpi':240})
assets={1:'API网关',2:'Web应用',3:'订单处理',4:'身份认证',5:'核心数据库',6:'后台管理'}
edges=[(1,3,.08),(1,4,.09),(2,3,.10),(4,3,.11),(4,5,.07),(4,6,.12),(3,5,.10),(6,5,.05)]
G=nx.DiGraph(); G.add_nodes_from(assets);G.add_weighted_edges_from(edges)
pos={1:(0,1.6),2:(0,-1.25),4:(2.7,2.15),3:(3.0,-.45),6:(5.2,1.9),5:(6.2,-.2)}
fig, (ax,ax2)=plt.subplots(1,2,figsize=(13.5,4.8), gridspec_kw={'width_ratios':[1.35,1]})
nx.draw_networkx_nodes(G,pos,ax=ax,nodelist=[1,2],node_size=2600,node_color='#cfe4fc',edgecolors='#40678b',linewidths=1.4)
nx.draw_networkx_nodes(G,pos,ax=ax,nodelist=[3,4,6],node_size=2600,node_color='#e9ebf0',edgecolors='#5a6270',linewidths=1.4)
nx.draw_networkx_nodes(G,pos,ax=ax,nodelist=[5],node_size=2600,node_color='#f7dbad',edgecolors='#b77a28',linewidths=1.6)
nx.draw_networkx_labels(G,pos,labels={n:f'v{n}\n{assets[n]}' for n in assets},font_family=FONT,font_size=10,ax=ax)
nx.draw_networkx_edges(G,pos,ax=ax,arrowstyle='-|>',arrowsize=19,node_size=2800,edge_color='#606c80',width=1.45,connectionstyle='arc3,rad=0.01')
# labels hand placed near their arrows to minimize crossings
lab={(1,3):(1.55,.43),(1,4):(1.4,2.05),(2,3):(1.6,-.98),(4,3):(3.28,.9),(4,5):(4.35,1.1),(4,6):(4.0,2.43),(3,5):(4.52,-.64),(6,5):(5.95,1.14)}
for u,v,w in edges:
    xx,yy=lab[(u,v)];ax.text(xx,yy,f'{w:.2f}',fontsize=9,ha='center',va='center',bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1.6})
ax.set_xlim(-.72,7.25);ax.set_ylim(-2,3.2);ax.set_axis_off();ax.set_title('(a) 六类资产及有效攻击传播边',fontweight='bold')
vals=[.463738,.225360,.140469,.076786,.062960,.005190]
ax2.barh(np.arange(6),vals,color=['#4474a8','#6d91b9','#839cb5','#869fac','#c79c53','#a5acb9'])
ax2.set_yticks(np.arange(6),[assets[i] for i in range(1,7)]);ax2.invert_yaxis();ax2.set_xlim(0,.55)
ax2.set_xlabel('六区间平均隔离 + 恢复资源强度')
for i,v in enumerate(vals): ax2.text(v+.012,i,f'{v:.6f}',va='center',fontsize=9)
ax2.set_title('(b) B=1.2 的逐资产平均投入',fontweight='bold');ax2.grid(axis='x',alpha=.14)
fig.tight_layout(w_pad=2);fig.savefig(F/'fig4_1_topology_actions.png',bbox_inches='tight');plt.close(fig)

cap=[.6,1.2,1.8];da0=[.000625,.000432,.000407];dag=[-.000633,-.000434,-.000409];daf=[-.000788,-.000516,-.000480]
fig,ax=plt.subplots(figsize=(9.7,4.8)); xx=np.arange(3);ww=.23
for ofs, data, lab, col in [(-ww,da0,'固定攻击 a0','#7091b2'),(0,dag,'G 攻击响应 aG','#d0a15e'),(ww,daf,'F 攻击响应 aBR,F','#749f91')]:
    rr=ax.bar(xx+ofs,np.array(data)*1000,width=ww,label=lab,color=col)
    for bar,v in zip(rr,data):
        y=bar.get_height();dy=.025 if y>=0 else -.025
        ax.text(bar.get_x()+bar.get_width()/2,y+dy,f'{v:+.6f}',ha='center',va='bottom' if y>=0 else 'top',fontsize=8)
ax.axhline(0,c='#444444',lw=.85);ax.set_xticks(xx,[f'B={c:.1f}' for c in cap]);ax.set_ylim(-.99,.82)
ax.set_ylabel('G−F 的综合损失差（×0.001）');ax.set_title('同一公共攻击下两种防御配置的损失差',fontweight='bold');ax.legend(frameon=False,ncol=3,loc='lower left',fontsize=9);ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(F/'fig4_2_common_attack_difference.png',bbox_inches='tight');plt.close(fig)

cases=['B=0.6 / E0','B=0.6 / E1','B=1.2 / E0','B=1.2 / E1','B=1.8 / E0','B=1.8 / E1']
g=[.040393,.117591,.057912,.165432,.059432,.172527];r=[.045501,.110316,.065226,.156664,.067461,.163117]
fig,ax=plt.subplots(figsize=(10.2,4.8));xx=np.arange(6);ww=.36
ax.bar(xx-ww/2,g,width=ww,label='博弈重规划 G',color='#517d9f')
ax.bar(xx+ww/2,r,width=ww,label='固定观测攻击滚动优化 R',color='#d2a36d')
ax.set_xticks(xx,cases,rotation=18,ha='right');ax.set_ylim(0,.2)
ax.set_ylabel('相对继承原计划 P 的事件后损失降低（%）');ax.set_title('攻击效率改变后重新规划的条件性改善',fontweight='bold')
ax.legend(frameon=False);ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(F/'fig4_3_rolling_gain.png',bbox_inches='tight');plt.close(fig)
print('created',*[p.name for p in F.glob('*.png')])
