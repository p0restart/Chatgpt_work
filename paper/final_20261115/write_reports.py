"""Write finalization evidence, review dispositions, and delivery reports."""
from pathlib import Path
import hashlib,json,difflib
import pandas as pd
BASE=Path(__file__).resolve().parent
def write(name,s):(BASE/name).write_text(s.strip()+'\n',encoding='utf-8')
v=json.loads((BASE/'results/verification.json').read_text());a=json.loads((BASE/'results/manuscript_audit_summary.json').read_text())
data=pd.read_csv(BASE/'results/objective_recalculation.csv')
loss=[]
for B in [.6,1.2,1.8]:
    import numpy as np
    for scenario in ['aG','a0','aBR_F']:
        d=data[np.isclose(data.B,B)&(data.scenario==scenario)].set_index('plan')
        g=d.loc['G','J_D'];f=d.loc['F','J_D']
        loss.append(dict(B=B,scenario=scenario,J_D_G=g,J_D_F=f,G_minus_F=g-f,percent_relative_to_F=100*(g-f)/f))
pd.DataFrame(loss).to_csv(BASE/'results/gf_loss_differences.csv',index=False,float_format='%.17g')
rows=[]
for B in [.6,1.2,1.8]:
    folder=BASE/f'raw_d7/results/static/B{B}'
    m=json.loads((folder/'model.json').read_text());attacks=json.loads((folder/'cross_attacks.json').read_text())
    for p in ['G','F']:
        u=json.loads((folder/f'{p}_controls.json').read_text())
        for scenario in ['aG','a0','aBR_F']:
            for k in range(6):
                defense=sum(np.array(u[1][k])*m['b_s']+np.array(u[2][k])*m['b_r']);attack=sum(np.array(attacks[scenario][k])*m['d_a'])
                rows.append(dict(B=B,plan=p,scenario=scenario,slot=k+1,defense_use=defense,defense_limit=B,attack_use=attack,attack_limit=m['A'],passed=defense<=B+1e-10 and attack<=m['A']+1e-10))
