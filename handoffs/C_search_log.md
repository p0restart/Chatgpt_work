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
