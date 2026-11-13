"""Build D3 writing artifacts from frozen D1/D2 text; never run research solvers."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'paper/work_d3'
ANALYSIS = OUT / 'analysis'
ANALYSIS.mkdir(parents=True, exist_ok=True)

def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')

def write(path, text):
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text.strip() + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

sources = [
    'paper/work_d1/03_introduction_zh.md',
    'paper/work_d1/04_system_model_zh.md',
    'paper/work_d1/05_game_solution_zh.md',
    'paper/work_d2/02_experimental_design_zh.md',
    'paper/work_d2/03_results_discussion_zh.md',
]
src = [read(p) for p in sources]
manifest_path = ANALYSIS / 'input_manifest.json'
if not manifest_path.exists():
    version = json.loads(read('paper/work_d2/analysis/minimal_revision_version_manifest.json'))
    protected = dict(version['files'])
    # Record current bytes independently; historical logs are intentionally appendable.
    current = {p: sha(ROOT / p) for p in protected if (ROOT / p).is_file()}
    for p in sources + ['02_MODEL_SPEC.md', 'src/core.py', 'src/game_solver.py',
                         'paper/work_d1/D1_R1_reproduction_notes.md',
                         'literature/fulltext_audit/R1_extracted.txt',
                         'literature/fulltext_audit/R3_extracted.txt',
                         'literature/fulltext_audit/R4_extracted.txt']:
        current[p] = sha(ROOT / p)
    for base in ['paper/work_d2/tables', 'paper/work_d2/figures']:
        for p in (ROOT / base).rglob('*'):
            if p.is_file():
                current[p.relative_to(ROOT).as_posix()] = sha(p)
    manifest_path.write_text(json.dumps({'date': '2026-11-11', 'timezone': 'Asia/Shanghai',
        'scope': 'D3 writing input bytes; no new research computation',
        'files': current}, ensure_ascii=False, indent=2), encoding='utf-8')

quote = '可以由你正式批准 G-D2，随后启动 Work D3，下一阶段应集中完成 摘要、结论、全文合稿、篇幅压缩、引用统一和投稿格式审查'
approval = f'''
## G-D2 现行最小修订稿与 Work D3 启动
- 状态：APPROVED（2026-11-11，Asia/Shanghai）。
- 用户明确授权原文：“{quote}”
- 批准依据：本会话用户明确授权批准 G-D2 并启动 D3；由 Work 执行登记。不是 Work 独立生成的人工签字，也不伪造第三方审查结论。
- 材料：paper/work_d2/D2_handoff.md、06_D2_review.md、D1_D2_equation_alignment.md，及 analysis/minimal_revision_version_manifest.json 对应现行最小修订版本。
- 范围：接受D2实验设计、结果解释、图表和既有证据边界，开放D3摘要、结论、全文整合、压缩、引用统一和投稿格式审查。具体登记见 reviews/G_D2_decision.md。
- 不扩大模型或实验范围；不将本批复作为连续全局Nash认证或最终投稿授权。目标会议、模板、篇幅与最终投稿文件另行确定。
'''
for name, text in [
    ('reviews/APPROVAL_LOG.md', approval),
    ('DECISIONS.md', f'''\n- **2026-11-11 / G-D2 APPROVED / Work D3启动**：用户明确授权原文“{quote}”。依现行D2最小修订材料及式号对齐PASS登记通过，进入摘要、结论、全文合稿、篇幅压缩、引用统一和投稿格式审查。授权来源为本会话用户，Work仅执行登记；不伪造人工签字或独立审查。保留两项贡献、合成数据、局部候选、负结果和有限精化范围，不修改冻结方程或重跑研究。具体会议与模板未指定，最终页数/套版验收未开放为已通过事实。见reviews/G_D2_decision.md。\n'''),
    ('logs/STATUS.md', '''\n## 2026-11-11 / G-D2 APPROVED / Work D3执行中
- 用户明确授权批准G-D2并启动D3，原文与边界见reviews/APPROVAL_LOG.md、reviews/G_D2_decision.md。
- 现行D2最小修订为本次接受版本；既有D1/D2等待文字保留为历史记录，由本条及正式批准记录更新状态。
- D3范围：摘要、结论、合稿、压缩、引用统一、通用投稿审查。冻结模型、源码、原始实验及D1/D2源稿保持原样。
- 具体目标会议与模板未指定；可继续通用稿及引用核对，会议页数、匿名要求和最终PDF版式待确定。
''')]:
    p = ROOT / name
    if 'G-D2 APPROVED' not in p.read_text(encoding='utf-8-sig') and '## G-D2 现行最小修订稿' not in p.read_text(encoding='utf-8-sig'):
        with p.open('a', encoding='utf-8') as handle:
            handle.write(text)

decision = f'''# G-D2 批复登记

日期：2026-11-11（Asia/Shanghai）。状态：**APPROVED**。

## 授权来源

用户本会话明确指示：

> {quote}

本记录将该消息作为用户授权批准G-D2并启动D3的依据，Work完成登记与执行。不将系统审阅伪装为人类专家意见，不补签G-D1，也不虚构用户逐页审阅的事实。

## 接受版本与审阅依据

- 接受paper/work_d2现行最小修订稿，以analysis/minimal_revision_version_manifest.json为版本接口；D3起始实际来源哈希另存paper/work_d3/analysis/input_manifest.json。
- D3对历史包与当前D1另作版本核对：5个文件有换行或Markdown表格空格/分隔线差异，规范化后正文一致；不是研究内容变更。原始比较见paper/work_d3/analysis/version_comparison.json，历史清单不覆盖。
- D2_handoff.md及06_D2_review.md记录无未解决BLOCKER、MINOR已处置；D1_D2_equation_alignment.md记录式(1)–(20)对齐PASS。本轮核对这些交付及版本，不虚称重新执行857项分析或独立审稿。
- 接受价值位置×传播条件交互、控制异质性、双评价规则强基线、反例与局部数值边界。贡献仍为主要匹配分析与支撑性协议内配对比较；模型及求解算法不是独立创新。

## 开放的下游范围

启动Work D3：完成摘要、结论、全文合稿、篇幅压缩、引用统一和投稿格式审查。D3不得自行扩大实验、改变冻结数学假设或抹去失败/负结果。目标会议未指定时可完成通用稿与审查，不宣称特定模板、页数或最终PDF已经通过。实际投稿不在本次执行范围。
'''
(ROOT / 'reviews/G_D2_decision.md').write_text(decision, encoding='utf-8')

equations = {}
for text in src:
    for block in re.findall(r'\\\[.*?\\\]', text, re.S):
        tag = re.search(r'\\tag\{(\d+)\}', block)
        if tag:
            equations[int(tag.group(1))] = block
assert sorted(equations) == list(range(1, 21))

def fill(text):
    for n, block in equations.items():
        text = text.replace(f'@@{n}@@', block)
    return text.strip()

def subsection(text, number):
    match = re.search(rf'^## {re.escape(number)} .*?(?=^## |\Z)', text, re.M | re.S)
    if not match:
        raise ValueError(number)
    return match.group(0).strip()

def relink(text):
    text = text.replace('](figures/', '](../work_d2/figures/')
    text = text.replace('](tables/', '](../work_d2/tables/')
    text = text.replace('](S1_source_data_index.md)', '](../work_d2/S1_source_data_index.md)')
    return text

title = '攻防交互下异质传播网络的隔离与恢复配置：匹配对照与收益边界'
en_title = 'Isolation and Recovery Allocation in Heterogeneous Propagation Networks under Attack–Defense Interaction: Matched Comparisons and Limits of Benefit'
abstract = '''资产的直接价值与出向传播能力并不总是一致，其相对位置如何影响隔离与恢复配置，需要在匹配条件下检验。本文采用隔离与恢复共享逐时容量的非零和开环攻防模型，构造上游暴露匹配的六节点合成网络，交叉改变高价值位置与出向传播条件。在三个种子、三个容量的36个分段开环局部候选中，九组价值—传播损失交互均为正，为0.018274—0.029192，相当于同组C格损失的0.170%—0.261%。控制记录显示，低容量下两个价值交换节点的隔离近零，中容量存在时窗与种子异质性，高容量大多松弛，因而正向目标交互不对应普遍动作切换。九个D格配置中，联合动态计划相对固定攻击训练计划的损失改善在响应攻击评价下仅为0.029%—0.286%，在公共固定攻击下均为负；原网络另有联合计划不占优反例。两组控制槽精化保持目标交互方向，但六槽嵌入后仍可发现十二槽单边改善。结果表明，该构造族中的价值位置效应依赖传播条件，联合防御收益同时受训练与攻击评价规则限制；证据不构成连续控制全局Nash或真实云环境有效性证明。'''
en_abstract = '''The direct value of an asset need not align with its capacity to propagate damage. We examine how this mismatch affects isolation and recovery allocation using a non-zero-sum open-loop attack–defense model with shared instantaneous defense capacity. A six-node synthetic network matches upstream exposure while crossing high-value location with outgoing propagation conditions. Across 36 piecewise-constant local candidates covering three seeds and three capacity levels, all nine loss interactions are positive, ranging from 0.018274 to 0.029192, or 0.170%–0.261% of the corresponding cell-C loss. Control records show negligible isolation at the two value-swapped nodes under low capacity, heterogeneous temporal responses under medium capacity, and mostly slack capacity at the highest level. Thus, positive loss interactions do not imply a universal switch between actions. Across nine cell-D configurations, the joint dynamic plan improves loss over fixed-attack-trained plans by only 0.029%–0.286% under local attack-response evaluation and performs worse under the common fixed attack. A separate original-network case also shows joint defense failing to outperform recovery alone. Refinement from six to twelve control intervals preserves the interaction direction in two selected four-cell groups, while unilateral improvements remain detectable against embedded six-interval plans. These findings establish a conditional value-location effect within the tested construction and identify evaluation-dependent limits on joint-defense benefits. They do not certify a global continuous-control Nash equilibrium or effectiveness in operational clouds.'''
keywords = '开环微分博弈；传播网络；隔离与恢复；匹配对照；资源配置'

intro = src[0].split('## 参考文献')[0].strip()
intro = intro.replace('两者说明，联合防御和资源竞争本身不能作为本文的原创性依据。', '上述工作构成联合防御与资源竞争的研究基础。')
intro = intro.replace('因此，动态博弈、价值异质性及条件性配置均不是尚未涉及的领域空白。', '这些结果为检验价值位置与传播条件的具体交互提供了基础。')
intro = intro.replace('这些研究基础仍需落实到可区分的配置问题。', '')
intro = intro.replace('Hamiltonian分析用于解释资源边际作用，多初值、单边偏离及积分精化用于检查数值质量；这些检查不构成连续控制全局Nash证明。', 'Hamiltonian分析解释资源边际作用，多初值、单边偏离及积分精化检查数值质量。')
intro = intro.replace('这三层差异不可相加为总收益，也不构成可独立归因的因果效应。动作语义明确的模型为上述分析提供统一研究设置，不作为独立方法创新。研究结论限于具体模型与已检验配置，不主张新的均衡算法或普遍配置规律。', '比较限于各自协议，三层差异不可相加或独立作因果归因。模型与局部求解为研究设置，主要增量是匹配交互分析及其收益边界。')

model = fill(r'''# 2 攻防微分博弈模型

## 2.1 参与者、状态与行动

考虑防御者\(D\)和攻击者\(A\)构成的两人有限时域非零和博弈，\(0<T<\infty\)。双方已知网络、参数、初态、目标和容量约束，在\(t=0\)同时选择\([0,T]\)上的完整时间计划，执行期间不按新状态修正行动；一方选择前不能观察另一方已选计划。离线交替求解不改变这一开环信息结构。

有向网络\(G=(V,E_G)\)中，\(V=\{0,\ldots,n-1\}\)表示逻辑资产实例组，\(\beta_{ji}\geq0\)为来源\(j\)到接收\(i\)的有效传播率，无边及自环时为零。状态\(x_i(t)\in[0,1]\)表示实例组受损比例，不是单台服务器的被攻击概率。防御直接损失权重为\(q_i\)，出向强度\(w_i^{\mathrm{out}}=\sum_{k\ne i}\beta_{ik}\)仅概括局部出边，不能替代动态影响。

攻击投入\(a_i\)仅作用于预定义入口\(\mathcal E\)：入口效率\(\alpha_i>0\)，非入口\(\alpha_i=a_i=0\)。防御行动为来源节点隔离\(s_i\)和本地恢复\(r_i\)，均与\(a_i\)一样取值于\([0,1]\)。节点是配置对象，不是独立参与者。

## 2.2 可行策略与状态演化

令\(u=(s,r)\)。双方几乎处处满足逐时容量约束

@@1@@

\(b_i^s,b_i^r,d_i^a>0\)为容量占用系数，\(B,A\geq0\)为同时可用的容量上限；它们不是累计消耗预算，也不同于经济成本。令\(U,\mathsf A\)分别为满足式(1)、箱约束及非入口零攻击的瞬时可行集合，开环策略集合为

@@2@@

给定\(x(0)=x_0\in[0,1]^n\)，状态演化为

@@3@@

其中隔离效率\(0<\varepsilon_i\leq1\)，基础恢复率\(\delta_i\geq0\)，投入恢复效率\(\gamma_i\geq0\)。隔离作用于来源节点的全部出边，不直接削减其入口攻击；恢复减少本地受损，并通过后续状态改变外传。记\(z_i=\alpha_i a_i+\sum_{j\ne i}\beta_{ji}(1-\varepsilon_js_j)x_j\)、\(d_i=\delta_i+\gamma_ir_i\)，则\(f_i=(1-x_i)z_i-d_ix_i\)，\(d_i\)与\(d_i^a\)含义不同。

参数有限、控制有界可测时，\(f\)对时间可测、对状态局部Lipschitz，给定控制对存在局部唯一绝对连续解。立方体各面上，\(x_i=0\)时\(f_i=z_i\geq0\)，\(x_i=1\)时\(f_i=-d_i\leq0\)，故\([0,1]^n\)正不变，解可延拓至整个有限时域；数值积分另行检查越界与精度。

## 2.3 双方目标与研究问题

防御者最小化累计受损损失、隔离业务中断及行动成本：

@@4@@

攻击者最大化受损收益扣除攻击成本后的净收益：

@@5@@

其中\(q_i,g_i,h_i,\omega_i,\nu_i\geq0\)，\(c_i^s,c_i^r,c_i^a>0\)。恢复不另设线性业务中断项；\(q_i\)与\(g_i\)可不同，双方成本分别计入目标，通常形成非零和结构。正式基准取\(\omega_i=\nu_i=0,g_i=1\)，交换\(q_i\)不改变攻击者的直接状态收益权重。

模型由参与者、时域、状态、初态、策略集合、动力学和目标共同定义。本文检验价值位置效应是否随出向传播条件改变，并比较指定训练与攻击评价规则下的防御损失。参数均为合成或归一化设定，不含检测、信念更新或学习机制；实际云环境的传播率与行动副作用须另行校准。
''')

solution = fill(r'''# 3 博弈分析与数值求解

## 3.1 理论基准与必要条件

理论上的开环Nash控制对满足

@@6@@

本文不预设其存在或唯一；计算对象为有限槽策略类中经局部响应诊断的开环候选。将式(4)、(5)的被积函数记为\(L_D,L_A\)，定义

@@7@@

固定对手计划，在正常型最优控制满足Pontryagin极值原理（Pontryagin maximum principle，PMP）的条件下，状态—伴随关系与Hamiltonian极值为必要条件。向量场及目标可微，控制集固定、紧且凸；状态边界由动力学保持，不另作独立路径约束。状态Jacobian及伴随方程为

@@8@@

@@9@@

防御最小化\(H_D\)，攻击最大化\(H_A\)；实现中最小化\(-J_A\)等价，但相应连续伴随为\(-p^A\)。非负权重和\(F\)的非负非对角元给出\(p^D,p^A\geq0\)。伴随是沿给定轨迹的未来边际损失，不是反馈价值函数。

## 3.2 行动边际与容量竞争

对控制求导可得

@@10@@

由此定义瞬时边际削减量

@@11@@

隔离作用于下游增长，取决于来源受损、下游未受损比例及其未来损失；恢复直接影响本地受损，也改变之后的传播。二者都含动态系统信息，不能简化为“隔离只看传播、恢复只看价值”。

固定\((t,x,p^D,p^A)\)时，防御Hamiltonian对本方控制严格凸，攻击Hamiltonian严格凹；瞬时可行子问题各有唯一解。这不意味着整段动态目标全局凸/凹。令容量乘子\(\lambda_D,\lambda_A\geq0\)，由Karush–Kuhn–Tucker（KKT）条件得到

@@12@@

@@13@@

这里\(\operatorname{clip}_{[0,1]}(v)=\min(1,\max(0,v))\)。容量松弛时乘子为零，绑定时乘子未必严格为正；非零投入的单位容量边际还须扣除二次成本并考虑箱约束。式(12)是给定状态—伴随条件下的关系，不给出普适时间优先级。

## 3.3 分段开环求解与诊断

将时域等分为\(K\)槽，每槽控制常值，得到\(\mathcal U_K\subset\mathcal U,\mathcal A_K\subset\mathcal A\)。式(1)逐槽实施，左侧不乘槽长。直接射击采用经典四阶Runge–Kutta（RK4）积分，每槽\(H\)子步、步长\(T/(KH)\)，同步传播离散映射灵敏度得到梯度，再以序列最小二乘规划（Sequential Least Squares Programming，SLSQP）求本方局部响应。该过程不求连续PMP边值问题，式(12)也不替代槽变量优化。

匹配实验从均分、零、随机三类可行初值开始，以均分路径为登记主路径。每轮固定同一候选分别检查双方局部偏离，再用顺序攻击响应生成下一轮候选；不采用阻尼。通过条件为双方归一化已发现改善不超过\(10^{-7}\)、当前候选投影残差不超过\(10^{-4}\)、响应控制最大变化不超过\(10^{-3}\)，且优化成功退出。未通过且到达轮数上限仍记失败。主路径经12起点及稀疏起点偏离审计，再以\(H=48\)重求并作三起点审计；全部路径保留。算法1与复现参数见补充S3。

相对于精确常微分方程（ordinary differential equation，ODE）目标，受限策略类的全局单边改善为

@@14@@

有限槽可行集紧且目标连续，单方极值可取到，局部搜索不保证找到它。令\(\widehat J\)为RK4目标，\(\widetilde u,\widetilde a\)为返回的可行响应，展示的已发现改善为

@@15@@

对最小化目标\(F\)（防御为\(\widehat J_D\)，攻击为\(-\widehat J_A\)）、本方槽向量\(v\)及可行多面体\(\mathcal C\)，投影残差定义为

@@16@@

其中\(\Pi_{\mathcal C}\)是欧氏投影。搜索保留当前计划，返回点须目标有限、约束违反不超过\(10^{-10}\)且不劣于当前候选；优化退出码另行检查。积分失败或状态越界显式报告，不裁剪隐藏。式(15)至多给出同一数值目标的已发现改善下界，小值不是未知全局偏离的上界；式(16)只是一阶诊断。候选上的积分精化也不提供全可行域误差界。控制槽数\(K\)改变策略空间，\(H\)改变固定策略的积分精度，必须分别核验。
''')

method_table = src[3].split('|方法|防御计划')[1].split('\n\n单动作')[0]
method_table = '|方法|防御计划' + method_table
design = fill(r'''# 4 实验设计

## 4.1 参数与匹配四格

实验采用六节点合成网络，\(T=10,K=6\)，每槽宽\(5/3\)；入口为0、1，\(x(0)=(0.1,0,0,0,0,0)\)。三个种子生成成对匹配的上游边权，不代表现实样本。表1列出主要参数，精确边权及完整参数见补充S1。成本系数进入目标，容量系数进入约束；相同容量上限不要求实际用量相同。

**表1 主要合成参数。** 各节点相同取值仅列一次。

|参数|取值|
|---|---|
|\(n,T,K\)；种子|6，10，6；11、22、33|
|入口\(\mathcal E\)、入口效率\(\alpha_i\)|\(\{0,1\}\)、0.25；非入口为0|
|\(\delta_i,\gamma_i,\varepsilon_i\)|0.10，0.30，1.00|
|\(q_i,g_i,h_i\)|高价值位置\(q_i=4\)，其余1；\(g_i=1,h_i=0.05\)|
|\(c_i^s,c_i^r,c_i^a,b_i^s,b_i^r,d_i^a\)|全部1|
|\(\omega_i,\nu_i\)；\(B,A\)|全部0；\(B=0.6,1.2,1.8\)，\(A=0.8\)|
|积分子步\(H\)|匹配粗/细求解12/48；强基线最终目标192|

网络含八条边（图1）：0、1各连2、3，2、3各连4、5。对每个入口，到2、3的边权相同，匹配初态与路径长度；此结构匹配不强制防御后的状态相同。equal条件下，2、3各条出边均为0.08，出向强度均为0.16；unequal条件下，2的各出边0.12、3的各出边0.04，出向强度分别为0.24、0.08。两条件下游总边权均为0.32，上游边及连接关系不变。

![图1 六节点匹配网络](../work_d2/figures/fig01_matched_network.png)

**图1 六节点匹配网络。** 左、右面板分别为equal、unequal；\(u=\beta_{02}=\beta_{03}\)、\(v=\beta_{12}=\beta_{13}\)是图内边标签，与防御计划\(u\)无关。蓝灰节点为价值交换位置，两者不同时高价值；边交叉处无节点。

在两传播条件中分别将高价值置于2或3，形成A（equal，高价值2）、B（equal，高价值3）、C（unequal，高价值2）、D（unequal，高价值3）。价值交换仅改变\(q_2,q_3\)，\(g\)及其他参数不变。A/B为镜像，C/D因强出边仍在2而不是镜像。3种子×3容量×4格共36配置，逐格允许双方重新形成局部候选。对同一种子与容量定义

@@17@@

\(J_D\)下标D为防御者，上标A—D为实验格。交互包含双方计划及状态共同调整，不是固定攻击下的纯防御效果或现实因果效应。强基线预先限定为9个D格，原网络反例另列；K精化和环境复现复用既有实例，不追加为独立样本。

## 4.2 防御方法与攻击评价

表2中的八方法共享模型、种子、容量上限与评价规则。Uniform、Value-only、Spread-only按1、\(q_i\)、出向强度加权，将一半容量用于隔离、一半用于恢复，六槽不变；本批箱约束截断未触发，用满容量。它们是内部规则基线，不是外部算法复现。优化方法允许容量松弛。

**表2 八种防御方法。** 优化均为局部求解。

@@METHOD_TABLE@@

每份防御计划分别接受公共固定攻击（common_fixed_attack）和响应攻击（adaptive_attack）评价。前者固定入口各0.4；后者固定防御，以三起点局部优化重新计算完整六槽攻击。两评价逐分量使用相同防御计划，额外防御响应检查只作诊断。响应攻击不是实时反馈，也不把原同时行动模型改为Stackelberg博弈。各规则内分别比较，不将两模式计作独立重复。

## 4.3 指标与数值核验

匹配交互使用H=48目标，八方法最终配对使用H=192目标；分解与轨迹另按来源精度报告。同配置、同评价\(e\)内，以基线\(m\)损失为分母定义

@@18@@

该数值以百分数报告，\(G=0.1\)即降低0.1%；正值为联合动态损失较低。1%是原协议描述门槛，不是显著性或现实经济收益阈值。三类强基线改变的策略限制及训练假设不同，可能伴随不同攻击响应与资源用量，不能把配对差异相加或独立归因。

时窗控制和容量按

@@19@@

统计，\(W\)固定为全时域、前段\([0,20/3)\)、末段\([20/3,10]\)。\(S,Q\)为控制积分，乘容量系数后才是容量时间积。控制交互沿用式(17)，绝对均值交互超过0.001为工程分辨率；\(|B-U_{D,k}|<10^{-6}\)标记绑定，全部节点均计入。种子与控制槽均不作独立随机样本，不实施总体显著性检验。

以\(E\)表示逐槽复制的六槽到十二槽嵌入，定义

@@20@@

两组精化比较\((K,H)=(6,48)\)与\((12,24)\)，保持物理步长一致，再以96与48子步核验。另固定嵌入后的对手搜索十二槽偏离，区别于十二槽重新求解后的残余改善。优化退出、式(15)/(16)、多初值、可行性及积分检查分别报告。
''').replace('@@METHOD_TABLE@@', method_table)

table3 = src[4].split('|攻击评价|基线|')[1].split('\n\n公共固定')[0]
table3 = '|攻击评价|基线|' + table3
results = r'''# 5 实验结果与讨论

## 5.1 价值位置效应依赖传播条件

九组种子—容量组合的损失交互均为正（图2）。equal下价值交换的目标差绝对值不超过\(7.32\times10^{-12}\)，交换节点后的全控制最大差为\(7.75\times10^{-11}\)；unequal下，价值移至弱出向节点均使损失增加，\(I_J\)为0.018274—0.029192。以同组C格损失归一化，量级为0.170%—0.261%；该比例描述交互尺度，不是式(18)的方法改善率。三个种子均在中容量取得较大交互，未随容量单调增大。全部36目标及九组差值见补充S1，不以精选示例替代。

![图2 四格损失与交互](../work_d2/figures/fig02_losses_interactions.png)

**图2 四格原始损失及交互。** a—c为三个容量下A/B/C/D的H=48防御目标，d—f为同种子、容量的\(I_J\)。零轴保留，A/B近乎重合；每点是确定性配置，连线只区分种子，不表示连续趋势。

C格高价值与强出边位于同一节点，D格将两者分离。C格损失较低，与恢复高价值节点同时减少较强外传的解释相容。然而交互还含攻击共同响应、业务中断和行动成本变化，不能视为已独立分离的传播收益，更不意味着所有时段控制同向。

## 5.2 配置变化与容量条件

图3固定展示种子11，补充图S1展示种子33的中容量异质性，两者不承担总体代表性。低容量12个候选中，节点2、3隔离最大仅\(7.65\times10^{-16}\)，资源主要用于入口0、1的治理及中间节点恢复。因此，低容量变化不能解释为两个中间节点持续隔离—恢复切换。前段节点2、3的恢复交互分别为−0.007356至−0.006017、−0.006030至−0.004761，均超过0.001分辨率；末段种子22节点2已转为+0.001425，而种子11为−0.000354。

![图3 时序配置与容量](../work_d2/figures/fig03_temporal_allocation.png)

**图3 种子11的C/D控制与容量。** 三列为B=0.6、1.2、1.8；上两行为节点2、3的隔离和恢复，下行为全部六节点的容量使用率。每槽宽5/3，颜色区分C/D、线型区分节点；隔离与恢复轴尺度不同，近零和重合曲线保留。

中容量全时域恢复交互在种子11、22为小幅正值且低于分辨率，种子33的节点2、3则为−0.001174、−0.003069。低、中、高容量分别仅有60/72、40/72、1/72槽绑定，高容量主要松弛。由此，正向目标交互可与控制异质性并存；容量松弛时仍有传播收益与成本取舍，不能将所有配置解释为紧容量竞争或普遍“先隔离后恢复”。式(11)提供定性组织，未直接重建伴随轨迹验证优先级定理。全部节点用量、状态与成本分解见补充S2。

## 5.3 强基线与评价依赖

9个D格在响应攻击评价下，联合动态相对仅恢复、静态联合、固定攻击训练的改善分别为0.887%—4.796%、0.661%—2.190%、0.029%—0.286%（表3）。最后一项九值均低于1%描述门槛；公共固定攻击下又全部反向。结果支持具体协议内的差异，不能据此宣称一般博弈方法优势。

**表3 协议内强基线配对改善。** 单位为%，按式(18)以该行基线损失为分母；使用H=192。范围和中位数是九项描述统计，正向项数表示联合动态损失较低的配置数。

@@TABLE3@@

Fixed-trained专门对公共固定攻击训练，其在该评价下领先与训练目标一致。响应攻击下，相对Uniform、Value-only、Spread-only、Isolation-only的差距分别为7.693%—11.480%、8.223%—17.542%、5.578%—14.053%、5.665%—11.000%，但规则方法用满容量，优化方法可松弛，差距还含资源用量与成本差异。较弱基线的大差距不能替代相对Fixed-trained的小收益。完整八方法目标和逐配置配对见补充S4。

## 5.4 反例与数值边界

原网络seed33/business_cost/B0.6在各自局部响应攻击下，联合损失12.437518228196426，仅恢复12.436854043461201，联合改善为−0.005340456%。该反例不是第十个D格。固定联合候选攻击时，联合与仅恢复分别为12.437518、12.439491；固定仅恢复候选攻击时，分别为12.434801、12.436854。共同攻击的两列中联合较低，而各自响应后的排名相反，说明攻击响应参与了排名；局部候选的交叉评价不能证明增添动作本质有害，也不能确定全局最佳响应结果。

36匹配配置通过登记局部门槛：最大归一化已发现单边改善\(1.54\times10^{-9}\)，当前候选投影残差\(9.97\times10^{-5}\)，三初值控制差\(8.88\times10^{-5}\)，容量违反\(8.10\times10^{-15}\)，保存计划积分精化目标差\(9.45\times10^{-9}\)。这些分别是局部搜索、一阶、初始化、可行性和积分诊断，不能合并为全局均衡证书。

**表4 控制槽精化及复现范围。** 不同行不累加为独立样本。

|范围|结果|解释边界|
|---|---|---|
|seed11/B0.6四格，K=6→12|交互0.0182736907→0.0182733189|该组目标方向保持|
|seed33/B1.2四格，K=6→12|交互0.0291919616→0.0291096181|该组目标方向保持|
|六槽复制至十二槽，8格|防御已发现归一化改善0.1223%—0.2141%；攻击0.1731%—0.1767%|六槽候选跨类偏离仍存在|
|重新求解十二槽，32路径|最大归一化已发现改善\(3.36\times10^{-9}\)，投影残差\(9.94\times10^{-5}\)|十二槽自身策略类的局部质量|
|seed11/B1.2，K=6四格隔离环境|目标差≤\(1.96\times10^{-12}\)，控制差≤\(1.13\times10^{-11}\)，状态差≤\(4.08\times10^{-12}\)|同Windows主机、Python3.11.7与算法的重求复现|

表4只覆盖两组精化，不能推广到全部36配置或连续控制收敛。防御控制最大分量差在低、中容量组分别为0.063305—0.064929、0.082446—0.084091，攻击也同时改变；部分末段交互跨越0.001分辨率。目标方向稳定不等于控制时序稳定，十二槽重新求解的小残差也不能抹去嵌入六槽候选的偏离。

实现修复后的53项历史测试与单配置回放提供防护证据，四张三节点两槽有限表的纯均衡仅对各自菜单有效。历史补充run01失败，run02为完成批次；隔离环境复现不称跨平台或独立数学实现。上述检查支撑所报告数值的有限可信性，不证明连续开环Nash的存在、唯一或全局可求性。补充S3、S4保留诊断、失败记录与重现入口。
'''.replace('@@TABLE3@@', table3)

conclusion = r'''# 6 结论

本文在上游暴露匹配的合成传播网络中，通过价值位置与出向传播条件的四格比较，识别了所测构造族中方向一致的损失交互。高价值从强出向节点移至弱出向节点时，损失增加；这一位置效应在出向条件相等时不可分辨。其配置基础表现为恢复、入口治理与行动成本的共同调整，并随容量、种子和时窗改变，不能概括为普遍的隔离—恢复切换规则。

与强基线的配对比较进一步表明，联合动态计划的收益取决于训练和攻击评价规则。相对固定攻击训练，响应攻击评价中的改善仅为0.029%—0.286%，公共固定攻击下则九项均不占优，原网络还存在相对仅恢复的负反例。因此，本文的研究增量是可重算的价值—传播交互及其适用条件，而非联合防御普遍领先或新的均衡求解方法。

两组控制槽精化保持了目标交互方向，但配置时序有所变化，六槽候选在十二槽策略类中仍存在已发现偏离。研究限于六节点合成构图与局部开环搜索；后续应围绕真实传播参数及隔离副作用的校准，以及更广策略类中的偏离控制，检验这些条件性结论的外部适用范围。
'''

references = '''## 参考文献

[1] Preciado V M, Zargham M, Enyioha C, Jadbabaie A, Pappas G J. Optimal Resource Allocation for Network Protection Against Spreading Processes. IEEE Transactions on Control of Network Systems, 2014, 1(1): 99–108. DOI: [10.1109/TCNS.2014.2310911](https://doi.org/10.1109/TCNS.2014.2310911).

[2] Paarporn K, Xu S. Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests. IEEE Control Systems Letters, 2024, 8: 2421–2426. DOI: [10.1109/LCSYS.2024.3486629](https://doi.org/10.1109/LCSYS.2024.3486629).

[3] Tian L, Gan C, Lin J, Shang F, Zhu Q. Analysis of attack-defense game for advanced malware propagation control in cloud. Computer Communications, 2025, 237: 108148. DOI: [10.1016/j.comcom.2025.108148](https://doi.org/10.1016/j.comcom.2025.108148).

[4] Botteghi E, Centonze M S, Pastorello D, Tantari D. Contagion Effects of Heterogeneous Cyber Risk on Network Security and Systemic Stability. arXiv:2601.16805v2, 2026-10-05. [版本全文](https://arxiv.org/html/2601.16805v2).

[5] Chen W, Wang J, Xia Y, Wang Z. To protect, or to recover? The effect of defense resource allocation on network robustness. Chaos, 2025, 35(12): 123136. DOI: [10.1063/5.0267934](https://doi.org/10.1063/5.0267934).
'''

sections = [intro, model, solution, design, results, conclusion]
write('manuscript_zh.md', '# ' + title + '\n\n## 摘要\n\n' + abstract + '\n\n**关键词：** ' + keywords + '\n\n' + '\n\n'.join(sections) + '\n\n' + references)
write('01_abstracts.md', f'# {title}\n\n## 中文摘要\n\n{abstract}\n\n**关键词：** {keywords}\n\n## English title\n\n{en_title}\n\n## Abstract\n\n{en_abstract}\n\n**Keywords:** open-loop differential game; propagation network; isolation and recovery; matched comparisons; resource allocation')
write('02_conclusion_zh.md', conclusion)
baseline = '\n\n'.join([src[0].split('## 参考文献')[0].strip()] + src[1:])
write('analysis/assembled_before.md', baseline)

param_table = src[3].split('|参数|取值|')[1].split('\n\n匹配实验')[0]
param_table = '|参数|取值|' + param_table
value_table = src[4].split('|种子|B|')[1].split('\n\nA/B防御')[0]
value_table = '|种子|B|' + value_table
algorithm = re.search(r'```text.*?```', src[2], re.S).group(0)
s2 = subsection(src[4], '5.2').replace('## 5.2 时序配置与资源竞争', '## S2 全节点配置、状态及成本分解')
s4 = subsection(src[4], '5.5').replace('## 5.5 数值可靠性与稳健性', '## S4 完整数值诊断与强基线源表')
s4 = s4.replace('（表4）', '（补充表S2）').replace('**表4 反例与数值边界摘要。**', '**补充表S2 反例与数值边界摘要。**')
notes = read('paper/work_d1/D1_R1_reproduction_notes.md').split('\n\n', 2)[2]
supp = f'''# 补充材料：{title}

本文件保留压缩主文之外的参数、全量原值与技术细节。它与主文共同构成D3中文审阅稿，不是新增实验。路径均可从本项目访问；投稿时应按会议附件政策打包，不将本地链接直接当作公开数据地址。

## S1 参数与全部四格原值

以下参数表及原值表继承D2；来源S/M/P含义分别为冻结规格、保存匹配模型/配置、实验协议。传播与经济参数均为合成或归一化量。

{param_table}

以下四格目标使用H=48。上标A—D是实验格，不与防御者下标D混淆。交互依主文式(17)；以C格损失为分母的0.170%—0.261%仅表示相对量级。

{value_table}

完整精度：[四格原值](../work_d2/tables/matched_four_cells.csv)；原始文件定位：[D2源数据索引](../work_d2/S1_source_data_index.md)。

{s2}

![补充图S1 中容量异质性及状态](../work_d2/figures/figS01_seed33_state_allocation.png)

**补充图S1 种子33、B=1.2的配置与状态。** 沿用D2图形及其源数据映射，呈现与种子11不同的中容量行为，不承担总体代表性；纵轴覆盖完整状态数据。

## S3 算法、实现与重现

{algorithm}

{notes}

以下为既有结果的核验与研究重现入口，D3没有执行求解或实验；研究命令须指定新的空输出目录，不覆盖历史结果：

```powershell
python paper/work_d2/analysis/build_analysis.py
python paper/work_d2/analysis/final_verify.py
python -m src.matched_mechanism --output <新的空目录>
python -m src.supplement_c2 --output <新的空目录>
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine <新运行名>
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine_analysis <同一运行名>
```

前两条消费保存数据；后四条会运行研究计算。具体环境、种子与完整命令以[Work C2交接](../../handoffs/C2_robustness.md)及各运行metadata为准。D3自身文本检查入口为`python paper/work_d3/analysis/verify_d3.py`。

{s4}

强基线原始目标：[八方法全部目标](../work_d2/tables/baseline_all_objectives.csv)；[逐配置配对](../work_d2/tables/baseline_pairs.csv)；[完整D2结果与交叉攻击反例](../work_d2/03_results_discussion_zh.md)。不得将144评价、160含反例评价、140配对或32路径相加作为独立样本数。

## S5 来源与图形接口

- [逐主张证据映射](../work_d2/04_claim_evidence_matrix.md)与[D2源索引](../work_d2/S1_source_data_index.md)定位全部控制、状态、容量及结果JSON。
- [D1–D2式号对齐](../work_d2/D1_D2_equation_alignment.md)为D3继承的式(1)–(20)版本接口；D3逐式正文保留原公式字节。
- 三张主图与图S1的PDF/SVG/PNG位于[图表清单](../work_d2/05_figure_table_manifest.md)所列目录，D3不重绘、不缩放、不替换。最终套版后须重新检查字号与可读性。
'''
write('supplement_zh.md', relink(supp))

# Build the five-entry bibliography from the same reference identities as the text.
write('references.bib', r'''% D3 canonical bibliography: numeric order [1]--[5] is recorded in citation_audit.md.
@article{Preciado2014Protection,
  author={Victor M. Preciado and Michael Zargham and Chinwendu Enyioha and Ali Jadbabaie and George J. Pappas},
  title={{Optimal Resource Allocation for Network Protection Against Spreading Processes}},
  journal={IEEE Transactions on Control of Network Systems},
  year={2014}, volume={1}, number={1}, pages={99--108},
  doi={10.1109/TCNS.2014.2310911}, url={https://arxiv.org/pdf/1309.6270}
}
@article{PaarpornXu2024,
  author={Keith Paarporn and Shouhuai Xu},
  title={{Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests}},
  journal={IEEE Control Systems Letters}, year={2024}, volume={8}, pages={2421--2426},
  doi={10.1109/LCSYS.2024.3486629}
}
@article{Tian2025,
  author={Liang Tian and Chenquan Gan and Jiabin Lin and Fengjun Shang and Qingyi Zhu},
  title={{Analysis of attack-defense game for advanced malware propagation control in cloud}},
  journal={Computer Communications}, year={2025}, volume={237}, pages={108148},
  doi={10.1016/j.comcom.2025.108148}
}
@misc{Botteghi2026v2,
  author={Elisa Botteghi and Martino S. Centonze and Davide Pastorello and Daniele Tantari},
  title={{Contagion Effects of Heterogeneous Cyber Risk on Network Security and Systemic Stability}},
  year={2026}, eprint={2601.16805}, version={2}, archivePrefix={arXiv},
  url={https://arxiv.org/html/2601.16805v2}, note={Version 2, revised 2026-10-05}
}
@article{Chen2025,
  author={Wei Chen and Jingrui Wang and Yongxiang Xia and Zhen Wang},
  title={{To protect, or to recover? The effect of defense resource allocation on network robustness}},
  journal={Chaos}, year={2025}, volume={35}, number={12}, pages={123136},
  doi={10.1063/5.0267934}
}''')

write('terminology.md', r'''# D3 统一术语

|规范形式|定义及处理|
|---|---|
|受损比例\(x_i\)|实例组的聚合受损状态，禁作单台服务器攻击概率|
|有效传播率\(\beta_{ji}\)|来源j至接收i，不是攻击成功概率|
|来源节点隔离\(s_i\)；本地恢复\(r_i\)|分别作用于出边传播、本地恢复率|
|逐时容量\(B,A\)|同时可用上限，不是累计预算|
|经局部响应诊断的开环候选|数值输出；理论开环Nash仅用作式(6)基准|
|公共固定攻击；响应攻击|分别对应common_fixed_attack、adaptive_attack；后者不表示状态反馈|
|Fixed-trained|固定攻击训练方法，与评价规则分开|
|四格交互\(I_J\)|式(17)，含双方共同响应|
|配对改善\(G\)|式(18)，乘100的数值，单位%；分母为基线损失|
|控制槽K；每槽积分子步H|分别改变策略空间、积分精度|
|PMP；KKT；RK4；SLSQP|在主文第3节首次展开；后续保留短名|
|A/B/C/D|仅表示匹配四格；原P3三场景另行命名|
''')

print(json.dumps({'built': 'D3 manuscript, abstracts, conclusion, supplement, bibliography',
                  'equation_groups': len(equations), 'source_files': sources}, ensure_ascii=False))
