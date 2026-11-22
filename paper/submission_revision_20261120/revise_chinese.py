"""Synchronize the verified English additions into the supplied Chinese DOCX."""
from pathlib import Path
from copy import deepcopy
import re, sys, json, hashlib, zipfile
from lxml import etree as E
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.shared import Pt

R=Path(__file__).resolve().parent
ROOT=R.parents[1]
SOURCE=ROOT/'reports/conference_word_audit_20261120/input/1119-final-基于非零和微分博弈的有限资源网络防御决策方法.docx'
OUT=R/'基于非零和微分博弈的有限资源网络防御决策方法_中文同步修订版.docx'
sys.path.append(str(R/'qa/math_deps'))
from latex2mathml.converter import convert
XSL=E.XSLT(E.parse(r'C:/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL'))
d=Document(SOURCE)
P={i+1:p for i,p in enumerate(d.paragraphs)}
changes=[]

def replace(p,old,new):
    """Edit only textual nodes, leaving all original math and formatting intact."""
    nodes=list(p._p.iter(qn('w:t')))
    text=''.join(n.text or '' for n in nodes)
    assert old in text, old
    start=text.index(old); end=start+len(old); pos=0; done=False
    for n in nodes:
        s=n.text or ''; lo=pos; hi=pos+len(s); pos=hi
        if hi<=start or lo>=end: continue
        left=max(0,start-lo); right=min(len(s),end-lo)
        n.text=s[:left]+(new if not done else '')+s[right:]
        done=True
    changes.append({'original':old,'revised':new})

def math(s):
    root=deepcopy(XSL(E.fromstring(convert(s).encode())).getroot())
    if E.QName(root).localname=='oMathPara': root=deepcopy(root.find(qn('m:oMath')))
    return root

def fill(p,s,template=None):
    sample=template or P[58]
    rpr=next((r._r.rPr for r in sample.runs if r.text and r._r.rPr is not None),None)
    rpr=deepcopy(rpr) if rpr is not None else None
    for c in list(p._p):
        if c.tag!=qn('w:pPr'): p._p.remove(c)
    for part in re.split(r'(\$[^$]+\$)',s):
        if not part: continue
        if part.startswith('$'): p._p.append(math(part[1:-1]))
        else:
            run=p.add_run(part)
            if rpr is not None: run._r.insert(0,deepcopy(rpr))

def after(anchor,s,template=None):
    node=OxmlElement('w:p'); anchor._p.addnext(node)
    p=Paragraph(node,anchor._parent)
    sample=template or anchor
    if sample._p.pPr is not None: node.append(deepcopy(sample._p.pPr))
    fill(p,s,sample)
    changes.append({'inserted':s})
    return p

# The abstract and conclusion carry the same comparison conditions as the English revision.
replace(P[2],'以资产受损比例描述网络状态，来刻画防御者面对该问题时如何动态部署防御资源。',
        '以资产受损比例描述网络状态演化，以隔离与恢复控制刻画防御者随时间部署资源的行动。')
replace(P[2],'设计动态防御行动求解算法（ABR-DAD）',
        '设计基于交替最佳响应的动态防御行动求解算法（Alternating Best Response for Dynamic Defense Action Decision，ABR-DAD）')
replace(P[2],'动态防御的累计加权受损损失和累计综合防御损失均低于对照方案，验证了该方法在有限资源条件下求解动态防御行动的有效性。',
        '在主容量及与动态防御联合求得的共同攻击计划下，动态防御的累计加权受损损失和累计综合防御损失均低于对照方案，支持该方法用于有限资源条件下的防御行动求解。')
replace(P[17],'恢复投入效率','恢复效果系数')
replace(P[54],'并用序列最小二乘规划（SLSQP）求解具有控制边界与线性容量约束的单方优化问题',
        '并用序列最小二乘规划（SLSQP）计算控制边界与线性容量约束下的单方局部数值响应')
