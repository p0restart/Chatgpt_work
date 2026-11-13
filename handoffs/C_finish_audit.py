"""Render the six requested audit deliverables from verified evidence notes."""
import json
import hashlib
from pathlib import Path
from C_build_deliverables import ROOT, OUT, papers, write, export_matrix_bib

search = r'''
# Work C｜检索日志

检索截止：**2026-11-07，Asia/Shanghai**。执行：单一审查会话，独立进行外部创新性核证；A/B仅作项目证据范围来源，不继承其创新判断。任务为定向反证查新，不冒称系统综述、数据库穷尽检索或人工双盲复核。C1→C2→C3已完成本轮交付，尚未取得的全文和元数据见末节。

## 1. 本地证据与当前状态

用户指定的11个必读文件全部找到：AGENTS.md、02_MODEL_SPEC.md、DECISIONS.md、04_EXPERIMENT_PROTOCOL.md、handoffs/A_inventory.md、handoffs/B_math_audit.md、reports/MATCHED_MECHANISM_PROTOCOL.md、reports/MATCHED_MECHANISM_RESULTS.md、reports/SUPPLEMENT_C2_PROTOCOL.md、reports/C2_EXECUTION_LOG.md、manuscript/04_method_zh.md。另读manuscript/03_model_zh.md、05_results_zh.md及paper/manuscript.md（引言/相关工作仍为占位）、reports/C2_FINDINGS.md、configs/proposed_mechanism_identification.yaml、reviews/APPROVAL_LOG.md。所读文件指纹另存C_evidence_manifest.json。

原始结果只读抽核：comparison_statistics.csv、finite/summary.csv、robust_effects.csv、equal_graph_symmetry.csv、capacity_summary.csv。没有重跑实验，也没有把报告核对称为完整独立复现。

发现比B报告更新的handoffs/C1_fix_report.md及c1_evidence/comparison.json：报告B1–B4已修复、53测试通过，单个正常六资产配置前后相同；本会话未重跑这些测试。故不再将B1–B4描述为当前必然未修复缺陷，也不据单例推广到全36配置。G2的现行记录为2026-11-03 APPROVED；旧模板/执行日志中的PENDING是历史文本。本任务不写审批记录，不代替新关卡。

## 2. 平台、工具与访问边界

实际使用联网检索工具的search_query/open/find/click；通过一般网络搜索定位官方论文、作者机构库和预印本，并按题名/DOI交叉核验。覆盖IEEE官方索引、Elsevier/ScienceDirect、Springer、arXiv、作者大学机构库、OUP；ACM相关条目经arXiv关联DOI核验。Google Scholar域限定检索已尝试，未得到可复核的原生Scholar结果，不声称完成Scholar数据库检索。ACM站内查询结果未提供可用的直接方法全文，不声称访问了ACM付费全文。

学术专用MCP搜索接口当前未挂载，改用现有网页检索。Crossref API经本地requests尝试失败（DNS解析失败），网页open也未成功，因此不声称已由Crossref批量核验。IEEE正文出现机器人验证，JAIR官网不可取；CityU的Bai全文链接返回403。Elsevier有页面可被搜索返回而直接open返回403；这类访问仅按实际可见内容判定。未使用私人账号、付费绕过或非授权下载。

书目真实性以论文首页、官方/作者机构记录为依据；一般聚合站只用于发现与交叉排错，不以其方法片段承担核心差异证明。P20的摘要信息另有可访问镜像，精确方法保留待全文核验。

## 3. 实际查询轨迹（按主题合并；不代表各平台原生高级搜索）

以下是实际执行的查询式；在联网工具search_query中逐条重放即可。未记录网页排名为稳定结果，也不报告无法重建的“共命中N条”。

|批次|实际查询式/打开对象|用途及筛选结果|
|---|---|---|
|Q01|"10.1016/j.comcom.2025.108148"；"10.1016/j.comnet.2023.109635"；"10.1016/j.cose.2023.103187"；"2601.16805"|核起始P01/P02/P03/P06；前3篇另读本地原文提取|
|Q02|"10.1063/5.0267934"；"10.1016/j.ress.2024.110740"；"10.1186/s42400-026-00577-4"；"10.1109/JIOT.2025.3541852"|P07–P10；题名/年份不直接照抄线索|
|Q03|"Preventive-Reactive Defense Tradeoffs" arxiv；"Optimal Resource Allocation for Network Protection" arxiv；"Stackelberg Security Games with Contagious Attacks" pdf；"Contagion effects of heterogeneous cyber risk"|找到P11及P06期刊更名记录|
|Q04|Preciado Zargham Enyioha Jadbabaie Pappas 2014 resource network protection arxiv 1309；Bai Letchford Vorobeychik Li 2023 contagious attacks reallocation rescue JAIR|后者查询包含探索性作者猜测，**没有作为引文采用**；作者以CityU实际记录更正|
|Q05|network protection security resource allocation spreading processes 2024 2025 differential game heterogeneous isolation recovery；"网络传播" "微分博弈" "资源" 防御|跨中英扩展；排除纯云计算资源编排及无攻防/传播的问题|
|Q06|"Stackelberg Security Games with Contagious Attacks on a Network" jair.org；"security" "source" "isolation" "differential game" malware|追溯再配置、源端控制；发现2026多防御者救援P12|
|Q07|site:arxiv.org "Stackelberg" "Reallocation to the Rescue"；site:arxiv.org "Network Security" "2014" Goyal Vigier；site:arxiv.org "Optimal control" "malware" "2014"；site:dl.acm.org "contagious" "security" "resource"|扩展基础工作；ACM原生方法访问不足如实保留|
|Q08|"Network security and contagion" Acemoglu 2016；"Optimal control of" malware "patching" 2014 2015；"Attack, Defence, and Contagion in Networks" Goyal Vigier doi|P14/P15/P16|
|Q09|site:arxiv.org "Optimal Patching in Clustered"；site:academic.oup.com "Network Security" "Vigier" 2014；site:scholar.google.com "asset value" "propagation" defense；site:dl.acm.org "security games" "contagious attacks"|找到P21投资政策；Scholar/ACM未形成可复核的数据库结果|
|Q10|"heterogeneous node value" "propagation" "defense" game；"attack-defense" "matched factorial" network|反证价值/传播错位与匹配实验首创；未找到精确相同四格不等于全球无先例|
|Q11|"A differential game method against attacks in heterogeneous honeynet" DOI；"Differential game approach for attack-defense strategy analysis in internet of things networks" DOI|P19/P20；P20卷期应为2022，DOI包含2021|
|Q12|"A Differential Game Method Against DDoS Attacks in IoT Botnets" "Zhang"；同题名authors；同题名"Guo" "Tao"|查询作者猜测经核验排除；最终Guo/Wang/Yu/Zhu/Tao|
|Q13|"Attack-defense game modeling framework" "Wu" "Guo"；同题名site:re.public.polimi.it|P08作者机构库核验|
|Q14|"Optimal Patching in Clustered Malware Epidemics" "10.1109"；"Preventive-Reactive Defense Tradeoffs" "10.1109"|年份/DOI交叉检查|
|Q15|open arxiv.org/abs/1707.07054、1512.05299、1401.5753、1403.1639；open arxiv.org/html/2601.16805v1及v2|版本/前后向引文扩展、去重|

## 4. 纳入、排除和追溯

纳入：2014–2026期间，对传播安全、价值/拓扑异质性、战略攻击、两类防御、资源约束或动态求解至少有一个直接方法关联，并可核实真实身份的研究。优先2024–2026而不排除2014基础。核心威胁要求比较状态方程和决策信息；只有摘要的论文不承担“它没有某机制”的强否定判断。

排除：仅检测分类准确率、纯计算任务卸载/云边激励而无相关安全传播问题、资料身份无法确认、搜索混入的推荐文章/引文被误当目标论文正文。多个版本合并为同一研究。未将早于2014的Aspnes等基础条目硬计入数量，可在后续需要时追溯。

追溯链：P06 v2 §§1/1.1及参考文献→P05、P15、P16；P12 §§1/2→P05及多防御者背景；P09相关工作/参考文献→P02/P03/P20；P01 §2及参考文献→Tian 2023单方云传播控制（后续待核）及控制基础；P04 arXiv相关结果→P13/P18。P11由主题反证检索新增，并本地正文核验。没有把引文列表本身当成引用论文全文。

## 5. 数量、可得性与未闭合项目

保留**21项独立研究**，9项有全文支持的方法级核验（P01/P02/P03/P04/P06/P07/P09/P11/P12），12项为仅摘要/预览级。全文级表示取得全文并针对本任务核验方法和实验段落，不表示对每行推导作独立数学证明。9项方法卡见主报告§3；各篇原文位置见CSV。P06的v1/v2/期刊合计1项。

必须继续保持的待核项：P05虽有公开PDF入口仍403；P08有OA入口但本轮未读PDF；P10/P20须读官方全文核对容量/时序和均衡概念；P19须核对两动作方程；P06期刊准确online日期待核，不能用December卷期推断11月7日尚无公开版本（v2已在10月5日可见）；P14和P18若最终采用期刊版需补该版元数据/全文。P20官方身份通过IEEE Communications Society目录及P09原文引文交叉确认，正文比较仍降级。

查无证据边界：本轮没有找到与“给定入口暴露、等/不等出强度×交换高价值位置、隔离恢复共享逐槽容量”的完整设置及同一交互估计完全一致的公开研究。**这是检索范围内的未发现，不是首创证明。**相反，广义“价值和网络位置共同决定资源配置”“联合保护恢复”“动态攻防传播”均有直接已有工作。
'''

