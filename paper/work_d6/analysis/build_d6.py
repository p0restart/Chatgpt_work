from pathlib import Path
import re, csv, json, hashlib, shutil

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'paper/work_d6'
def read(p): return (ROOT / p).read_text(encoding='utf-8-sig')
def write(p,s):
    q=OUT/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(s,encoding='utf-8')
def rows(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def table(headers, values):
    return '|'+ '|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('|'+ '|'.join(map(str,r))+'|\n' for r in values)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

OUT.mkdir(parents=True,exist_ok=True)
inputs=[]
for folder in ['paper/work_d1','paper/work_d2','paper/work_d3','paper/work_d4','paper/work_d5','reports/work_d4','reports/work_d5','handoffs','reviews']:
    for p in (ROOT/folder).rglob('*.md'):
        if not any(x in p.parts for x in ['_qa_packages','history','source_snapshot','minimal_revision_before']): inputs.append(p)
inputs += [ROOT/p for p in ['AGENTS.md','DECISIONS.md','02_MODEL_SPEC.md','src/core.py','src/game_solver.py','src/matched_mechanism.py','paper/work_d3/references.bib','handoffs/C_bibliography.bib','handoffs/C_prior_art_matrix.csv']]
for folder in ['results/work_d5/replanning/run03','reports/work_d5/p0/run02','paper/work_d2/tables']:
    inputs += [p for p in (ROOT/folder).iterdir() if p.is_file() and p.suffix in ['.csv','.json','.md']]
inputs += [ROOT/'paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv']
manifest={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(set(inputs))}
write('analysis/input_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))

d3=read('paper/work_d3/manuscript_zh.md')
model=d3.split('# 2 攻防微分博弈模型')[1].split('# 3 博弈分析与数值求解')[0]
model=model.replace('本文检验价值位置效应是否随出向传播条件改变，并比较指定训练与攻击评价规则下的防御损失。','本文计算容量约束下逐节点、逐时槽的隔离与恢复计划，并比较不同攻击评价条件下的防御损失；价值位置与传播条件的匹配对照用于解释配置差异。')
model=model.replace('其中\\(q_i,g_i,h_i,\\omega_i,\\nu_i\\geq0\\)，','其中\\(q_i,g_i,h_i,\\omega_i,\\nu_i\\geq0\\)，分别表示防御直接损失权重、攻击状态收益权重、隔离业务中断系数及双方终端受损权重；')
model=model.replace('\\(c_i^s,c_i^r,c_i^a>0\\)。','\\(c_i^s,c_i^r,c_i^a>0\\)分别为隔离、恢复和攻击的二次成本系数。')
method=d3.split('# 3 博弈分析与数值求解')[1].split('# 4 实验设计')[0]
method=method.replace('将式(4)、(5)的被积函数记为\\(L_D,L_A\\)，定义','将式(4)、(5)的被积函数记为\\(L_D,L_A\\)，以\\(p^D,p^A\\)表示双方伴随向量，定义')
method=method.replace('状态Jacobian及伴随方程为','令\\(F_{i\\ell}=\\partial f_i/\\partial x_\\ell\\)为状态Jacobian元素，\\(\\ell\\)表示来源节点索引，则状态Jacobian及伴随方程为')
method=method.replace('由此定义瞬时边际削减量','其中\\(\\mathbf1_{\\{k=i\\}}\\)为指示函数，节点相同时取1，否则取0；第一式在\\(k=i\\)时因零自环等于零。由此定义瞬时边际削减量')
method=method.replace('将时域等分为\\(K\\)槽，每槽控制常值，','将时域等分为\\(K\\)槽，槽长\\(\\Delta=T/K\\)，第\\(k\\)槽为\\([k\\Delta,(k+1)\\Delta)\\)，其中\\(k=0,\\ldots,K-1\\)。各槽的\\(a_k,s_k,r_k\\)为常值向量，')
method=method.replace('算法1与复现参数见补充S3。','算法1在下节给出；各批次的复现参数见配套证据映射，历史流程的优化容差不混用。')

intro=r'''# 基于非零和微分博弈的有限资源网络防御决策方法

> 审阅版说明（2026-11-13）：本稿以D3为底稿，按本次D6授权整合写作。D4-P0-1、D5决策差异审计及滚动重规划run03作为**待批准证据**纳入；其出现不代表结果已获人工验收。原有审批状态保持不变。本稿供完整内容审阅，尚未按具体会议模板套版。

## 摘要

针对传播风险与防御行动成本共同作用下的有限资源配置问题，本文采用有限时域非零和微分博弈，描述攻击入口投入、来源节点隔离与本地恢复之间的动态关联，并以开环Nash作为理论比较基准。将控制离散为分段常值计划，通过四阶Runge–Kutta积分、离散灵敏度、序列最小二乘规划和交替局部响应，计算满足逐时共享容量的隔离与恢复配置；攻击条件变化后，以当前状态重新求解剩余时域问题并仅执行首槽。在六节点合成网络的既有九组方法比较中，联合动态计划相对固定攻击训练计划在各自攻击响应评价下改善0.029%—0.286%，在公共固定攻击下均不占优。待批准的决策差异证据显示双方响应随对方计划改变；待批准的18条重规划轨迹中，博弈重规划相对沿用原计划均降低总损失，但相对非博弈滚动优化在两种公共执行攻击下分别略逊和略优，且计算开销更高。匹配对照进一步表明，价值—传播交互不能全部归因于战略响应。结果支持在指定模型与评价协议下形成可检查的资源决策流程，其收益受攻击假设、容量和策略类限制；数值候选不构成连续控制全局或反馈Nash均衡证明。

**关键词：** 非零和微分博弈；开环策略；有限资源；隔离与恢复；滚动重规划

# 1 引言

网络防御需要回答具体的资源决策问题：在每个时段，应在哪些资产上实施隔离和恢复，各投入多少资源，以及何时重新计算计划。隔离能够抑制来源资产向外传播，却会带来业务中断；恢复能够减少本地受损，也会通过后续状态降低传播。两类行动共享有限容量时，单独按资产价值或网络出向强度排序，难以同时反映未来受损、业务成本和资源竞争。云工作负载之间的访问关系提供了这一问题的应用动机，本文采用合成有效传播网络开展模型分析，而非生产云实测。

联合配置传播抑制与恢复资源已有充分研究基础。Preciado等[1]在有向异质网络中联合调整感染率与恢复率，通过几何规划求解预算约束下的传播控制问题。Paarporn和Xu[2]研究攻击竞争下预防与恢复共享资源的取舍，给出特定零和资源竞赛的均衡刻画。前者采用静态率参数优化，后者以独立节点的攻破概率及恢复时长描述损失，为本文的资源约束与双动作比较提供参照。

传播微分博弈进一步将行动与状态演化联系起来。Tian等[3]已针对云恶意软件传播建立非零和开环攻防模型，并利用状态和伴随方程求取控制计划。价值异质性与网络位置的共同作用也已有先例：Botteghi等[4]在Stackelberg安全博弈中分析双方估值与传播风险对保护配置的影响。Chen等[5]从负载级联角度考察保护—恢复比例，表明资源条件会改变两类行动的取舍。因此，非零和建模、联合防御和动态配置本身均不足以构成本文的独立创新声明。

本文关注有限资源条件下从模型到实际时间计划的计算链，以及战略响应对配置和收益的具体影响。攻击者选择入口投入，防御者选择来源节点的出边隔离和本地恢复，双方通过同一受损状态轨迹形成非零和关联。攻击者的目标不是直接最大化防御总损失，因而“攻击响应更适合自身目标”与“防御损失一定增加”不能等同。判断战略建模的作用，需要同时比较防御动作、攻击响应和统一协议下的目标，不能只凭存在博弈方程或必要条件作出判断。

本文的工作包括两方面。第一，围绕既定传播模型组织有限时域资源决策流程，明确状态与收益如何进入分段控制优化，并将求解结果转化为逐节点、逐槽的隔离与恢复投入；在攻击效率变化时，复用同一求解器重新规划剩余时域。该项是具体问题上的建模应用与计算流程，不提出新的均衡算法。第二，在分别定义的固定攻击、各自攻击响应及公共执行攻击协议下，对照单动作、静态联合、固定攻击训练和非博弈滚动优化，报告战略依赖、资源配置、成本与计算时间的条件性差异。价值位置与传播条件的匹配对照提供辅助解释，不作为博弈不可替代的证明。D4/D5新增证据仍待人工验收，本文如实列示以供审阅。

全文第2章给出网络攻防模型，第3章说明理论基准、数值求解和重新规划执行过程，第4章报告比较设计、资源计划及适用边界，第5章总结研究结论。

# 2 网络攻防微分博弈模型
'''

extra_method=r'''
## 3.4 从状态和收益到资源计划

求解输入包括网络传播率、入口集合、初始受损状态、双方收益系数、容量上限及控制槽数。对一个给定攻击计划，程序以全部隔离和恢复槽变量为待优化对象：先由式(3)向前计算状态，再由式(4)累计安全损失、业务中断和行动成本，最后以该离散目标及其梯度调用SLSQP。梯度包含某槽行动对后续状态和损失的影响，所以资源配置是整段计划优化的结果，而非将当前受损比例代入式(12)后直接排序。攻击方固定防御计划，以同样方式最小化式(5)的相反数。

在六节点、六槽设置中，防御端有72个槽变量，攻击端仅保留两个入口的12个槽变量。每个防御槽共享同一个容量约束，SLSQP同时处理各节点隔离、恢复的箱约束与容量约束。对于某个节点，增加恢复会降低本地受损及后续外传，增加隔离则立即降低其出边传播；二者引起的安全损失变化要与业务中断和二次成本一起进入目标。式(11)—(13)解释这种取舍，实际数值由离散目标优化确定。

**算法1 分段开环局部响应候选的计算。** 下列流程对应主要匹配实验的强化求解；重规划沿用同一单路径过程。

```text
输入：模型、初态、时域、槽数、积分精度、可行初始攻击和防御计划
对每条登记初始化路径：
  最多进行40次完整更新；每轮先固定同一个当前策略对
  分别求防御局部响应和攻击局部响应，计算当前点的双方偏离与残差
  若改善、残差、响应距离及优化器退出均达标：保存当前候选并停止该路径
  若到达上限仍不达标：保存失败，不能以“迭代结束”替代通过
  否则接受防御响应，再固定新防御求攻击响应，完整更新下一策略对
保留全部路径；使用预先指定主路径，进行多起点偏离及积分精化检查
输出：每槽起止时刻、每节点a/s/r、容量使用与余量、状态、成本和诊断
```

上述攻击与防御的先后更新只属于数值计算步骤，不赋予一方在原博弈中先行承诺的权利。初始匹配实验以均分路径为主，另保留零与随机路径；滚动子问题以继承尾段的暖启动路径为主，另保留零与随机路径，不能根据最终损失择优删掉其他路径。匹配与重规划的SLSQP单次迭代上限为300，停止参数为\(10^{-10}\)；旧补充C2强基线使用\(10^{-11}\)，它们都不是全局误差保证。

输出可以直接解释为归一化资源配置。例如，既有seed11、B=1.2的D格计划在第一槽对节点0分配隔离0.161214、恢复0.267405，对节点1分配隔离0.154894、恢复0.185808；节点2至5的恢复依次约为0.021641、0.044004、0.000939、0.000939，隔离均近零。该槽总容量使用约0.836845，低于上限1.2，攻击投入为入口0约0.318581、入口1约0.481419。后续各槽独立保存，不用这一示例替代完整计划。完整36行数据见[原计划全部节点—时槽动作](figures/data/original_allocation.csv)，对应第4章的固定示例。实际平台仍需校准归一化投入与具体隔离、恢复能力之间的转换关系。

## 3.5 攻击条件变化后的剩余时域重规划

重规划保留单次问题的开环结构。在更新时刻\(t_j\)，以实际已执行过程得到的状态\(x^{\mathrm{exec}}(t_j)\)作为新初态，将式(3)—(5)的积分区间换为\([t_j,T]\)，按当时已知参数重新求解剩余槽数\(K_j\)对应的局部开环候选。这里\(j\)为更新序号，\(K_j\)为尚未执行的槽数，上标exec表示实际执行记录。已发生的累计成本对这一子问题为常数，不再重复优化；终端时刻仍为原来的\(T\)，终端权重沿用原定义。

在D5登记情景中，更新时刻为5、20/3、25/3，剩余时域分别为5、10/3、5/3，剩余槽数为3、2、1。每次仅执行新防御计划的首槽，下一更新点重新读取实际状态，舍弃未执行的旧预测尾段。模型中入口0的有效攻击效率在t=5由0.25变为0.50；这改变状态方程的参数输入，不意味着实际攻击投入被强制翻倍。所有其他参数和目标保持原值。

比较三种执行方式：P继续执行原计划尾段；G在每个更新点重新计算双方开环局部响应候选；R将上一槽已观测攻击持续到剩余时域，仅求防御局部响应。G的攻击计划是内部预测，实际执行攻击由第4章公共协议另行给定；R不读取本槽或未来实际攻击。三者共享事件前执行前缀，G/R从各自已执行状态继续计算，而不是反复使用原轨迹上的预设状态。

**算法2 重新求解与首槽执行。**

```text
执行共同原计划至t=5，观察当前状态并更新已知入口效率
对三个更新时刻：
  G：在实际当前状态上求剩余时域双方局部响应候选，保存全部预测计划
  R：用上一槽攻击作持续预测，求剩余时域防御局部响应
  P：读取原计划对应槽
  各方法仅执行本槽防御；评价器向三方法施加同一条公共实际攻击
  保存实际动作与状态，将槽末实际状态传入下一子问题
汇总前缀与后续实际执行轨迹的目标；预测目标不能替代实际执行目标
```

拼接控制依赖观测历史，因此整条执行轨迹不是t=0选定的单一开环均衡。该实现也没有求解所有状态上的价值函数或反馈最优响应，不能称为Markov反馈Nash均衡。当前验证采用模型内可观测状态、已知事件参数和理想即时动作切换，未包含状态估计误差或计算延迟。D5实现及结果在本稿中按待批准证据报告。
'''

design=d3.split('# 4 实验设计')[1].split('# 5 实验结果与讨论')[0]
design=design.replace('../work_d2/figures/','figures/')
design=design.replace('精确边权及完整参数见补充S1。','精确边权及完整参数见[边权源表](figures/data/matched_edges.csv)和[原D3补充S1](../work_d3/supplement_zh.md)。')
design=design.replace('统计，\\(W\\)固定为','统计，其中\\(|W|\\)是时间窗长度，\\(\\bar s,\\bar r\\)为平均投入，\\(S,Q\\)为投入积分，\\(U_{D,k}\\)为第\\(k\\)槽总防御容量使用。\\(W\\)固定为')
design=design.replace('两组精化比较','其中上标(6)、(12)表示控制槽数，\\(D_u,D_a\\)是同时间对齐后的防御与攻击最大分量差，\\(\\delta J_D\\)为重新求解后的防御损失差。两组精化比较')
design += r'''
本稿的新增证据分为两层。D5-P0读取既有九组G/F防御及各自攻击响应，交叉评价54个冻结配对，未重训防御或重求攻击。D5-run03只使用seed11的D格，在三个容量、两条公共执行攻击、三种防御执行方式下形成18条完整轨迹。E0在事件后入口各投入0.4；E1在t=5共同初态上，固定P的原尾段防御并按变化后参数求攻击局部响应，随后冻结给P/G/R共同使用。E1不针对G/R分别生成，也不是已认证的最坏攻击。两种协议均保留相同的原计划前缀，而不是从t=0开始施加E0或E1。

因此必须区分四种评价：旧公共固定攻击比较使用同一个全时域攻击；旧各自响应评价使用各防御分别对应的攻击；D5的E0和E1各自在同一容量内对三种执行方法使用完全相同的实际攻击。D5总目标采用H=48，H=96/192用于固定执行策略的精化核验。三个种子不是现实随机样本，E0/E1也不是独立重复，不作总体显著性检验。
'''
results=d3.split('# 5 实验结果与讨论')[1].split('# 6 结论')[0]
parts=re.split(r'(?m)^## 5\.[1-4] ',results)[1:]
old1='## 4.4 '+parts[0]
old2='## 4.5 '+parts[1]
old3='## 4.6 '+parts[2]
old4='## 4.9 '+parts[3]
old4=old4.replace('表4','表9')
old1=old1.replace('全部36目标及九组差值见补充S1','全部36目标及九组差值见[四格原始目标与交互](figures/data/matched_four_cells.csv)')
old2=old2.replace('补充图S1展示','[补充图S1](figures/figS01_seed33_state_allocation.png)展示').replace('全部节点用量、状态与成本分解见补充S2。','全部节点用量见[容量表](figures/data/matched_budgets.csv)，完整状态与成本分解沿用[D3补充S2](../work_d3/supplement_zh.md)。')
old3=old3.replace('完整八方法目标和逐配置配对见补充S4。','完整八方法目标和逐配置配对分别见[目标表](figures/data/baseline_all_objectives.csv)与[配对表](figures/data/baseline_pairs.csv)。')
old4=old4.replace('补充S3、S4保留诊断、失败记录与重现入口。','[证据映射](claim_evidence_map.md)保留原始诊断、失败记录与重现入口。')
for name in ['old1','old2','old3','old4']:
    globals()[name]=globals()[name].replace('../work_d2/figures/','figures/')

fixed=rows('paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv')
old1 += '\n**待批准证据：D4固定攻击对照。** 对同样36格固定入口各0.4，并重新优化六槽防御后，九组交互仍全部为正，为0.018120—0.028590，占对应GAME交互的97.124%—99.426%。图4及[九组完整原值](figures/data/d4_four_cell_comparison.csv)同时列出两类结果。这说明在所测构造与局部求解流程中，出现交互不以攻击者战略响应为必要条件。两类交互之差还包含防御重新优化，不能解释为战略响应的纯因果贡献。\n\n![图4 固定攻击与博弈条件的交互](figures/figure_interaction_comparison.png)\n\n**图4 固定攻击与博弈条件下的四格交互（待批准证据）。** 复用D4-P0-1原图，全部九组、H=48；两类防御分别在其训练条件下形成。比值的分母是对应GAME交互，不是防御总损失。\n\n'

p0=rows('reports/work_d5/p0/run02/case_summary.csv')
strategic=r'''## 4.7 攻防策略的战略相互依赖（待批准证据）

令G表示既有Joint-dynamic计划，F表示Fixed-trained计划；\(u_G,u_F\)是相应防御，\(a_G,a_F\)是冻结各防御后保存的局部攻击响应，\(a^{\mathrm{fix}}\)为全时域入口各0.4的公共固定攻击。这里G/F来自旧C2，不能与下一节在事件后逐槽更新的G/R控制器混作同一个实验。D5-P0只对这些保存计划进行读取和交叉重放，没有新增优化。

表4完整列出九组配置。最大隔离和恢复分量变化分别为0.016535—0.041992与0.015336—0.034938，平均每槽容量加权L1差除以容量上限为1.7035%—10.8441%。L1差同时包含重新分配和实际总用量变化，不表示同等比例资源被搬移。攻击响应的最大分量差为0.008701—0.024367，直接攻击入口始终为0、1，未出现新入口。最大攻击投入节点只在54槽中的2槽改变，因此差异主要表现为既有入口间强度和时间安排的微调。

**表4 九组冻结计划的动作与收益差异（待批准证据）。** Δs、Δr和Δa列为最大绝对分量差；L1/B列为平均槽容量加权差占B的百分比；末两列分别以各自响应和公共固定评价中的F损失为分母，正值表示G损失较低。全部目标H=192。

'''
strategic+=table(['种子','B','最大Δs','最大Δr','L1/B(%)','最大Δa','各自响应改善(%)','公共固定改善(%)'], [[r['seed'],r['B']]+[f'{float(r[k]):.6f}' for k in ['max_abs_delta_s','max_abs_delta_r','defense_L1_percent_of_B','max_abs_delta_attack','own_response_D_advantage_percent','common_D_advantage_percent']] for r in p0])
strategic+=r'''
单纯看到控制不同还不足以判断战略适配。将两条攻击响应在同一防御上交叉评价，九组中攻击者使用自身对应响应而非另一条响应，净收益均有正向增加：固定\(u_G\)时增加0.000221495—0.00187105，固定\(u_F\)时增加0.000221657—0.00187383。这是保存候选层面的直接相互依赖证据，幅度仍然很小。表5固定展示seed11、B=1.2的完整收益矩阵，其他配置均保存在[完整交叉收益表](figures/data/p0_payoff_matrix.csv)。

**表5 seed11、B=1.2的防御—攻击交叉评价（待批准证据）。** 防御目标越低越好，攻击目标越高越好；两者不是同一效用，不能相减定义社会收益。G/F表示防御方法，a0为数据文件对公共固定攻击的标签，aG/aF为两条局部攻击响应。

'''
pay=rows('reports/work_d5/p0/run02/payoff_matrix.csv')
strategic+=table(['防御','攻击','J_D','J_A'],[[r['defense'],r['attack'],f"{float(r['J_D']):.8f}",f"{float(r['J_A']):.8f}"] for r in pay if r['seed']=='11' and float(r['B'])==1.2])
strategic+=r'''
在该例中，G相对F的各自响应损失优势为0.021745685，公共固定攻击下则为−0.007757669。由公共固定攻击转为各自响应时，F与G的防御损失分别改变−0.076094162与−0.105597515；三者的算术关系解释了评价差值如何变化，却不构成独立机制的因果分解。攻击方优化的是自身净收益，因此其更优响应可以同时降低防御总损失。结构上，攻击改变状态及伴随边际，防御也反过来改变攻击响应；数值上，保存的双方控制和交叉收益支持这种有限依赖，但不能推出博弈不可替代或其收益具有普遍实践意义。

'''

comp=rows('results/work_d5/replanning/run03/comparisons.csv')
rolling=r'''## 4.8 攻击效率变化后的重规划与执行（待批准证据）

run03完成三个容量、两种公共执行攻击与三方法的18条轨迹。所有方法在t=5前执行相同原计划；随后P保持原尾段，G/R按第3.5节更新。表6报告全部六组事件后防御目标，以及相同绝对差在全时域目标中的相对量级。共同前缀相消，所以前后两种时域的绝对配对差相同，但百分比分母不同，不能互换。完整前/后/全时域状态及成本来源见[执行目标](figures/data/replanning_objectives.csv)与[配对结果](figures/data/replanning_comparisons.csv)。

**表6 全部公共执行攻击下的防御损失（待批准证据）。** 三个J列为事件后[5,10]的H=48目标；ΔP与ΔR分别为P−G和R−G；末两列为全时域相对改善率，以P或R各自全时域损失为分母，单位%。

'''
full={(float(r['B']),r['evaluation']):r for r in comp if r['period']=='full'}
post=sorted([r for r in comp if r['period']=='post'],key=lambda r:(float(r['B']),r['evaluation']))
rolling+=table(['B','攻击','J_P','J_G','J_R','ΔP','ΔR','全域P→G(%)','全域R→G(%)'], [[r['B'],r['evaluation']]+[f'{float(r[k]):.9f}' for k in ['J_D_P','J_D_G','J_D_R','delta_P_to_G','delta_R_to_G']]+[f'{float(full[(float(r["B"]),r["evaluation"])][k]):.6f}' for k in ['percent_P_to_G','percent_R_to_G']] for r in post])
rolling+=r'''
G相对P的绝对损失下降为0.003249673—0.013750905，六组均为正。G与R之间则随攻击协议反转：E0下G在三个容量均较差，差值为−0.000577565至−0.000496245；E1下均较好，差值为0.000768054—0.000827859。图5保留两种攻击、三个容量和正负差异，不将E1的小优势扩展为一般博弈优势。P是原先随时间变化的计划，不是Joint-static；G对P的改善比较的是是否重新规划，而非动态与静态控制的区别。

![图5 重规划配对损失](figures/paired_comparisons.png)

**图5 两种公共执行攻击下的配对比较（待批准证据）。** 原run03图，H=48；正值为G相对该基线损失较低，零基准和E0的负值保留。E0/E1是确定性协议，不是两份随机重复。

表7给出B=1.2首次更新的全部六节点决策。G把节点0的隔离从0.109306提高到0.153268，同时降低节点1的隔离，并小幅调整各节点恢复。节点4、5该槽的两类行动均近零。此时G在E0/E1下获得相同初态和信息，因此首次动作相同；后续状态因实际攻击不同而分化。完整六槽的实际动作见图6、图7，不以预测计划代替执行结果。

**表7 B=1.2、[5,20/3)首个重规划槽的资源配置（待批准证据）。** 数值取E0，G首次动作在E1相同。Δ为G−P，投入均为归一化强度；舍入为0的数值按原精度保留在CSV中。

'''
adj=rows('results/work_d5/replanning/run03/resource_adjustments.csv')
selected=[r for r in adj if float(r['B'])==1.2 and r['evaluation']=='E0' and r['method']=='G' and int(r['slot'])==3]
rolling+=table(['节点','s_P','s_G','Δs','r_P','r_G','Δr'],[[r['node']]+[f'{float(r[k]):.6f}' for k in ['s_P','s','delta_s','r_P','r','delta_r']] for r in selected])
rolling+=r'''
![图6 E0实际资源配置](figures/resources_E0.png)

**图6 B=1.2、E0下全部六节点的实际隔离与恢复（待批准证据）。** 复用run03原图，三方法均保留事件前后完整控制；虚线标记t=5。零投入、节点差异及末期变化原样呈现，不能用单一节点代替全网配置。

![图7 E1实际资源配置](figures/resources_E1.png)

**图7 B=1.2、E1下全部六节点的实际隔离与恢复（待批准证据）。** 与图6相同的显示范围，实际公共攻击由针对P尾段的局部攻击响应冻结得到；它不是G内部求得的预测攻击。两图的数据为executed_controls，而非planned_controls。

G在B=1.2首次重规划中预测入口攻击约为(0.491514,0.308486)，R持续预测上一槽的(0.386221,0.413779)。E0实际为(0.4,0.4)，E1首槽实际约为(0.499839,0.300161)。两种预测在不同协议中的适配不同，与表6的排名反转相容；这属于结果解释，不是预测误差对收益影响的因果证明。特别是E1专门针对旧P构造，不能据此声称G在任意战略攻击下优于R。

总目标还必须与安全分项分开。B=0.6、E1下，G的总损失比R低约0.000772885，但累计加权受损损失高约0.001868119；B=1.8、E0下，G的受损损失低约0.005454964，总损失却高约0.000577565。业务与控制成本可以改变总目标排名。图8给出B=1.2、E1全部六资产的实际受损状态，三方法曲线接近，未通过截断纵轴放大差异；E0全节点状态与完整成本分解一并保留在图表目录。

![图8 E1执行状态](figures/states_E1.png)

**图8 B=1.2、E1下全部六资产的实际受损比例（待批准证据）。** 复用run03的H=192固定执行策略重放图，纵轴为实例组受损比例；曲线不是单台服务器被攻击概率，也不是重规划预测状态。主目标表仍采用H=48。

**表8 单次重规划实际耗时（待批准证据）。** 秒，18次G与18次R；包括各自登记初始化和H=48停止检查，额外H=96偏离审计、公共E1生成及绘图另计，不重复累加嵌套调用时间。

'''
tim=rows('results/work_d5/replanning/run03/timing_summary.csv')
rolling+=table(['方法','次数','最小','中位数','最大','合计'],[[r['method'],r['count']]+[f'{float(r[k]):.6f}' for k in ['min','median','max','sum']] for r in tim])
rolling+=r'''
G单次耗时中位数为17.94秒，R为3.88秒，战略预测并非无计算代价。原始离线计划的历史求解耗时无法可靠拆分，记录为缺失，不以读取文件的耗时替代。模型时间未进行物理标定，且没有模拟求解期间的执行延迟，因此不能通过将秒数与槽长5/3直接比较来宣称实时可用。实验也没有无扰动对照，G相对P的差异不能单独归因为入口效率变化，还可能受到剩余时域、重新初始化及重新求解的共同影响。

'''
old4+=r'''
**D5-run03数值核验（待批准证据）。** 保存记录包含960次SLSQP起点优化，失败0次；最终候选的最大当前投影残差约9.9689×10⁻⁵，接近10⁻⁴门槛；最大响应控制距离约6.2410×10⁻⁵，三路径最大控制差约6.2926×10⁻⁵。H=48/96/192固定执行策略的目标、分项与共同时点状态检查满足10⁻⁶登记容差。另用DOP853重积分实际动作，并核对共同前缀、实际攻击一致性、重规划初态、只执行首槽及R不读取未来攻击，共3909项作者侧复核通过。这是另一个积分算法的复核，仍复用原模型函数，不是独立模型实现或外部同行审稿。

run01因JSON布尔编码失败，run02在B=1.2通过后因CSV写入中断，最终run03承接已通过的B=1.2及其原始计时，其余组按原输入完成。失败和中间记录保留，不计为三次独立成功。D6只读取这些结果并核对表格，没有重跑优化、积分或上述研究测试。

综合而言，本文已保存证据支持指定合成网络上的容量可行计划、局部响应差异及评价依赖；它不支持纯开环Nash存在性、全局求解收敛、跨策略类无偏离或生产云有效性。两组K精化不能覆盖九组G/F比较，更不能认证滚动控制的连续策略收敛。有限的网络规模、合成参数、状态可观测假设和未经延迟建模的执行方式共同限制外推。

'''
conclusion=r'''# 5 结论

本文在有限时域非零和攻防框架下，将入口攻击、来源节点隔离和本地恢复通过受损状态方程联结，形成从状态与收益输入、分段常值优化到逐节点资源配置的计算流程。PMP/KKT用于解释行动边际与共享容量竞争，实际计划由RK4直接射击、离散灵敏度、SLSQP及交替局部响应得到。理论开环Nash、受限策略类与数值局部候选始终分开，停止诊断不替代全局均衡证明。

既有九组方法比较显示，联合动态计划相对固定攻击训练计划在各自攻击响应下的改善仅为0.029%—0.286%，公共固定攻击下则全部不占优；原网络相对仅恢复的负反例仍成立。待批准的D5决策审计进一步显示，防御与攻击响应均发生可测变化，但主要体现为既有节点、入口和时槽内的微调。待批准的run03结果展示了以实际状态重新求解剩余时域、只执行首槽的过程：G相对原计划在六组公共攻击比较中降低总损失，却在E0下略逊于R，在E1下略优，且计算开销更高。重规划拼接既不是原时刻的单一开环均衡，也不是Markov反馈Nash均衡。

价值位置与传播条件的匹配结果保留为配置解释，待批准的固定攻击对照表明该交互并非战略响应独有。两组控制槽精化保持目标交互方向，但六槽候选在十二槽中仍存在已发现偏离。因此，本文的结论是指定模型和评价协议下可检查的资源决策及其收益边界，不是博弈普遍领先、实时部署有效或新均衡算法的证明。真实参数与行动映射的校准、更广策略类的偏离控制及执行延迟的影响仍需另行研究。

'''
refs='## 参考文献'+d3.split('## 参考文献')[1]
paper=intro+model+'# 3 动态防御决策求解方法\n'+method+extra_method+'\n# 4 数值实验与分析\n'+design+old1+old2+old3+strategic+rolling+old4+conclusion+refs
# Original graph numbering: inserted D4 figure shifts old allocation image from 3 to 5 if left as is.
# Use simple order: original 1/2, D4 3, allocation 4, rolling figures 5--8.
paper=paper.replace('图3','图TMP').replace('图4','图3').replace('图TMP','图4')
write('paper_v1_zh.md',paper)
shutil.copy2(ROOT/'paper/work_d3/references.bib',OUT/'references.bib')

copies=[]
def copy(src,dst):
    source=ROOT/src; target=OUT/dst; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    copies.append({'source':src,'destination':dst,'sha256':sha(source)})
for name in ['fig01_matched_network','fig02_losses_interactions','fig03_temporal_allocation','figS01_seed33_state_allocation']:
    for ext in ['png','pdf','svg']: copy(f'paper/work_d2/figures/{name}.{ext}',f'figures/{name}.{ext}')
for ext in ['png','pdf','svg']:
    copy(f'paper/work_d4/P0_01_fixed_attack/figure_interaction_comparison.{ext}',f'figures/figure_interaction_comparison.{ext}')
for name in ['paired_comparisons','resources_E0','resources_E1','states_E0','states_E1','resource_use']:
    for ext in ['png','pdf','svg']: copy(f'results/work_d5/replanning/run03/figures/{name}.{ext}',f'figures/{name}.{ext}')
for name in ['matched_edges','matched_four_cells','matched_controls_all_nodes','matched_budgets','baseline_all_objectives','baseline_pairs','counterexample_cross_evaluation','robust_interactions','robust_cross_class','k_control_distances','environment_cross_environment_errors']:
    copy(f'paper/work_d2/tables/{name}.csv',f'figures/data/{name}.csv')
copy('paper/work_d4/decision_reorientation_20261112/evidence/saved_allocation_seed11_B1.2_D.csv','figures/data/original_allocation.csv')
copy('paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv','figures/data/d4_four_cell_comparison.csv')
for name in ['case_summary','payoff_matrix','defense_by_node_slot','attack_by_node_slot','response_quality']:
    copy(f'reports/work_d5/p0/run02/{name}.csv',f'figures/data/p0_{name}.csv')
for name in ['comparisons','objectives','executed_controls','planned_controls','resource_adjustments','attack_prediction_comparison','timing_summary','timing','quality_summary','independent_checks','solver_audit','trajectories','loss_component_comparisons']:
    copy(f'results/work_d5/replanning/run03/{name}.csv',f'figures/data/replanning_{name}.csv')
write('figures/source_manifest.json',json.dumps(copies,ensure_ascii=False,indent=2))
print(json.dumps({'paper_chars':len(paper),'copied_artifacts':len(copies),'input_files':len(manifest)},ensure_ascii=False))