replace(P[54],'随后交替更新双方控制计划',
        '这些局部数值响应近似求解式（13）—（14）所定义的理论最佳响应问题。随后交替更新双方控制计划')

# Keep the original numbered equations (15) and (16) in place.
fill(P[58],r'算法设置最大交替更新次数$M=40$，单次SLSQP优化最多迭代300次，停止容差为$10^{-10}$。分别从均匀可行、零控制和随机可行计划启动完整交替求解，每轮单方优化均以当前控制为唯一起点。以归一化已发现单方改善量$\eta_p$、投影梯度残差$stat_p$和响应距离$dist_p$作为停止指标，其中$\eta_p=gap_p/(1+|J_p|)$，$p\in\{D,A\}$。当双方SLSQP均正常退出，且三项指标在双方中的最大值分别不超过$10^{-7}$、$10^{-4}$和$10^{-3}$时，判定满足数值停止条件。')
diag=r'为定义停止诊断指标，在固定对手控制计划的条件下，记$F_D=J_D$、$F_A=-J_A$。设$\widetilde z_p$为数值求得的单方响应，且$\mathcal C_D=U_K$、$\mathcal C_A=A_K$。已发现单方改善量定义为$gap_p=\max\{0,F_p(z_p)-F_p(\widetilde z_p)\}$。采用单位步长的投影梯度残差$stat_p=\|z_p-\Pi_{\mathcal C_p}(z_p-\nabla F_p(z_p))\|_\infty$和响应距离$dist_p=\|\widetilde z_p-z_p\|_\infty$，其中$\Pi$表示向同时满足控制边界和容量约束的可行集作欧氏投影。仅当候选响应的控制边界违反量和容量违反量均不超过$10^{-10}$时，才接受该候选响应。用于停止判断的单起点检验与迭代终止后开展的三起点搜索是两项独立检验。'
dp=after(P[58],diag,P[58])
after(dp,r'求解完成后，防御者获得逐资产、逐控制区间的隔离与恢复行动计划。对资产$i$、区间$k$，算法给出的防御行动与资源占用为：',P[58])

replace(P[68],'为API网关','为应用程序编程接口（API）网关')
replace(P[68],'仿真采用预设的有向传播参数，模型强度和成本均为归一化量。',
        '本实验采用包含六类资产的合成网络，传播参数为预设值，时间、控制强度和成本均采用归一化量。表1汇总主要仿真参数。')
replace(P[72],'在同一攻击控制轨迹中比较动态防御（G）、固定均值防御（M）和无防御（N）。',
        '比较动态防御（G）、固定均值防御（M）和无防御（N）。三方案采用与G联合求得、随后固定用于全部对照方案的同一攻击控制轨迹。')
env='存档优化计算在Windows系统上完成，使用Python 3.11.7、NumPy 1.26.4和SciPy 1.11.4。防御容量为0.6、1.2和1.8时，基础随机种子分别为20262114、20261114和20263114；完整交替求解中的随机初始化使用对应基础种子加2。本文选取均匀初始化所得的计划作为报告结果。保存的控制计划、状态轨迹、诊断记录及绘图输入随论文源码一并提供。'
validation=r'三种容量下的均匀初始化路径均在第5次交替更新后首次满足停止条件。在三种容量和攻防双方中，归一化已发现单方改善量、当前计划的投影梯度残差和响应距离分别不超过$2.90\times10^{-10}$、$6.48\times10^{-5}$和$3.35\times10^{-5}$；最终单起点SLSQP检验的退出码均为0。不同完整求解初始化所得控制计划之间的最大差异小于$4.02\times10^{-5}$。对最终报告计划另行开展的三起点复核也满足上述局部检验标准。对于主容量下的三个对照计划，将每个控制区间的RK4子步数由48增加至192后，共同时刻的状态差异最大为$8.71\times10^{-12}$。这些结果属于给定策略类中的数值诊断。'
ep=after(P[72],env,P[72]); after(ep,validation,P[72])
replace(P[74],'检验防御配置的时空可计算性和容量可行性',
        '检验算法能否生成跨资产、跨时段且满足容量约束的防御计划')