audit = r'''
# Work C｜文献与创新性独立终审

审查日：2026-11-07。对象：第三章研究及其EI会议小论文。21项独立文献、9项全文方法级核验、12项仅摘要/预览级；起始10项均已定位，版本与访问限制见[C_search_log.md](C_search_log.md)，全量文献见[C_prior_art_matrix.csv](C_prior_art_matrix.csv)。编号Pxx对应唯一研究及BibTeX键，不是未经核验的引用占位。

## 1. 判决先行

**现有材料支持一篇范围明确的合成网络机制与收益边界论文；不支持“新微分博弈算法”“首次价值—传播错位建模”或“博弈防御普遍优越”的论文。**方法学原创性偏低，问题组合与匹配识别有有限增量，证据透明性较强，推广能力较弱。按本报告明确的保守定位，普通相关方向EI会议可作**有条件尝试、创新性风险中高**；这不是录用概率预测，更没有核验特定会议的EI收录。以算法/理论创新定位则**不建议提交**。不改变冻结模型可以重写成可信的小论文，但不能保证足够满足任何会议的创新门槛。

首选研究问题：**在上游受损暴露匹配、直接价值可与出向传播强度分离的网络中，改变高价值位置是否会因传播条件不同而改变隔离—恢复计划？在相同攻击响应评价规则下，联合动作、分时计划和针对战略攻击训练各自能带来多大额外收益？**

这里有三个必须分开的对象：q_i与Σ_kβ_ik的关系；g_i与q_i的关系；随状态/剩余时域变化的动态边际影响。原匹配干预主要改变第一个，攻击权重g仍均匀；它不是研究攻击者按q定向偏好的实验。出强度只是局部网络指标，不能与完整动态系统影响或中心性同义。

## 2. 当前项目事实、审批与证据层级

依据[02_MODEL_SPEC.md](../02_MODEL_SPEC.md)、[DECISIONS.md](../DECISIONS.md)、[APPROVAL_LOG.md](../reviews/APPROVAL_LOG.md)：非零和、有限时域、同时事前选择开环计划；K=6、n=6、T=10主要实例。x是实例组受损比例；a作用入口、s作用来源出边、r改变本地恢复率；容量每时刻/每槽约束，不是跨期总预算。PMP/KKT只给附条件必要性，求解采用直接射击和交替局部响应；后算攻击响应是评价方法，不把原博弈改成Stackelberg。

|证据层|真实覆盖|支持与不支持|
|---|---|---|
|原P3|3种子×3容量×3场景=27配置；六方法与fixed/adaptive评价|独立于匹配A/B/C/D；不能拼成63个同质重复样本|
|G1-C1|3种子×3容量×四格=36配置|价值位置效应与传播条件的交互；不是全部强基线优势检验|
|C2方法比较|匹配D格9配置＋原图反例1配置；八方法|强基线结论只覆盖D格9项；反例另列|
|C2小图|n=3,K=2；4张有限表，386397策略对|数值表内全偏离核验；不认证六节点连续域全局Nash|
|B审计及后续修复|B数学/数值边界；C1_fix_report报告B1–B4修复及单正常配置前后相同|本轮只读核对，无测试复跑；不把历史漏洞作为当前事实，也不把53测试变成均衡证明|

G2已于2026-11-03批准实际结果与边界，旧PENDING不能覆盖最新记录。本任务不改冻结文件、结果、源码或正式稿，不执行新实验。A/B审计用于约束证据强度；外部创新性裁决由本会话核证。

## 3. 九项全文方法级对照与五项最危险先例

以下每张方法卡覆盖问题、状态/控制、收益/资源、时序、算法、实验与差异；“作者声称”不等于本审查认证其定理。

### P01 Tian 2025：最接近非零和开环传播博弈

原文§§3–5、Eqs.(4),(15)–(18)、Algorithm 1；本地R1提取含PDF页标记。节点有U/I/C状态，攻击控制直接入侵和传播，防御控制直接防御与意识传播。收益/损失分别扣加各自成本，§4.3明确采用开环Nash；已足以否定“首次在云传播控制引入非零和开环博弈”。算法为状态前推、伴随后推与控制迭代，§6借用SNAP网络进行仿真，不是生产云实测。本项目与之的严格差异是单受损状态、抑制源出边与增加本地恢复的两种机制共享逐槽容量，及四格对照/强基线边界。**这些是特定建模和识别范围的区别，不自动构成算法创新。**未在核验模型中找到同一容量式，不把这一发现扩大到所有Tian相关研究。[原文DOI](https://doi.org/10.1016/j.comcom.2025.108148)

### P04 Preciado 2014：联合资源优化早期直接先例

§II-B Eq.(3)、§II-C与§III：调节点感染率β_i和恢复率δ_i，给定总成本预算优化谱衰减，使用几何规划；§IV为航空网络示例。它是单方静态率参数配置，不包含本项目的战略入口攻击、有限时域累计损失和分时动作。故**“两类资源共同配置”已做过**，区别必须落在目标、信息和控制位置上。目标入向防护与本项目源端隔离的方程差异见§4，不能将源端索引改动称为新理论。[作者公开稿](https://arxiv.org/pdf/1309.6270)

### P11 Paarporn–Xu 2024：联合防御与攻击竞争的最直接反证

原文§II Eqs.(1)–(8)、§III Theorem 1：有价值权重v_i，预防与恢复共享总资源X，攻击者预算Y；Tullock攻破概率后接指数恢复时间，节点间没有传播。物理过程两阶段，但恢复向量事前选择，防御不观察受损集合；战略式零和Nash。作者给解析均衡配置。本项目的传播、非零和、有限时域与逐槽容量不同，但**“博弈下联合保护恢复的有限资源取舍”不是新问题**；并且本项目理论保证更弱，不能以“采用数值优化”作优越性。[NSF公开稿](https://par.nsf.gov/servlets/purl/10574678)

### P06 Botteghi等2026：最危险的问题定位近邻

v1题名与用户线索一致；v2于2026-10-05更名，arXiv页关联Economic Modelling 165,107854及DOI。§2是易感子图连通风险，η和z为双方估值，成本加权；§2.3是防御先承诺的SSE，§3含网络保护指标/近似及附条件定理。§4改变拓扑和价值分布，§4.3再用SIS等动态过程检验。**双方估值不同与本项目q—出强度错位不是同一变量关系，但其工作已经涉及价值与网络位置共同塑造资源配置，甚至固定图改变价值位置；不能用变量概念不同把它排除为无关。**严格剩余差异是本项目同时开环、两动作时变竞争、源端控制和可解释的四格交互。它的动态验证并非本项目逐槽两动作联合优化，所以也不应反过来判为完全重复。[v2全文](https://arxiv.org/html/2601.16805v2)

### P07 Chen等2025：取舍与条件性发现的直接先例

正文§II Eqs.(1)–(6)、§III：按度设成本，保护/恢复拆分同一总资源，节点移除/重连后计算负载级联与鲁棒性；随机攻击、按度防御顺序。不同资源量和冗余下最优比例非单调已有。它不是受损比例ODE，也不是双方同时开环均衡；本项目只能贡献特定传播动力学下的交互与收益边界。**“效果随预算改变”本身不足以成为新机制发现。**原PDF封面为第1页，正文页码需与PDF页分开。[DOI](https://doi.org/10.1063/5.0267934)

### P02 Zhang等2023 Computer Networks

本地R2，原PDFpp.3–5状态/收益、§3.2算法、§4实验。按度分组S/I/R/D，攻击投入在感染/破坏间作用，防御投入修复；含状态效益与行动成本、资源强度上下界。前向状态、后向伴随扫描求控制，比较无标度网络。原文鞍点术语不替代对其零和性的逐式核查。与本项目区别：度分组与节点图控制不同；其度异质不能替代固定暴露交换业务价值的识别。**动态策略和异质网络无独立创新空间。**[DOI](https://doi.org/10.1016/j.comnet.2023.109635)

### P03 Zhang等2023 Computers & Security

本地R5，p.3 Eq.(1)：SIRS，β_i S_i Σ_j b_ij I_j−γ_i I_i；收益Eq.(2)–(3)含节点r_i/s_i及成本。采用势微分博弈、Hamiltonian与迭代，在小世界/无标度网络仿真。节点收益已可异质；不能把“加入q_i”作首创。该文β_i作用于接收端的感染率，本项目s_j作用于来源j出边，导数结构不同；同时，本项目没有证明势结构或全局最优。[出版社](https://www.sciencedirect.com/science/article/pii/S0167404823000974)

### P09 Lou等2026

出版社模型Eq.(1)–(12)是N/I/S/C汇总状态与竞争强度；Eq.(13)–(17)作策略信念更新；收益Eq.(22)–(23)、Hamiltonian算法，实验报告Mininet校准及CICIoT2023。它解决的信息设定与本项目已知模型开环不同，不能将其“异质节点”直接当成本项目价值错位；也不能借其部署/数据验证证明本项目。本审查只确定方法先例，不认证其贝叶斯与均衡证明的正确性。[全文](https://link.springer.com/article/10.1186/s42400-026-00577-4)

### P12 Cui等2026：起始清单外的最新危险邻居

§3.1–3.3：多防御者预算和估值、攻击选点、事前公布规则下按目标转移盈余救援；含转移边容量和捐赠者安全约束，Eqs.(14)–(19)定义继续阶段损失和SNE，MILP仅作集中基准，贪心/区域搜索输出启发式候选并注明不作全局认证。§4报告三模拟三真实网络。它是观察目标后的资源救援，不是预先指定时间的隔离—恢复率控制；但**传播、价值、动态救援与资源约束的组合已存在**，本项目不能凭组合词声称填补领域空白。[全文](https://link.springer.com/article/10.1007/s44443-026-01181-9)

五个应优先正面回应的先例为P01、P04、P11、P06、P07；P12是第六项最新风险。P05仅摘要已足以确认传播与再配置先例，但不足以逐式排除完全相同机制；P19的捕获/补丁也要求保留全文缺口，不能因未读而“判无”。

## 4. 关键数学差异与匹配设计到底识别什么

以接收端在行的矩阵W_ij=β_ji记传播。冻结模型传播项为diag(1−x) W diag(1−εs)x；常见接收端防护是diag(1−x)diag(1−εv)Wx。对来源j的s_j，

$$\frac{\partial f_i}{\partial s_j}=-(1-x_i)\beta_{ji}\varepsilon_jx_j\quad(i\ne j),\qquad \frac{\partial f_j}{\partial s_j}=0,$$

而目标端v_j只直接改变第j个状态方程的感染输入；恢复有∂f_i/∂r_j=−γ_jx_j·1_{i=j}。例：仅j→k有边且x_j>0、x_k<1，源端s_j立刻降低f_k，目标端v_j不能抑制这条出边。故通常不是改名。但不要声称任何目标式都无法等效：若控制同质、图特殊，矩阵可交换；仅比较线性谱且恢复是同一标量时，WD与DW还可能同谱。**不同作用方向是有意义的模型细节，不是源端隔离概念首次出现的证据。**P04 Eq.(3)、P03 Eq.(1)提供可复核接收端对照；P19全文不足，不判其无源端机制。

边际隔离收益M_j^s=ε_jx_jΣ_kβ_jk(1−x_k)p_k^D；恢复M_j^r=γ_jx_jp_j^D。隔离面向下游未来损失，恢复直接作用本地且通过后续状态间接降低传播。q经伴随进入二者，因此“隔离只看传播，恢复只看价值”是错的。非零控制时应再扣c^s_js_j/c^r_jr_j及h；受容量/上下界约束，不能从式子直接得到全局排序。零终端权重和T=10使末期收益解释有条件。

四格为equal/high2、equal/high3、unequal/high2、unequal/high3。equal两节点到4/5各0.08；unequal分别各0.12/0.04；交换q=4的位置，其他q=1，h固定0.05；各源上游暴露匹配、总出边权不变。严格说“固定拓扑”指边存在关系固定；**四格之间并非传播矩阵完全相同**，等/不等条件改变边权。估计量(D−C)−(B−A)测价值位置效应是否依赖传播条件。A/B镜像可作求解/模型对称性对照；C/D不是镜像。

这超过无控制的随意参数扫描，因它主动控制上游暴露并构造交互；但仍是合成模型内的匹配因子敏感性设计，没有现实随机试验或总体因果效应。每格允许攻击计划随局部博弈解变化，交互包含响应渠道，不能称“固定攻击下纯防御动作因果效应”。若只给四条轨迹，解释价值有限；需同时报告交互、原始控制和容量绑定。全网恢复竞争不等于节点2/3隔离显著竞争：B=0.6时s2/s3近零，不能写核心源节点普遍发生隔离—恢复切换。

## 5. 候选贡献A–F逐项裁决

证据等级：L0=构想；L1=定义/解析差异；L2=指定合成实例数值与诊断；L3=多拓扑/参数稳健外推；L4=真实校准/实证。本项目主要L1–L2；这些是审查分类，不是统计置信度。

|项|直接先例及位置|严格剩余区别/创新类型|本项目等级|可否独立主张|风险|最小补证或处理|
|---|---|---|---|---|---|---|
|A连续状态传播|P04 §II-B Eq.(3)；P03 Eq.(1)；P01 §3|实例组受损比例的具体解释；模型应用|L1+L2|否，作为背景和统一模型|高|明确状态语义并引用，不能首次|
|B非零和开环含攻击隔离恢复|P01 §4.3；P19摘要含攻击/捕获/补丁；P11 §II双防御竞赛|源出边隔离＋本地恢复＋入口攻击的具体组合；模型/问题|L1+L2|可描述研究设置，不能单独称重大创新|高|取得P19/P10/P20全文关闭控制位置近邻风险；只提出，不改模型|
|C按节点按槽共享容量联合分配|P04 §II-C联合预算；P11 Eq.(1)总资源两用途；P12预算与救援|逐槽容量与有限时域计划区别；建模/数值实现|L1+L2|与D/F合用；不称新算法|高|解释瞬时容量而非总预算，保留松弛；若主张时间离散收敛才需K加密|
|D价值位置×出强度四格|P06 §4.1/4.2固定图价值分布；P02度异质|匹配入口暴露、交换q且固定总出强度的交互识别；实验设计/限定机制|L2|**可作首要实质贡献**，不称四格方法首创|中高|用已有robust_effects/容量/镜像证据并列；精确相同先例本轮未发现，不宣称无|
|E统一攻击响应下强基线|P01 §6；P05摘要；P12 §4均有方法比较|拆开联合动作、时间变化、训练攻击假设；实验诊断|L2，仅D格9配置|可以作为支撑贡献；非新评价理论|中|已有C2足够报告范围；不把自身启发式称为完整复现文献算法|
|F条件效果及反例|P07 §III/结论；P13摘要反例；P19摘要时域依赖|特定配置交互的条件性、战略训练增量小、同一规则下负反例；数值发现|L2|与D/E合用可主张；普遍条件性已做过|中|报所有零效应/反向与负值；不能声称跨T稳健，因为T未变|

“时间窗差异”只是在同一T=10内分段报告，并非T敏感性实验；“容量大时松弛”也意味着不能继续解释为紧约束资源争夺。共同预算上限并不等于实际耗用相等；启发式与优化方法比较还混入是否允许少用资源的差异。

## 6. 审稿人攻击测试

|最有杀伤力的问题|有证据的回答/承认|状态|
|---|---|---|
|1. 2014已有预防/恢复，为什么再做？|承认P04已解决静态联合率配置；只研究源端隔离/恢复在有限时域战略入口攻击下的匹配交互，不重宣联合配置发明|现有材料可答；原创增量仍有限|
|2. 2023–2025已有传播微分博弈，模型有何必要？|P01甚至已有非零和开环；新模型只提供独立动作机制与共享容量的可解释实验工具，价值取决于D/E/F发现|现有材料可答；不能答新理论算法|
|3. 2026价值异质传播配置是否重复？|P06已研究价值/拓扑；估值双方差异不是同一轴但有明显交集。精确不同在时变两动作、同时开环和匹配交互；没有查新首创证书|现有材料可答限定差异；广义首次不能答|
|4. 六节点三种子足以泛化？|只覆盖同构造族三组入口权；非三份独立现实网络，未提供概率抽样或显著性证据|广泛推广不能答；限定实例可答|
|5. 强基线不足1%及反例怎样处理？|针对各自局部响应，Fixed-trained增益0.029%–0.286%，均低于1%描述门槛；原反例联合12.437518高于仅恢复12.436854；不写普遍优势|现有材料可答|
|6. 没有全局Nash与K加密，还叫博弈方法？|博弈是研究模型；输出称局部响应候选。H精化不代表K加密；有限表是另一有限游戏|现有材料可答定义；连续收敛不能答|
|7. 你是不是只比弱启发式？|C2有仅恢复、静态联合、固定攻击优化，但仅D格9项；并未复现P01/P06等外部算法|现有材料可答；领先现有文献不能答|
|8. DID算不算现实因果发现？|是受控模型内参数交互；攻击可随格变化，不能宣称现实识别或固定攻击纯效应|现有材料可答|
|9. 反例是否证明联合可行域更大仍更差？|固定同一a且全局优化时可行域嵌套保证联合不劣；这里对手a变化且仅局部解，故反例是评价协议下结果，不违反嵌套定理，也不证明联合动作本质有害|现有材料可答；归因局部误差/战略响应的大小仍不能答|
|10. 源隔离只是把索引换一下？|§4导数与单边例证明确干预对象不同；但未证明该对象新颖，不能升格创新定理|现有材料可答数学区别；先例穷尽不能答|
|11. B审计缺陷是否使结果无效？|更晚C1报告修复及单例正常结果一致；并无证据证明历史数据因此错误，本轮也未全量复跑|现有材料可答有限状态；全量修复后复现需小规模/分层补核计划|

## 7. 结果能支撑到哪里

直接读取results/supplement_c2/run02/comparison_statistics.csv：在D格9项各自局部攻击响应下，联合相对仅恢复损失降低0.887%–4.796%，相对静态联合0.661%–2.190%，相对Fixed-trained仅0.029%–0.286%。公共固定攻击下，相对Fixed-trained为−0.094%至−0.017%，9项均不占优。**由此应分开报告联合动作收益、分时计划收益和针对战略响应训练的增量，不用启发式大差距掩盖后者很小。**1%是登记描述阈值，不是显著性、现实经济意义或理论误差界。

36配置的robust_effects及capacity_summary支持低容量前四槽恢复交互的指定方向；中容量出现时段/种子依赖，高容量多数槽松弛；s2/s3低容量接近零。equal_graph_symmetry可检查A/B镜像；这些都不是普适“先隔离再恢复”时序定理。有限表4张各一个数值纯均衡，仅用于核验菜单内偏离。失败run01保留，成功run02不是两次独立成功。

复现命令与原证据入口见下一文件[结论—证据映射](C_claim_evidence_map.md)。本次只核对保存材料，不冒称执行那些重现命令。

## 8. 保守、中等、激进三种定位

|定位|题名/主线|取舍与判定|
|---|---|---|
|**保守（首选）**|《攻防交互下异质传播网络的隔离与恢复配置：匹配对照与收益边界》|D为主，E/F支撑；明确合成实例和局部候选。可信但创新有限，EI尝试风险中高|
|中等|《资产价值与出向传播强度错位下的动态防御配置机制》|可用，但需始终限制为指定模型交互；“机制”不能承诺一般规律。与P06/P07竞争更直接|
|激进（否决）|《面向云安全的全局最优微分博弈联合防御算法》|算法理论和真实云证据缺失，且已有强先例；无法靠润色修复|

现有paper/manuscript.md工作题名已基本符合保守方向；建议增加“匹配对照”而非强行重命名整个硕士论文。硕士论文总题名与第三章子题可分层处理，本次不替用户更改任何正式题名。

## 9. 最小缺口、行动边界与终审摘要

**无需改模型即可做的必要修订**：正面引P01/P04/P11/P06/P07；将D的匹配条件写清；将C2三类收益分列，加入公共固定攻击下Fixed-trained的反向比较；区分时间窗与时域敏感性；撤回所有新算法、连续Nash、普遍领先和现实云有效性标签。这些已在交付草稿中落实。

**未闭合的最小文献缺口**：P05/P19及P10/P20控制位置/预算原式，需合法全文才能关闭近乎同机制风险。P08有合法OA入口但本轮尚未完成正文核验。它们不阻止保守地写“采用某模型分析”，但阻止写“现有工作没有该结构”。

**若目标会议要求方法创新或广泛机制证据，当前材料仍不足**。最小证据方案应先是一个保持冻结模型不变的独立拓扑或预登记反转条件测试，检验D是否超出这一特定构图；如果主张连续时间可迁移性则另需K加密，主张部署有效性则需参数校准/真实环境。它们是备选变更提案，**本任务不执行、不视为已获G1/G2批准，也不为追求正结果扩展实验**。即使补一个拓扑也不自动变成普遍机制或算法创新。预算、q、h与传播率的系统敏感性尚缺，不把窗口比较充当这些检验。

综合裁决：A/C的大类已做过；B为已有思想的特定组合，独立原创性不足；D为本项目最可辩护的实验识别增量；E为必要的分层评价贡献；F的具体小收益/反例值得报告，但一般条件性并非新发现。**可写可信的小论文，宜以可解释对照和收益边界取胜；是否足以录用取决于会场对有限数值机制研究的接受度。**尚未查到完全相同先例不转化为全球首次。
'''