pd.DataFrame(rows).to_csv(BASE/'results/per_slot_budget_checks.csv',index=False,float_format='%.17g')
assert all(d['passed'] for d in rows)
write('00_来源盘点与执行边界.md',f'''
# 来源盘点与执行边界

日期：2026-11-15。研究题目：《基于非零和微分博弈的有限资源网络防御决策方法》。当前用户明确授权实际完成D7状态恢复、绘图、第四章修订、五章合稿和审计。附件中的启动文字作为待核查工作材料，其表值、文献判断和建议结构不自动取得用户指令或审批记录的效力；未执行附件提供的脚本。

交接包已完整读取。原五章稿为写作基础，单独提供的第三章为优先基准。附件状态CSV只有表头，没有轨迹；其余重组汇总不是原始实验。原始D7完整控制和状态代码均已找到，不存在状态数据缺失阻塞。

## 数据身份与来源

- 原项目`paper/work_d7/`，固定拓扑ID为D7_asymmetric_cloud_fixed_20261114。
- `config_new_topology.yaml`、`results/static/B*/model.json`和八边拓扑CSV共同确认六资产、边方向、q5=4、入口1/2、T=10、K=6及三容量。
- `results/static/B*/G_controls.json`与`F_controls.json`保存每方案6×6隔离和6×6恢复控制；攻击序列在`cross_attacks.json`，均为6×6含非入口零值。
- `cross_evaluation.csv`保存每容量六个防御—公共攻击配对及全部成本分项。原方案各自训练攻击与公共执行攻击已区分。
- `rolling_event_B*/B*/E*_M_executed.json`为实际执行控制；planned_controls不是执行控制。无参数事件对照为rolling_control_B1.2。
- 状态与目标的原始积分为`source_snapshot/src/core.py`，本次使用冻结副本；独立DOP853在新脚本中显式实现来源行—目标列传播。
- `raw_d7/`保存本次只读来源副本；各文件SHA256及字节数见raw_manifest.json，原ZIP校验码见intake_manifest.json。原D7源文件和历史不利结果均未覆盖。

## 本次执行范围

实际完成18组静态交叉评价、24条滚动执行的固定控制复算，主容量两种公共攻击的4条完整状态轨迹，各1153点。结果表、控制长表、108条静态逐槽预算检查、原始求解日志及状态数据均保留。没有重新进行攻防优化、改变参数、运行新的K精化或将D8结果混入D7。

本次复算环境为Python {v['environment']['python']}、NumPy {v['environment']['numpy']}、SciPy {v['environment']['scipy']}、Pandas {v['environment']['pandas']}、Matplotlib {v['environment']['matplotlib']}。确定性重复积分不是独立随机样本。隔离目录复现仍在同一机器，不等于第二机器复现或独立重新优化。

本次授权为最终合稿和复算范围授权，不登记为新G1/G2结果批准，不改变历史D4/D5/D7/D8待审事实。正式投稿、具体会议模板及作者信息仍由作者决定。

交付包只附复现所需的研究原始数据与代码，不附第三方论文全文及完整文本提取。审稿时读取的本地原件保留在原项目，文献表提供出版链接与访问层级；相关历史审稿路径不是数值复算依赖。
''')
write('01_数学与实验审计报告.md',f'''
# 数学与实验审计报告

## 审计结论

冻结控制复算的{v['checks']}项数值检查全部通过，最大差异为{v['max_error']:.16g}；独立读取原始CSV/JSON的{a['checks']}项稿件核对通过。原优化记录1544次尝试均成功。主结论仅为模型内行动计算及条件性响应，不支持全局均衡或普遍优势。详细检查见results/recalculation_checks.csv、manuscript_audit_checks.json和per_slot_budget_checks.csv。

## 数学一致性

1. βji为来源j到目标i，源端sj乘来源受损xj，冻结实现使用β转置乘来源向量。恢复ri作用在本地xi，非入口直接攻击为零。
2. 连续方程在可行控制下状态立方体正不变；该固定控制轨迹性质不推出博弈均衡存在。数值轨迹额外检查区间约束，没有裁剪状态。
3. JD为最小化的安全、业务中断、隔离和恢复成本；JA独立最大化受损收益减攻击成本，不能使用JD极小极大替代。终端权重在D7全部为零。
4. A/B是逐时瞬时容量，隔离和恢复共用B；二次行动成本在时域上累计，二者不混用。
5. 式（5）仅给出理论开环Nash定义。式（6）/（7）的BR为数学最优响应集合定义，实际SLSQP产生局部数值响应。交替停止、局部残差和多起点均不证明全局Nash、唯一性或全局收敛。
6. 第三章原文逐项应用17条机械替换后与最终章节完全一致。只统一数学排版、四个公式编号和表3-1题名；章节3.1—3.5和五步算法均未变化。diff及替换字典可审阅。
7. 公式编号统一（1）至（10），图4-1至4-4、附图A-1至A-4、表3-1及表4-1至4-8均有唯一来源和引用。

## 实验复核

原完整G/F防御分别固定，执行攻击在同一配对内完全相同，初态为(0.1,0,0,0,0,0)。DOP853用rtol=1e-12、atol=1e-14，各区间独立积分以避免跨控制不连续边界混用。每区间193个等距输出点，去除重复边界后1153点。RK4 H=48/96/192在共同时间点和目标分项上复核，使用更严格1e-8检查线，全部通过。

18个静态配对的JD、六成本分项与原表一致；24条滚动轨迹分别复核全时域及事件后成本和保存状态。图4-3、附图A-1的xq严格按(1,1,1,1,4,1)/9加权。另用导出状态的Simpson数值求积检查安全损失，而非由累计目标重构状态。

主容量公共aG下，G/F的JD约9.326646704193193和9.327080703313605，G−F约−0.000433999120412；公共a0下约9.467228487398313和9.466796376106583，G−F约+0.000432111291730。全部未舍入值及以F为分母的百分比见gf_loss_differences.csv。与历史RK4的差异远低于1e-5提示线。

G的安全改善不等于所有资产/所有时刻改善。aG下网关早期略高，Web期末高约0.001044，数据库期末低约0.000189；xq早期最大正差约4.24e-6。a0下G累计安全损失减少0.011547，而非安全成本增加约0.011979，因此综合损失略高。该负结果已保留在摘要、4.3和结论。

滚动百分比统一采用事件后[5,10]的P损失作分母；E1是针对P按JA生成并冻结的公共攻击，不是针对每方案的最坏攻击。G/R排名随E0/E1反转，无事件对照、计算耗时及作用边界保留。重规划没有被列为核心创新。

## 发现与修复

冻结审稿稿中发现并修复：表4-8容量浮点展开、a0相对差的六位小数末位、DOP853输出间隔措辞、对warm路径距离的模糊说明、正文缺少实际求解设置、包外拓扑图依赖。另在合稿数值自检时修正网关平均行动差和xq短时正差的手工近似。所有正式表格由数据生成，未调整参数或替换原控制。

最终独立检查脚本不调用合稿中的表格计算函数，直接读取原始JSON/CSV核对。三份模拟审稿与主代理事后算术审计分开，详细意见和处理见reviews/及04_独立审稿综合与修订闭环.md。

## 未主张及剩余风险

积分精化验证固定控制计算，不证明K=6控制策略收敛。没有第二机器重新优化、现实参数标定、真实平台操作或统计显著性。单一网络与微小收益限制外推，新颖性应以问题结构和评价增量论证，不能按通用博弈理论首创或性能领先投稿。具体会议及页数要求尚未提供，当前16页为包含全部五章和补充图的单栏审阅版。
''')
write('02_绘图数据来源与复算记录.md','''
# 绘图数据来源与复算记录

主问题为两种防御配置在共同攻击下如何影响入口、高价值数据库及全网状态。三个面板分别承担入口响应、下游关键资产和系统安全损失连接的作用。数据来自完整控制重新积分，不来自摘要表、损失反推、插值形状或示意函数。

| 图号 | 文件前缀 | 来源与含义 |
|---|---|---|
| 4-1 | fig4_1_topology | D7固定八边拓扑原图，包内保留原输入 |
| 4-2 | fig4_2_common_attack_difference | 18组配对复算后JD的G−F，纵轴乘1000 |
| 4-3 | fig4_3_GF_state_common_aG | 公共aG，G/F完整防御分别冻结；x1、x5、xq |
| 4-4 | fig4_4_rolling_gain | 事件后损失相对P降幅，E0/E1分面 |
| A-1 | figA1_GF_state_common_a0 | 公共a0的状态复核，完整轨迹从零纵轴 |
| A-2 | figA2_GF_state_difference_aG | aG下1000×(G−F)状态差 |
| A-3 | figA2_GF_state_difference_a0 | a0下1000×(G−F)状态差；保留文件前缀，正文图号唯一 |
| A-4 | figA4_GF_defense_actions | G/F全部72防御分量热图，共用0至0.4色阶 |

所有输出均有PNG 400 dpi、PDF、SVG。图4-3与A-1保留零起点纵轴，微小差值另图显示并标明符号和倍数，不以裁切轴夸大收益。绘图不使用平滑拟合。状态采样为直接DOP853等距输出，RK4细化独立交叉核对。

源数据与结果：gf_state_common_aG.csv、gf_state_common_a0.csv各2306行，包含每方案1153时点和全部六状态；xq与累计成本为追加审计字段。*_G.csv及*_F.csv为每方案原输出。objective_recalculation.csv保存18组复算全部成本；state_differences.csv保存逐状态的极值及对应时间；complete_static_defense_controls.csv保存三容量全部G/F控制；per_slot_budget_checks.csv保存108条静态预算检查。

模型、原完整控制、公共攻击、初始参数、源码版本和种子均在raw_d7及raw_manifest.json中冻结。状态积分与绘图为reproduce.py，结果复核为audit.py。其运行不会重新优化或更新原D7文件。

最终8幅图PDF的碰撞审计全部PASS、零警告；有效字形尺寸最低7 pt。对齐JSON保存多面板实际绘图区几何，报告通过；拓扑为单画布，不适用多子图对齐。最终人工视觉检查了曲线、面板、轴、图例、全图和稿件嵌入效果。图中文字适合当前双栏通栏宽度，模板缩图后需按实际宽度再次核对。
''')