replace(P[74],'权衡这一结果体现了','权衡。这一结果体现了')
replace(P[74],'容量激活和投入收缩','容量约束激活和规划末期投入下降')
replace(d.tables[2].cell(7,0).paragraphs[0],'合计（全网平均）','合计（时间平均）')
node=OxmlElement('w:p'); d.tables[2]._tbl.addnext(node)
note=Paragraph(node,d._body)
if P[78]._p.pPr is not None: node.append(deepcopy(P[78]._p.pPr))
fill(note,'注：合计值按未舍入数据计算。',P[78])
note.paragraph_format.first_line_indent=Pt(0)
note.paragraph_format.space_after=Pt(3)
for run in note.runs: run.font.size=Pt(9)
fill(P[87],r'图4展示同一攻击时序下API网关、身份认证、核心数据库及全网价值加权受损比例的变化，表3汇总三项评价指标。第6区间起点（$t\approx8.33$），网关入口攻击强度由0.384142降至0.139831，Web入口由0.365943降至0.137174；三方案下网关的新增受损流量$(1-x_1)\lambda_1$均小于恢复流量$(\delta_1+\gamma_1r_1)x_1$，受损比例由升转降。身份认证与核心数据库仍受上游传播影响，受损比例继续上升，体现传播滞后。',P[72])
replace(P[94],'在相同攻击时序下，动态方案',
        '在主防御容量下，采用与G联合求得的共同攻击计划时，动态方案')

# Synchronize only the bibliographic additions already verified for the English edition.
for idx,old,new in [
 (96,'PRECIADO V M, ZARGHAM M, ENYIOHA C, et al.','PRECIADO V M, ZARGHAM M, ENYIOHA C, JADBABAIE A, PAPPAS G J.'),
 (102,'LOU K, ZHAO G, WANG J, et al.','LOU K, ZHAO G, WANG J, HUANG X, WAN Z.'),
 (104,'MI Y, ZHANG H, HU H, et al.','MI Y, ZHANG H, HU H, TAN J, WANG J.'),
 (105,'TIAN L, GAN C, LIN J, et al.','TIAN L, GAN C, LIN J, SHANG F, ZHU Q.'),
 (111,'QIN Y, YANG X, YANG L X, et al.','QIN Y, YANG X, YANG L X, HUANG K.')]:
    replace(P[idx],old,new)
P[116].add_run(' 来源：https://degenerateconic.com/slsqp.html。')

d.save(OUT)
# Source diagrams, all original numbered equations and numerical table values stay unchanged.
with zipfile.ZipFile(SOURCE) as a, zipfile.ZipFile(OUT) as b:
    media=[n for n in a.namelist() if n.startswith('word/media/')]
    assert all(a.read(n)==b.read(n) for n in media)
for i in [14,16,30,31,33,34,36,37,40,41,45,46,52,53,59,60,63,64]:
    assert E.tostring(P[i]._p)==E.tostring(Document(SOURCE).paragraphs[i-1]._p),i
for ti in [1,2,3]:
    original=Document(SOURCE).tables[ti]
    for ri,row in enumerate(original.rows):
        for ci,cell in enumerate(row.cells):
            if ti==2 and ri==7 and ci==0: continue
            assert cell._tc.xml==d.tables[ti].cell(ri,ci)._tc.xml,(ti,ri,ci)
report={'source':str(SOURCE),'output':str(OUT),'translated_insertions':[diag,env,validation],
        'changes':changes,'checks':{'original_figures_unchanged':True,'18_numbered_equations_unchanged':True,'numerical_tables_unchanged':True}}
(R/'qa/chinese_revision_record.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT)
print('Verified: original diagrams, 18 numbered equations, and numerical table values preserved.')