claim = r'''
# Work C｜结论—证据映射

2026-11-07。允许表述可用于后续写作；本文件不改正式稿。Pxx及BibTeX键见[C_prior_art_matrix.csv](C_prior_art_matrix.csv)。下列重现命令是项目已有入口，**本会话未执行优化复跑**。

|拟写点/结果|具体项目证据|外部近邻|精确允许表述|禁止表述|
|---|---|---|---|---|
|状态和两控制机制|[模型§§1–3](../02_MODEL_SPEC.md)、[现稿§3](../manuscript/03_model_zh.md)|P04 Preciado2014Protection Eq.(3)；P03 Zhang2023Potential Eq.(1)|采用源端出向传播抑制和本地恢复两类动作，描述实例组受损比例|单台服务器受攻击概率；首次连续传播模型|
|非零和开环计划|[规格§4](../02_MODEL_SPEC.md)、[方法§§4.1–4.3](../manuscript/04_method_zh.md)|P01 Tian2025Cloud §4.3；P11 Paarporn2024Tradeoffs §II|在有限时域非零和博弈中求分段常值开环局部响应候选|首个云非零和开环博弈；实时反馈Nash|
|容量定义|[模型§3](../02_MODEL_SPEC.md)、[匹配配置](../configs/proposed_mechanism_identification.yaml)|P04/P11（其总预算不同）|隔离与恢复共享逐槽容量上限，优化允许留有余量|跨期总预算；各方法实际消耗相同|
|匹配四格设计|[协议](../reports/MATCHED_MECHANISM_PROTOCOL.md)、[配置](../configs/proposed_mechanism_identification.yaml)、[对称检查](../results/matched_mechanism/run01/equal_graph_symmetry.csv)|P06 Botteghi2026Contagion §4.1/4.2|在边连接关系和上游暴露匹配条件下，交叉改变出强度条件与高价值位置，检验模型内配置交互|传播矩阵四格完全相同；随机现实因果试验；四格设计首创|
|交互条件性|[全部稳健效应](../results/matched_mechanism/run01/robust_effects.csv)、[逐槽效应](../results/matched_mechanism/run01/slotwise_effects.csv)、[容量](../results/matched_mechanism/run01/capacity_summary.csv)、[机制报告](../reports/MATCHED_MECHANISM_RESULTS.md)|P07 Chen2025ProtectRecover；P19 Ren2020Honeynet|所检交互依赖容量、入口边权和报告时间窗；低容量前四槽恢复交互较一致，中容量不一致、高容量多松弛|任意网络普适规律；一般时间优先级切换；已经验证T变化|
|局部隔离不活跃|[源投入](../results/matched_mechanism/run01/source_allocations.csv)、同根各case/fine_evaluation/controls.csv|P04/P11（动作作用不同）|低容量时节点2/3隔离近零，恢复交互需结合全网控制解释|两比较节点始终出现显著隔离恢复竞争|
|联合相对仅恢复|[C2统计](../results/supplement_c2/run02/comparison_statistics.csv)、[逐项配对](../results/supplement_c2/run02/paired.csv)|P11/P07；非其算法复现|匹配D格九配置、各自局部攻击响应下损失降低0.887%–4.796%|全部36格均胜；对现有文献算法普遍领先|
|分时相对静态|同上，baseline=Joint-static|P01/P10动态策略先例|同九配置降低0.661%–2.190%，仅六项达到1%描述门槛|动态方法显著更优；静态攻击/防御概念混同|
|针对战略攻击训练增量|同上，baseline=Fixed-trained；[预登记](../reports/SUPPLEMENT_C2_PROTOCOL.md)|P01/P06战略模型|各自响应评价下额外降低0.029%–0.286%，九项均低于预设1%描述门槛|博弈较优化具有显著收益；小gap证明方法优势|
|公共固定攻击比较|同表evaluation=common_fixed_attack；[方法和范围](../reports/SUPPLEMENT_C2_PROTOCOL.md)|P01/P06（时序不同）|冻结最终防御后，在公共固定攻击下联合相对Fixed-trained为−0.094%至−0.017%；训练假设与评价攻击必须分开|把重新训练后的比较当作同一防御策略受攻击变化|
|原负反例|[同精度反例](../results/equilibrium_audit/counterexample01/comparison.json)、[C2报告§3](../reports/C2_FINDINGS.md)、C2 comparison中原图case|P13 Zargham2014WorstCase（不同反例命题）|原图seed33/business_cost/B0.6，联合12.437518高于仅恢复12.436854，负值保留且另列|联合控制对任意配置不劣；反例证明联合可行域更大仍固定对手全局更差|
|有限表稳定性|[四表汇总](../results/supplement_c2/run02/finite/summary.csv)、[方法§4.4](../manuscript/04_method_zh.md)、[B审计](B_math_audit.md)|P11理论均衡不可迁移|386397个策略对构成的四个数值表各识别一个容差内纯均衡，仅限明确菜单|连续动作唯一Nash；六节点全局证明；积分容差是严格误差界|
|数值验证与当前修复|[B审计](B_math_audit.md)、[C1修复](C1_fix_report.md)、[修复对比](c1_evidence/comparison.json)|P12也区分启发式和全局认证|有多初值/积分精化/局部偏离证据；C1报告接口修复及单例前后相同|本轮独立跑53测试；53测试证明全局收敛；B缺陷必使历史结果无效|
|适用范围|[实验协议](../04_EXPERIMENT_PROTOCOL.md)、[库存](A_inventory.md)、[现稿讨论](../manuscript/05_results_zh.md)|P06/P12有更广拓扑；不能借为自身验证|合成六资产网络族，三种子重现入口权，T=10、K=6、零终端权重|生产云实测；三独立现实样本；统计显著；一般规模可扩展|

## 复核与复现入口

只读核对：`python handoffs/C_verify_deliverables.py`，检查文献计数、交付文件、引用键、项目路径、文件指纹和相关工作正文长度。它不运行新实验。

原匹配实验的全量重现（须新目录；此处仅记录，不执行）：

```powershell
python -m src.matched_mechanism --output results/matched_mechanism/reproduce_C_review
python -m src.resume_matched --root results/matched_mechanism/reproduce_C_review
python -m src.audit_matched --root results/matched_mechanism/reproduce_C_review
```

`resume_matched`仅在程序按四格边界时间停止且允许续接时使用，不作失败重试。报告重建入口见原reports/MATCHED_MECHANISM_RESULTS.md。

C2既有协议的重现：

```powershell
python -m src.supplement_c2 --output results/supplement_c2/reproduce_C_review
python -m src.report_c2 --root results/supplement_c2/reproduce_C_review --report reports/C2_REPRODUCED_C_REVIEW.md
```

这些命令说明原研究的可重现来源，不是本次执行声明，也不是新实验范围授权。修复后环境及输入来源需重新记录；不能覆盖run01/run02。文献检索则按C_search_log查询表及CSV原文URL/位置重放；网页可得性与排序可能变化。
'''