diff=[]
for i,name in [(1,'第1章_引言.md'),(2,'第2章_网络攻防系统模型.md'),(3,'第3章_已批准基准版_请保留.md'),(4,'第4章_含状态演化图待补.md'),(5,'第5章_结论.md')]:
    old=(BASE/'source_handoff'/name).read_text(encoding='utf-8');new=(BASE/f'chapters/chapter{i}.md').read_text(encoding='utf-8')
    diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=f'handoff/chapter{i}',tofile=f'final/chapter{i}'))
write('chapters/full_change.diff',''.join(diff))
write('03_逐章修改记录.md','''
# 逐章修改记录

摘要：改为问题、行动计算、公共攻击证据和收益边界的闭合叙述；增加主容量真实G/F数字，不宣称显著或普遍优势。

第一章：压缩背景及重复声明，明确有限资源的资产、行动、时序与强度问题。补充与Preciado、Paarporn及Tian近邻研究的具体结构/计算差异，不把使用微分博弈或最佳响应作为原创理论。参数事件实验保留为补充。

第二章：保留原状态方程、收益函数、约束及开环Nash理论基准；修正策略集合措辞，将“非入口攻击为零”明确归入攻击可行集。统一β来源—目标、状态比例、瞬时容量、累计损失和文内引用。固定控制状态存在唯一性不扩大为均衡存在性。

第三章：保留确认基准的核心内容、五步ABR-DAD及3.1—3.5结构，只登记17项机械性替换。公式BR、防御行动、资源占用排为（6）至（9），表题补为3-1，变量代码式写法改为数学格式；Word原生公式不改变数学关系。全部替换可反向追踪，自动检查与基准应用替换后的文本完全一致。

第四章：删除空模板及条件写作备注；恢复D7完整控制并新增公共aG状态三联图、a0复核、差值和G/F行动热图。代表性行动表补全原稿“—”值，增加G/F平均行动对照，明确持续受损积累和短时反向。两种公共攻击均给出完整成本分解，区分安全损失与综合损失。滚动实验压缩并保留无扰动对照、E0/E1反转和求解代价。根据隔离审稿补全求解设置、指标及warm规则。

第五章：围绕行动计算、状态证据与成本权衡总结；保留固定攻击下G略劣、重规划并非独占收益和真实平台映射缺口。未来工作不写作已完成结果。

参考文献：15条与文内引用统一。[7]维持交接稿正确的时机博弈论文，不用历史D7的另一篇时间微分博弈论文替换；[12]作者顺序以出版社书名页确认，1993为第二版版权年，2008为修正印刷年。访问层级与核查来源另表记录。

图表与版式：正文四图、附录四图，九张表；公式（1）至（10）。旧滚动图号统一为4-4，新增状态图为4-3。Word公式为原生OMML，PDF由Word实际导出；修复标题主题边线及小表跨页。保留完整五章，当前16页单栏审阅版，不假称符合未提供的具体会议页数。

逐行差异见chapters/full_change.diff，第三章单独差异见chapter3_changes.diff。原始交接材料及D7结果保留。
''')
write('04_独立审稿综合与修订闭环.md','''
# 隔离模拟审稿综合与修订闭环

三个席位分别在独立上下文读取同一不可变稿件与证据包，未互相传递意见，未写入或覆盖项目文件。稿件SHA256为e6fbb9f5433b79de50d206087479f7ba6fa744140974b08b3e12842b589a66c2。侧重分别是数学/算法、实验/复现、贡献/叙述。三份报告形成后冻结，随后由主代理进行算术和文件审计，再修订终稿；没有根据综合结果改写原意见来制造共识。

这属于多上下文模拟审稿，不是外部专家评审，不等于第二机器实验复现。三个席位共用用户材料与同一计算环境，无额外外部模型或私人专家身份。

## 共识与分歧

三个席位均认为核心模型与数据边界相符，没有发现阻止当前有限场景结论成立的数学或算术错误。数学席位和贡献席位共同要求补足正文求解设置；三者均指出容量显示问题。贡献席位提出近邻研究区分，实验席位指出可迁移复现依赖，二者不写作多人共识。各自关注点和严重程度原样保留。

## 问题处理

| 原意见 | 处理 | 验收证据 |
|---|---|---|
| R1-m1 / R3-M2 设置与指标定义不足 | 4.1增加ftol、maxiter、40次更新、无阻尼、归一化分母、残差投影及距离范数 | 冻结源码和协议；终稿4.1 |
| R1-m2 warm参照不明确 | 4.1和4.5明确其他路径相对warm的最大控制分量差，最终预选warm | run_replanning.py；终稿4.1/4.5 |
| R1-m3 / R2-m1 / R3-m1 容量浮点展开 | 表4-8统一一位小数 | audit.py表4-8检查 |
| R2-M1 拓扑图依赖外部目录 | 拓扑原图及SHA写入包内，脚本优先读取包内副本；隔离无历史路径复跑 | isolated_reproduction.json及日志 |
| R2-m2 百分比末位 | a0相对F差改为0.004564% | 原始cross_evaluation.csv及gf_loss_differences.csv |
| R2-m3 DOP853子步措辞 | 改为192个输出间隔，明确自适应内部步长 | 4.3及reproduce.py |
| R3-M1 与先例区别过于概括 | 引言新增近邻研究比较段，不声称先例没有某机制 | 本地原文定向阅读及1.2 |
| R3-m2 第7条两篇文献混淆风险 | 当前正确条目保留，审计明确两篇论文和访问层级 | 05_参考文献核验报告.md |
| R3-m3 页数及重复边界 | 保留确认第三章，其他章节已压缩；具体模板套版保留为投稿行政事项 | 逐章diff、16页PDF |

事后独立算术检查64项通过，数值复算530项通过，8幅图的PDF碰撞及字号检查通过。稿件的可支持定位为有限资源防御行动计算及共同攻击下的条件性响应。新颖性竞争力、真实部署与控制离散精化的科学限制继续保留，不以修辞消除。

具体会议未指定，因此本报告不给出录用概率或对某EI会议的最终适配保证；建议作者按已完成内容选择会议后再套版并确认作者及声明。
''')

