"""Build the independent literature audit artifacts; no model or experiment writes."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'handoffs'
DATE = '2026-11-07'
papers = []

def add(pid, key, author, year, title, venue, doi, url, access, locator, model, timing, payoff, algorithm, experiment, difference, threat, cite, note='', **bib):
    papers.append(dict(id=pid, bibkey=key, authors=author, year=year, title=title, source=venue, doi=doi, url=url,
        access=access, evidence_locator=locator, control_propagation_model=model, game_timing=timing,
        payoff_budget=payoff, algorithm=algorithm, experiment_type=experiment,
        similarity_and_strict_difference=difference, novelty_threat=threat, recommended_citation=cite,
        evidence_boundary='原文直接陈述：模型/时序/算法/实验各列；审查员推断：差异/威胁/引用位置各列。未核验部分明确留空或标未知。',
        verification_notes=note, bib_extra=bib))

F='全文方法级核验'
A='仅摘要可核验'
add('P01','Tian2025Cloud','Liang Tian and Chenquan Gan and Jiabin Lin and Fengjun Shang and Qingyi Zhu',2025,
 'Analysis of attack-defense game for advanced malware propagation control in cloud','Computer Communications','10.1016/j.comcom.2025.108148','https://doi.org/10.1016/j.comcom.2025.108148',F,
 'literature/fulltext_audit/R1_extracted.txt；原PDF pp.3–7 §§3–5，Eqs.(4),(15)–(18)，Algorithm 1；p.8 Table 2',
 'U/I/C节点状态；直接攻击与感染传播，直接防御与意识传播控制；并非本项目单一x加源隔离结构',
 '有限时域开环Nash定义；双方目标分列，不能归为纯零和',
 '感染收益/损失与各自行动成本；控制区间；未在核验公式中见本项目共享逐时刻隔离恢复容量式',
 '状态前推、伴随后推、控制更新的Forward–Backward Euler',
 'SNAP YouTube/Facebook/Twitter拓扑仿真；不是云平台攻击实测',
 '直接威胁非零和开环云传播博弈新颖性；本项目增量在源隔离/恢复共享容量及匹配交互与强基线边界',
 '高：最接近博弈与应用框架','相关工作传播博弈段；不能声称首次非零和开环云博弈',volume='237',pages='108148')
add('P02','Zhang2023ScaleFree','Hengwei Zhang and Yan Mi and Xiaohu Liu and Yuchen Zhang and Jindong Wang and Jinglei Tan',2023,
 'A differential game approach for real-time security defense decision in scale-free networks','Computer Networks','10.1016/j.comnet.2023.109635','https://doi.org/10.1016/j.comnet.2023.109635',F,
 'literature/fulltext_audit/R2_extracted.txt；原PDF pp.3–5状态与收益，§3.2算法，§4仿真',
 '按度分组S/I/R/D；攻击感染/破坏，防御修复；度异质性',
 '有限时域微分博弈；原文使用saddle-point术语；本审查不据术语自行认证零和或反馈均衡',
 '状态效益和行动成本；资源强度上下界；未核验出相同跨节点两动作逐槽共享容量',
 'Hamiltonian/伴随必要条件与迭代决策',
 '无标度网络及比较仿真',
 '度与修复差异早已有之；不同于固定上游暴露下独立交换q并比较出向传播条件',
 '高：动态网络防御/度异质性非新','传播微分博弈段',volume='224',pages='109635')
add('P03','Zhang2023Potential','Hengwei Zhang and Yan Mi and Yumeng Fu and Xiaohu Liu and Yuchen Zhang and Jindong Wang and Jinglei Tan',2023,
 'Security defense decision method based on potential differential game for complex networks','Computers & Security','10.1016/j.cose.2023.103187','https://www.sciencedirect.com/science/article/pii/S0167404823000974',F,
 'literature/fulltext_audit/R5_extracted.txt；原PDF p.3 Eq.(1)–(3)，pp.4–6 §3，§4仿真',
 '节点级SIRS；感染率β_i作用于目标i入向感染，γ_i修复',
 '势微分博弈；原文称鞍点；其全局表述不移植到本项目',
 'J_A含感染收益和感染成本；J_D含修复收益、感染损失和修复成本',
 '势结构、Hamiltonian/伴随与迭代',
 '小世界与无标度网络仿真',
 '节点传播状态和异质收益已有先例；本项目源端隔离导数跨下游，且不宣称势结构或全局算法',
 '高：A/B背景与异质价值先例','传播模型及求解背景',volume='129',pages='103187')
add('P04','Preciado2014Protection','Victor M. Preciado and Michael Zargham and Chinwendu Enyioha and Ali Jadbabaie and George J. Pappas',2014,
 'Optimal Resource Allocation for Network Protection Against Spreading Processes','IEEE Transactions on Control of Network Systems','10.1109/TCNS.2014.2310911','https://arxiv.org/pdf/1309.6270',F,
 '作者公开期刊PDF https://www.georgejpappas.org/wp-content/uploads/2024/04/06763066.pdf；arXiv:1309.6270v2 §II-B Eq.(3)，§II-C，§III，§IV',
 '有向异质SIS；(1-p_i)β_i Σ_j a_ij p_j−δ_i p_i；调感染率与恢复率',
 '单方静态参数优化，非战略攻击者博弈',
 '预防与纠正成本共享给定预算；最大灭绝速率/最小控制预算',
 '几何规划及谱稳定条件',
 '航空运输网络仿真',
 '已覆盖预防恢复联合预算优化；不同于有限时域累计损失、源端隔离、入口战略攻击和逐槽计划',
 '高：直接否定联合预防恢复首创','联合资源配置段',volume='1',number='1',pages='99--108')
add('P05','Bai2023Reallocation','Rufan Bai and Haoxing Lin and Xinyu Yang and Xiaowei Wu and Minming Li and Weijia Jia',2023,
 'Stackelberg Security Games with Contagious Attacks on a Network: Reallocation to the Rescue','Journal of Artificial Intelligence Research','10.1613/JAIR.1.14563','https://scholars.cityu.edu.hk/en/publications/stackelberg-security-games-with-contagious-attacks-on-a-network-r/',A,
 'CityU作者机构记录Abstract和书目信息；公开PDF链接返回403，未取得正文',
 '节点攻击扩散至邻居；防御资源向邻居转移会削弱来源防御',
 'Stackelberg；细节仅据题名及摘要，不假装逐式核验',
 '节点防御与再分配，损失最小化；预算精确公式未核验',
 '摘要报告NP-hard、MILP及双准则近似',
 '摘要报告数值比较；规模细节未核验',
 '资源跨节点移动不是抑制感染源出边；不能用动态一词宣称本项目领先',
 '高：传播与资源再配置已有','传播安全博弈段',volume='77',pages='487--515')
add('P06','Botteghi2026Contagion','Elisa Botteghi and Martino Centonze and Davide Pastorello and Daniele Tantari',2026,
 'Contagion effects of heterogeneous cyber risk on network security and systemic stability','Economic Modelling','10.1016/j.econmod.2026.107854','https://arxiv.org/html/2601.16805v2',F,
 'arXiv:2601.16805v2（2026-10-05） §§2.1–2.3 Eqs.(1)–(6)，§3，§4.1–4.3 Eq.(20)；出版社S0264999326003834',
 '免疫/易感随机子图与路径风险；§4.3另用含恢复的SIS等动力学检验策略',
 '防御承诺、攻击种子分布响应的SSE；并非同时开环计划博弈',
 'η和z分别为双方节点估值；二次/L1成本；α、θ为成本权重，可作约束乘子解释',
 '小投资近似、网络保护指标、路径风险近似；定理有成本权重足够大条件',
 '多拓扑、多估值与欺骗案例；固定拓扑改变价值位置/区域的比较',
 '双方估值异质不等于q与出强度错位，但原文已把价值和拓扑联动；本项目只能主张具体两动作/容量/四格机制差异',
 '很高：最危险问题定位近邻','必须在研究缺口正面比较',
 'v1题名Network Security under Heterogeneous Cyber-Risk Profiles and Contagion，2026-01-23；v2与期刊同一工作只计一次。期刊卷期标December 2026（晚于审查日），已存在出版社页面及arXiv关联DOI，准确上线日未核实，不虚构提前发表日。',volume='165',pages='107854')
add('P07','Chen2025ProtectRecover','Wei Chen and Jingrui Wang and Yongxiang Xia and Zhen Wang',2025,
 'To protect, or to recover? The effect of defense resource allocation on network robustness','Chaos','10.1063/5.0267934','https://doi.org/10.1063/5.0267934',F,
 'literature/fulltext_audit/R4_extracted.txt；PDF第1页为封面，正文pp.2–4 §II Eqs.(1)–(6)，§III与结论',
 '度相关防御成本；节点移除/恢复和负载级联；保护与恢复预算比例',
 '随机攻击与选定防御顺序的仿真配置，非本项目双方同时开环博弈',
 '总资源拆分为保护与恢复；网络鲁棒性；非逐槽容量',
 '参数扫描和度排序策略',
 'BA/ER网络；资源变化的非单调配置和条件效应',
 '保护恢复取舍及资源/冗余条件依赖早已有之；不同传播物理和干预层级',
 '高：F及两动作动机已有','保护恢复与条件边界段',volume='35',pages='123136')
add('P08','Wu2025Vulnerability','Yanfang Wu and Peng Guo and Ying Wang and Enrico Zio',2025,
 'Attack-defense game modeling framework from a vulnerability perspective to protect critical infrastructure systems','Reliability Engineering & System Safety','10.1016/j.ress.2024.110740','https://re.public.polimi.it/handle/11311/1305169',A,
 '作者机构库摘要/作者/2025年份；出版社S0951832024008111摘要与章节概览；未读PDF正文',
 '功能脆弱性与级联失败；关键目标选择',
 'Stackelberg',
 '资源配置与累积前景理论风险态度；精确约束未核验',
 'PSO（机构摘要直接陈述）',
 '电网案例；出版社概览称IEEE57-bus',
 '关键性/系统影响与资源共同建模已有；不同于SIS型源隔离恢复与匹配控制',
 '中高：广义重要性创新不成立','关键性与系统风险背景',
 'DOI含2024不等于卷期2024；机构记录2025。发现OA PDF入口但未将可下载等同已读。',volume='256',pages='110740')
add('P09','Lou2026Crowdsensing','Kaiwen Lou and Guosheng Zhao and Jian Wang and Xiaodan Huang and Zixuan Wan',2026,
 'Collaborative defense model for crowdsensing networks based on incomplete Information differential games','Cybersecurity','10.1186/s42400-026-00577-4','https://link.springer.com/article/10.1186/s42400-026-00577-4',F,
 '出版社全文：模型Eq.(1)–(12)，Bayesian inference Eq.(13)–(17)，payoffs Eq.(22)–(23)，算法与dataset validation段',
 'N/I/S/C汇总状态；竞赛强度控制与随机扰动',
 '声称不完全信息微分博弈/贝叶斯策略推断；原文均衡声称未经本审查独立证明',
 '状态转移收益与行动成本；未核验出本项目两动作逐节点共享容量结构',
 'Bayesian更新及Hamiltonian迭代',
 '模拟和CICIoT2023数据校准验证（原文报告）',
 '不同信息与状态层级；本项目未建模隐蔽类型/贝叶斯反馈，不得借其验证证实自身',
 '中：最新差异背景，非最接近两动作机制','信息结构差异段',volume='9',pages='143')
add('P10','Guo2025Botnet','Chaojie Guo and Shen Wang and Ke Yu and Yuyao Zhu and Xiaofeng Tao',2025,
 'A Differential Game Method Against DDoS Attacks in IoT Botnets: Holistic and Dynamic Perspectives','IEEE Internet of Things Journal','10.1109/JIOT.2025.3541852','https://ieeexplore.ieee.org/document/10884766/',A,
 'IEEE官方索引摘要/卷页/日期；作者顺序经北邮导师主页、JST J-GLOBAL 202502265802413095核对；全文机器人验证受阻',
 '僵尸网络形成与DDoS攻击；潜伏期和攻击阈值',
 '微分攻防博弈；精确零和性/信息结构未读正文不判',
 '攻击激活与防御恢复；具体容量约束未核验',
 '最优控制方法；细节未核验',
 '传统/智能攻击数值仿真',
 '激活/恢复时机与动态策略已有；不同于价值位置匹配识别',
 '中高：动态恢复微分博弈非新','传播与动态博弈段',volume='12',number='12',pages='19414--19427')
add('P11','Paarporn2024Tradeoffs','Keith Paarporn and Shouhuai Xu',2024,
 'Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests','IEEE Control Systems Letters','10.1109/LCSYS.2024.3486629','https://par.nsf.gov/servlets/purl/10574678',F,
 'literature/fulltext_audit/R3_extracted.txt；正文pp.2422–2423 §II Eqs.(1)–(8)，§III Theorem 1，§IV证明',
 'Tullock攻破概率；独立目标；指数恢复时间；无节点间传播',
 '两物理阶段，资源事前同时选择；防御不观察受损集合；零和战略式Nash',
 '节点价值加权受损时长；预防和恢复共享总预算X，攻击预算Y',
 '分段解析均衡刻画',
 '解析结果及示例；不把理论标签移植本项目',
 '最直接否定双动作资源竞争首创；本项目增加传播、连续受损、非零和逐槽容量，不等于新理论',
 '很高：联合防御博弈最近邻','必须与Preciado并列比较',volume='8',pages='2421--2426')
add('P12','Cui2026Rescue','Lei Cui and Yifan Li and Shuhan Qi and Xuan Wang',2026,
 'Strategic allocation and dynamic rescue for multi-defender stackelberg security games with infectious attacks','Journal of King Saud University Computer and Information Sciences','10.1007/s44443-026-01181-9','https://link.springer.com/article/10.1007/s44443-026-01181-9',F,
 '出版社全文§3.1，Eqs.(7),(14)–(19),(22)–(30)，§3.3算法，§4实验；2026-08-27',
 '异质节点价值/阈值；目标被攻击后可转移盈余救援；邻接感染损失',
 '多防御者初始分配→攻击选目标→事前公布规则的目标条件救援；SNE',
 '各防御者资源预算、转移边容量、捐赠者安全约束、资产和资源损失',
 '集中MILP基准；均衡引导分配与贪心救援启发式，失败标记',
 '三模拟三真实网络（论文报告）；损失/时间比较',
 '最新传播/估值/动态救援组合；非时变源隔离和局部恢复率，同样不能把其dynamic与本项目开环混称',
 '高：2026新增危险先例','最新传播再配置段',volume='38',pages='813')
add('P13','Zargham2014WorstCase','Michael Zargham and Victor M. Preciado',2014,
 'Worst-Case Scenarios for Greedy, Centrality-Based Network Protection Strategies','arXiv preprint','','https://arxiv.org/abs/1401.5753',A,
 'arXiv:1401.5753v1摘要及提交史，2014-01-22',
 '线性化SIS，中心性贪心保护', '单方网络保护', '有限保护资源、遏制速率',
 '构造中心性启发式任意低效反例，GP比较（摘要）', '构造网络及仿真',
 '中心性启发式不可靠早已有之，本文反例不是这一一般命题首证', '中：启发式优劣动机','启发式局限段',eprint='1401.5753',archivePrefix='arXiv',version='1')
add('P14','Eshghi2014Patching','Soheil Eshghi and MHR. Khouzani and Saswati Sarkar and Santosh S. Venkatesh',2014,
 'Optimal Patching in Clustered Malware Epidemics','arXiv preprint','','https://arxiv.org/abs/1403.1639',A,
 'arXiv:1403.1639v1摘要；作者Cornell主页；期刊DOI 10.1109/TNET.2014.2364034另有2016卷期记录',
 '分层异质传播及动态补丁','单方最优控制','传播损失与补丁成本',
 'PMP与单阈值结构（摘要报告）','样例拓扑数值实验',
 '异质传播与时间策略非新；其单阈值不适用于本项目', '中','动态传播控制基础',
 '本条引用实际核验的2014预印本，不将DOI中2014误作期刊卷期年份；期刊版不另计一篇。',eprint='1403.1639',archivePrefix='arXiv',version='1')
add('P15','Acemoglu2016Contagion','Daron Acemoglu and Azarakhsh Malekian and Asuman Ozdaglar',2016,
 'Network security and contagion','Journal of Economic Theory','10.1016/j.jet.2016.09.009','https://www.sciencedirect.com/science/article/pii/S0022053116300837',A,
 '出版社摘要与MIT作者公开稿摘要，未深入正文',
 '互联主体安全投资与级联，外生/战略攻击', '分散主体投资、攻击选点内生化',
 '自身效应/外部性与社会最优比较','递归收益分解及小投资展开（摘要）',
 '理论与模拟','战略转移攻击可引起负外部性，说明防御投资效果非普适', '中高：价值/传播机制基础','网络外部性段',volume='166',pages='536--585')
add('P16','Goyal2014Attack','Sanjeev Goyal and Adrien Vigier',2014,
 'Attack, Defence, and Contagion in Networks','The Review of Economic Studies','10.1093/restud/rdu013','https://www.repository.cam.ac.uk/handle/1810/246381',A,
 'Cambridge作者机构库摘要/DOI/作者/卷；OUP直接页未能打开',
 '网络设计、防御与成功攻击后传播', '设计者先设计网络和配置防御，攻击者再分配并决定传播',
 '网络价值、冲突技术、资源配置', '解析网络结构条件（摘要）',
 '理论模型；星形或多枢纽/多分量条件',
 '网络位置与价值/资源已有联合讨论；本项目固定图的两因子干预不同于内生网络设计', '中高','传播攻防基础',volume='81',number='4',pages='1518--1542')
add('P17','Chen2017Infrastructure','Juntao Chen and Corinne Touati and Quanyan Zhu',2017,
 'A Dynamic Game Analysis and Design of Infrastructure Network Protection and Recovery','ACM SIGMETRICS Performance Evaluation Review','10.1145/3152042.3152079','https://arxiv.org/abs/1707.07054',A,
 'arXiv:1707.07054v1摘要、Journal reference和related DOI；未读全文',
 '基础设施连通性，建/删边与恢复', '两方三阶段，子博弈精炼均衡SPE',
 '连通效益与建删边成本', '参数化SPE解析（摘要）',
 'UAV通信灾难恢复案例',
 'dynamic protection/recovery博弈已有；不同物理与均衡时序', '中','动态保护恢复游戏段')
add('P18','Watkins2015Bilayer','Nicholas J. Watkins and Cameron Nowzari and Victor M. Preciado and George J. Pappas',2015,
 'Optimal resource allocation for competitive spreading processes on bilayer networks','arXiv preprint','','https://arxiv.org/abs/1512.05299',A,
 'arXiv:1512.05299v1摘要/版本，2015-12-16；后续期刊版未核验',
 'SI1SI2S双层竞争传播，边感染/节点恢复异质', '传播过程竞争，不等同战略玩家Nash',
 '最小遏制支出，预算不足的替代准则', '均值场稳定条件及资源优化（摘要）',
 '随机过程与均值场对照，并报告近似不准的情形',
 '两传播过程竞争不可当作已有或新攻防博弈；可借鉴近似边界报告', '中','传播控制方法边界',eprint='1512.05299',archivePrefix='arXiv',version='1')
add('P19','Ren2020Honeynet','Jianguo Ren and Chunming Zhang',2020,
 'A differential game method against attacks in heterogeneous honeynet','Computers & Security','10.1016/j.cose.2020.101870','https://www.sciencedirect.com/science/article/pii/S0167404820301425',A,
 '出版社摘要、引言和CRediT作者；状态/收益方程不可得，非全文核验',
 '普通节点与蜜罐交互；攻击、捕获和补丁', '微分博弈，作者声称鞍点；精确零和性未核验',
 '收益/损失和成本；预算未核验', '作者报告最优策略求解算法，正文细节未知',
 '随机策略及度/时域参数比较',
 '多个防御动作、度和时域条件依赖均非首次；不同于隔离恢复共享容量的匹配识别', '高：B/F的早期近邻','传播微分博弈段',volume='97',pages='101870')
add('P20','Wu2022IoT','Huici Wu and Qiuyue Gao and Xiaofeng Tao and Ning Zhang and Dajiang Chen and Zhu Han',2022,
 'Differential Game Approach for Attack-Defense Strategy Analysis in Internet of Things Networks','IEEE Internet of Things Journal','10.1109/JIOT.2021.3122115','https://doi.org/10.1109/JIOT.2021.3122115',A,
 'IEEE Communications Society 2022-06目录；P09出版社参考文献与可访问摘要 https://www.canyam.com/en/article/differential-game-approach-for-attack-defense-strategy-analysis-in-internet-of-things-networks/7714521',
 '攻击/防御竞争强度，设备安全状态ODE', '零和微分博弈（摘要）',
 '设备控制权竞争；约束精确式未核验', '最优控制与Gauss–Seidel式隐式差分（摘要）',
 '数值状态演化',
 '非零和与该零和先例不同，但P01已有非零和，不能只据此创新', '中高','零和/非零和区别',
 '官方正文访问失败；方法信息仅摘要，不能作为逐方程排除相同机制的证据。DOI在线2021，卷期2022。',volume='9',number='12',pages='10340--10353')
add('P21','Ebel2024Investment','Austin Ebel and Debasis Mitra',2024,
 'Economics and optimal investment policies of Attackers and Defenders in cybersecurity','Journal of Cybersecurity','10.1093/cybsec/tyae019','https://academic.oup.com/cybersecurity/article/10/1/tyae019/7900094',A,
 'OUP检索返回正文引言/结构/结论片段；直接页面打开失败；未核验完整模型式',
 '攻击者和防御者投资，系统先验脆弱性', '顺序Stackelberg投资',
 '损失/收益与投资、威慑成本；精确式未核验', '非凸目标驻点/决策区间分析（可访问片段）',
 '解析与数值例',
 '投资的条件性和跳变已有；单系统而非源隔离传播网络', '中','经济配置及条件边界',volume='10',number='1',pages='tyae019')

def write(name, text):
    path = OUT / name
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite {path}')
    path.write_text(text.strip()+'\n', encoding='utf-8')

def export_matrix_bib():
    fields=[k for k in papers[0] if k!='bib_extra']
    with (OUT/'C_prior_art_matrix.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for p in papers: w.writerow({k:p[k] for k in fields})
    entries=[]
    for p in papers:
        pre=p['source']=='arXiv preprint'
        d=dict(author=p['authors'],title='{'+p['title']+'}',year=str(p['year']),url=p['url'])
        if not pre:d['journal']=p['source']
        if p['doi']:d['doi']=p['doi']
        d.update(p['bib_extra'])
        if pre:d['note']='Preprint; version '+d.pop('version')+'; metadata and abstract verified 2026-11-07'
        elif p['id']=='P06': d['note']='Journal DOI linked by arXiv:2601.16805v2, revised 2026-10-05; earlier title: Network Security under Heterogeneous Cyber-Risk Profiles and Contagion; issue dated December 2026; exact online date not verified'
        else:d['note']='Verification scope: '+('methods checked from full text' if p['access']==F else 'abstract or accessible article preview only')+'; accessed 2026-11-07'
        entries.append('@'+('misc' if pre else 'article')+'{'+p['bibkey']+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in d.items())+'\n}')
    return '\n\n'.join(entries)

if __name__=='__main__':
    raise SystemExit('Builder is completed by C_finish_audit.py; import only.')