related = r'''
# Work C｜相关工作与贡献声明草稿

2026-11-07。以下正文约800–1200汉字；[@键]对应[C_bibliography.bib](C_bibliography.bib)，Pxx与访问等级见[C_prior_art_matrix.csv](C_prior_art_matrix.csv)。全文未读的条目仅承担摘要能确认的事实；本段不据摘要断言其缺少某控制。正文之外的定位/贡献/局限单列，不计入正文长度。

## 相关工作正文

网络传播控制中的资源配置已有明确基础。Preciado等在有向异质网络上联合调节感染率和恢复率，以成本约束优化传播衰减，并用几何规划求解[P04，@Preciado2014Protection]。因此，预防与恢复的联合投入本身不能构成本文的创新。Paarporn和Xu进一步将两类防御纳入资源竞争博弈，刻画有限预算下的均衡配置；其目标间相互独立，预防影响攻破概率，恢复缩短受损时长[P11，@Paarporn2024Tradeoffs]。Chen等则研究节点保护、恢复与负载级联，表明配置取舍随资源和网络冗余改变[P07，@Chen2025ProtectRecover]。这些工作为两类动作的收益比较提供了直接参照。

传播攻防的动态建模同样已有丰富先例。Zhang等分别针对无标度网络和复杂网络建立传播微分博弈，将感染、破坏或修复行为与动态收益联系起来[P02/P03，@Zhang2023ScaleFree；@Zhang2023Potential]。Tian等面向云恶意软件传播构造非零和开环攻防问题，并通过状态、伴随和控制迭代求解[P01，@Tian2025Cloud]。本文因此不将开环博弈、连续传播状态或常用数值求解器作为独立贡献，而关注源端传播抑制与本地恢复在共同容量约束下如何分配。

节点价值与网络传播位置的关系是另一条重要线索。Botteghi等将双方节点估值和传播风险结合，在Stackelberg框架下分析资源配置，并比较不同价值分布与拓扑；新版还检验了不同传播动力学[P06，@Botteghi2026Contagion]。双方对资产估值不同，与业务价值和出向传播强度不同并非同一问题，但二者都说明价值排序不能代替网络风险分析。Bai等研究传播攻击后的邻域资源再分配，Cui等进一步纳入多防御者和目标条件救援[P05/P12，@Bai2023Reallocation；@Cui2026Rescue]。这些顺序决策中的资源转移，与本文预先制定的分时隔离、恢复计划具有不同信息条件和动作含义。

在上述基础上，本文将比较重点放在匹配干预与收益分解。通过匹配两个节点的上游暴露，交叉改变其出强度条件与高价值位置，检验价值位置效应是否依赖传播条件；同时分别比较联合与单一动作、动态与静态计划以及不同训练攻击假设。既有强基线比较表明，在所检匹配配置中，针对战略攻击训练的额外收益低于预设描述门槛，原网络中也保留联合方案略逊于仅恢复的反例[本项目E1–E3，见结论映射]。本文据此讨论指定合成网络中的配置交互和收益边界，避免以较弱启发式上的优势替代对博弈增量的检验。

## 三条贡献声明（首选）

1. 在既定有限时域传播攻防模型中，构造上游暴露匹配的价值位置与出向传播强度四格对照，量化隔离、恢复计划对两类因素的交互响应。证据：36配置及robust_effects/capacity_summary；对应审计D。
2. 在匹配D格九配置中，采用统一的局部攻击响应评价规则，分别比较联合动作、分时计划与固定攻击训练，区分三种收益来源。证据：C2 comparison_statistics/paired；对应E。
3. 完整报告交互随容量和时间窗变化的条件性，以及强基线小收益与原图负反例，明确合成网络、局部求解和既定控制槽数下的适用边界。证据：匹配全表、C2及反例；对应F。

## 研究缺口定位

已有研究覆盖联合预防恢复、传播微分博弈及价值异质的战略配置。本文研究一个更窄、可用匹配对照检验的问题：在入口暴露可比的条件下，价值位置改变对恢复和源端隔离计划的影响，是否随出向传播强度条件而变化；并通过强基线分解其配置收益与针对战略攻击训练的增量。这个缺口是本轮已核文献与现有实验之间的具体比较位置，不代表此前没有研究价值与网络位置的关系，也不构成全球首次声明。

## 局限性

研究基于六资产合成网络族、三组入口权和固定T=10、K=6设置，尚未进行真实云参数校准、控制槽加密或跨网络族稳健性验证。数值输出为交替局部响应候选；小规模有限表只认证明确菜单内的数值稳定性。强基线比较覆盖匹配D格九配置，不能推广至全部四格或所有网络；1%为描述阈值，不是统计显著性。因双方目标非零和且响应攻击可变，联合动作可行域包含单一动作也不保证各自响应评价下处处更优。

## 项目证据编号

- E1：[匹配交互](../results/matched_mechanism/run01/robust_effects.csv)及[容量使用](../results/matched_mechanism/run01/capacity_summary.csv)。
- E2：[C2方法统计](../results/supplement_c2/run02/comparison_statistics.csv)。
- E3：[原反例](../results/equilibrium_audit/counterexample01/comparison.json)及[C2报告§3](../reports/C2_FINDINGS.md)。
'''