write('05_参考文献核验报告.md','''
# 参考文献核验报告

核验日期2026-11-15。正式条目15篇，均在正文被引用。作者前缀、题名、年份、卷期页码/文章号、DOI或报告号按原件及出版来源核对。全文可访问不等于整篇逐式验证；未读取全文的明确限制如下。不声称系统综述、撤稿普查或创新性认证。

| 编号 | 核验来源与实际访问层级 | 结果及正文用途 |
|---|---|---|
| 1 | [SCITEPRESS原PDF](https://www.scitepress.org/Papers/2023/117789/117789.pdf)检索可读元数据；本地原PDF提取首页及模型 | Li/Huang/Zhao等、2023、152–162、DOI一致；云图与多阶段随机博弈 |
| 2 | [作者arXiv](https://arxiv.org/abs/1309.6270)，仅摘要/元数据及journal reference | 五作者顺序、2014、1(1):99–108及IEEE DOI一致；有向网络预防/纠正配置，不引未读定理 |
| 3 | [NSF原稿](https://par.nsf.gov/servlets/purl/10574678)与本地原件首页、模型 | Paarporn/Xu、IEEE CSL 8:2421–2426、2024及DOI一致；两阶段预防/恢复竞争 |
| 4 | [出版社预览](https://www.sciencedirect.com/science/article/abs/pii/S0140366425001057)及本地原件首页、§4–6 | Tian/Gan/Lin等、237:108148、2025及DOI一致；已有云传播非零和开环先例，不继承其均衡证明 |
| 5 | [出版社预览](https://www.sciencedirect.com/science/article/abs/pii/S1389128623000804)及本地原件首页、模型/算法 | Zhang/Mi/Liu等、224:109635、2023及DOI一致；无标度网络微分博弈，不将real-time题名当本研究时延证据 |
| 6 | [出版社记录](https://www.sciencedirect.com/science/article/pii/S0167404823000974)及本地原件首页、§3–4 | Zhang/Mi/Fu等、129:103187、2023及DOI一致；势微分博弈，不移植势结构或全局保证 |
| 7 | [计算机工程官方页](https://www.ecice06.com/CN/10.19678/j.issn.1000-3428.0063866)，仅摘要/元数据 | 孙鹏宇、张恒巍、谭晶磊等；基于时机博弈的网络安全防御决策方法；2022,48(11):145–151；DOI一致。正文仅描述时机选择，不冒称读过全文 |
| 8 | [计算机应用研究官方页](https://www.arocmag.cn/abs/2023.01.0011)及本地原PDF提取 | 胡春娇/陈瑛/王高才、40(9):2832–2837、2023及DOI一致；阶段内微分、阶段间Markov |
| 9 | [Springer出版社全文](https://link.springer.com/article/10.1186/s42400-026-00577-4)及本地原件 | Lou/Zhao/Wang等、Cybersecurity 9:143、2026及DOI一致；仅介绍其不完全信息协同设计，不认证其推断/均衡理论 |
| 10 | [作者机构元数据及摘要](https://experts.illinois.edu/en/publications/constrained-model-predictive-control-stability-and-optimality/)，仅摘要/元数据 | Mayne/Rawlings/Rao/Scokaert、36(6):789–814、2000及DOI一致；首段执行思想，不移植稳定性结论 |
| 11 | [SIAM图书页](https://epubs.siam.org/doi/book/10.1137/1.9781611971132)及原记录1999版版权核对 | Başar/Olsder、2nd ed.、SIAM 1999；只用开环信息结构/非零和概念，非整本全文已读 |
| 12 | [Springer书名及版权页](https://link.springer.com/content/pdf/bfm:978-3-540-78862-1/1)与[图书页](https://link.springer.com/book/10.1007/978-3-540-78862-1) | 书名页作者顺序Hairer/Nørsett/Wanner；Second Revised Edition；1993版权，2008 corrected 3rd printing，不更换为2008新版。只核对前置页、目录及元数据 |
| 13 | [Springer图书页](https://link.springer.com/book/10.1007/978-0-387-40065-5)，仅元数据/目录 | Nocedal/Wright、第2版2006及DOI一致；一般约束优化背景 |
| 14 | [原报告公开副本](https://degenerateconic.com/uploads/2018/03/DFVLR_FB_88_28.pdf)及[SciPy1.11.4方法文档](https://docs.scipy.org/doc/scipy-1.11.4/reference/optimize.minimize-slsqp.html) | Kraft、1988、DFVLR-FB 88-28；未查到DOI不填写，不将SLSQP当全局优化 |
| 15 | [Princeton出版记录](https://press.princeton.edu/books/ebook/9781400842643/calculus-of-variations-and-optimal-control-theory-pdf)、[2012出版社目录](https://assets.press.princeton.edu/catalogs/math12.pdf)和[作者教学书页](https://liberzon.csl.illinois.edu/teaching/cvoc/) | Liberzon、2012、书名及出版社一致；一般最优控制背景，不引未经证明的全局命题 |

## 第7条专门说明

历史D7引用的是另一篇《基于时间微分博弈的网络安全防御决策方法》，作者顺序为孙鹏宇、谭晶磊、李晨蔚、张恒巍，刊于《信息网络安全》2022,22(5):64–74，DOI 10.3969/j.issn.1671-1122.2022.05.008。其本地原件不能作为当前[7]的全文证据。两篇均有独立题名/DOI，不是同一文献的更正版本。本次保留交接稿正确的《计算机工程》条目，并使引言主张限于官方摘要支持的时机选择。

## 访问限制

部分出版社直接打开403或前置页初始地址超时，检索缓存/本地原件与后续成功入口均分别记录，不伪称所有在线全文已访问。[12]出版社书目网页作者展示顺序与书名页不同，最终按书名页顺序；年份区分版次与印刷。[14]公开副本不等于出版社新版本。本次参考文献支持背景与方法来源，不构成已证明本文新颖性的结论。
''')
write('最终验收报告.md',f'''
# 投稿前最终验收报告

日期：2026-11-15。内容合稿、真实状态绘图、固定控制核验、全文润色和审稿修订已完成；未执行投稿。当前Word/PDF为包含全部五章、参考文献及四幅补充图的16页单栏审阅版，具体会议套版尚未验收。

## 已完成

- [x] 五章全文、摘要、关键词和15条参考文献合稿完成；正文Markdown、Word及PDF均已生成。
- [x] 第三章模型解释、五步算法、3.1—3.5结构保留；17项机械修改逐项登记并自动回放匹配。
- [x] D7六资产、八边、方向、容量、初态和收益函数与原始模型核对，无参数调整。
- [x] 主图在同一公共aG下比较冻结G/F完整防御；a0独立复核，所有状态均由原方程积分。
- [x] 两个场景各有2306行状态长表，含全部六状态、加权状态及累计成本；脚本、原始控制、哈希和日志齐备。
- [x] 18组静态交叉及24条滚动轨迹复算，共{v['checks']}项检查全部通过，最大差异{v['max_error']:.6g}。
- [x] 独立原始数据稿件核对{a['checks']}项通过，108条静态逐槽攻防预算检查通过；安全/综合损失分开。
- [x] 8幅正式图提供400 dpi PNG和PDF/SVG，全部PDF碰撞及字号检查通过，多面板对齐通过。
- [x] 同一机器、缺少历史D7预期路径的隔离目录内完整重新积分出图通过，目标结果与交付值一致；非跨机器重新优化。
- [x] 三个隔离上下文的模拟审稿完成，全部具体可修事项已处理；审稿原意见与综合处置分别保存。
- [x] 公式1—10、图4-1—4-4、附图A-1—A-4和九张表引用核对，无待补状态图或条件写作备注。
- [x] 15条文献核验与访问层级逐条登记，当前[7]与历史另一论文明确区分。
- [x] Word为231处原生OMML数学对象，PDF由本机Word真实导出；16页页面渲染已检查，无越界/缺字标记。标题主题边线与小表跨页已修复。

## 保留的结果与限制

G并非普遍优于F。B=1.2时公共aG下G−F约−0.000434，公共a0下约+0.000432；安全损失下降未必覆盖行动成本。网关早期和Web期末仍有G受损更高的局部结果。滚动G/R的优劣随E0/E1反转，收益不全归因于博弈。

单一合成网络、局部数值响应、未做当前任务内K策略类精化、没有实云标定与执行映射均保留为科学边界。530项数值检查不是530个独立实验样本，不能宣称统计显著。隔离模拟审稿不是外部同行意见；固定控制复算不是独立全流程优化。

## 尚未验收的投稿事项

| 严重程度 | 项目 | 当前状态与最短补齐方式 |
|---|---|---|
| 投稿行政事项 | 具体会议、模板、页数上限及语言要求 | 未提供，确定目标后按模板套版；当前16页不冒称符合任一特定会议页限 |
| 投稿行政事项 | 作者姓名、单位、通讯方式、基金及利益声明 | 未提供，不在稿中虚构；由作者填写确认 |
| 科学推广限制 | 现实标定、K精化、参数敏感性、外部复现 | 不属于本次冻结控制合稿的新增实验，正文已限定结论；不得以本交付替代证据 |

不存在阻止本次状态绘图或全文合稿的原始数据缺失。原始通用DOCX渲染器因本机没有LibreOffice失败，已使用现有Microsoft Word完成真实PDF导出和页面核验，排版交付已完成。后续Word再导出依赖本机Office；数值复算无需Office。

交付审阅完成不等于用户新G2批准，也不替代作者对投稿版本、作者信息及具体会议适配性的最终决定。
''')
print('Reports written')