targets=['C_search_log.md','C_prior_art_matrix.csv','C_literature_novelty_audit.md','C_claim_evidence_map.md','C_bibliography.bib','C_related_work_draft.md']
for name in targets:
    if (OUT/name).exists():raise FileExistsError(name)
write(targets[0],search)
bib=export_matrix_bib()
write(targets[2],audit)
write(targets[3],claim)
write(targets[4],bib)
write(targets[5],related)

inputs=[
 'AGENTS.md','02_MODEL_SPEC.md','DECISIONS.md','04_EXPERIMENT_PROTOCOL.md','handoffs/A_inventory.md','handoffs/B_math_audit.md',
 'reports/MATCHED_MECHANISM_PROTOCOL.md','reports/MATCHED_MECHANISM_RESULTS.md','reports/SUPPLEMENT_C2_PROTOCOL.md','reports/C2_EXECUTION_LOG.md',
 'manuscript/04_method_zh.md','manuscript/03_model_zh.md','manuscript/05_results_zh.md','paper/manuscript.md','reviews/APPROVAL_LOG.md',
 'reports/C2_FINDINGS.md','configs/proposed_mechanism_identification.yaml','handoffs/C1_fix_report.md','handoffs/c1_evidence/comparison.json',
 'results/supplement_c2/run02/comparison_statistics.csv','results/supplement_c2/run02/finite/summary.csv',
 'results/matched_mechanism/run01/robust_effects.csv','results/matched_mechanism/run01/equal_graph_symmetry.csv','results/matched_mechanism/run01/capacity_summary.csv']
inputs += [f'literature/fulltext_audit/R{i}_extracted.txt' for i in range(1,6)]
manifest={'review_date':'2026-11-07','scope':'read-only project and literature review; no experimental rerun',
 'records':len(papers),'fulltext_method_checked':9,'abstract_preview_only':12,
 'inputs':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in inputs],
 'outputs':[{'path':'handoffs/'+p,'sha256':hashlib.sha256((OUT/p).read_bytes()).hexdigest()} for p in targets]}
write('C_evidence_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'created':targets,'papers':len(papers),'fulltext':9,'abstract_preview':12},ensure_ascii=False))
