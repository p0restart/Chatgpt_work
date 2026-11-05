# 文献核验记录（2026-10-24，Asia/Shanghai）

**2026-10-25 来源更新**：用户提供 R1–R5 五篇本地 PDF 正文，已读取模型、目标、均衡与实验相关页，逐篇页码及差异见 [正文差异矩阵](prior_art_matrix_G1.md)。下文“未取得全文”“仅摘要”及访问失败记录均为 2026-10-24 历史记录，不代表当前来源状态。本文仍未完成系统查新或对论文全部证明的独立复核。

本次为有范围限制的 G1 查新；未取得下列四篇完整正文，均不得标记全文已读。没有凭摘要断言某机制不存在。没有核验所有参考文献的优先权。条目日期采用页面明确出版信息，不采用搜索引擎“若干月前”的相对时间。

## R1 Tian 等（2025）

Liang Tian; Chenquan Gan; Jiabin Lin; Fengjun Shang; Qingyi Zhu. *Analysis of attack-defense game for advanced malware propagation control in cloud*. Computer Communications 237, 108148，2025-05-01。DOI [10.1016/j.comcom.2025.108148](https://doi.org/10.1016/j.comcom.2025.108148)。

实际来源：[ScienceDirect 预览](https://www.sciencedirect.com/science/article/abs/pii/S0140366425001057)，题名、作者、卷/文章号及 Abstract、Introduction、Experimental analysis 预览。仅摘要/部分预览，未读模型公式及证明全文。文中自述每 VM 建模、微分攻防、Nash 与加速算法；这是作者声明，未独立验证其证明。实验预览指向 YouTube/Facebook/Twitter 网络，不能据“real-world datasets”改写成云生产攻击实测。

## R2 Zhang 等（2023）

Hengwei Zhang; Yan Mi; Xiaohu Liu; Yuchen Zhang; Jindong Wang; Jinglei Tan. *A differential game approach for real-time security defense decision in scale-free networks*. Computer Networks 224, 109635，2023-04。DOI [10.1016/j.comnet.2023.109635](https://doi.org/10.1016/j.comnet.2023.109635)。

实际来源：[出版社搜索可读摘要](https://www.sciencedirect.com/science/article/pii/S1389128623000804)。直接打开曾返回403，搜索工具返回完整摘要。仅摘要；可确认无标度网络传播、动态攻防、鞍点策略及按互联网平均度构造的仿真网络。不能由题名“real-time”认定是严格 Markov 反馈 Nash；不能判断是否已有来源隔离、恢复及业务中断成本。

## R3 Paarporn、Xu（2024）

Keith Paarporn; Shouhuai Xu. *Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests*. IEEE Control Systems Letters 8, 2421–2426 (2024)。DOI [10.1109/LCSYS.2024.3486629](https://doi.org/10.1109/LCSYS.2024.3486629)。

来源：[作者研究主页](https://sites.google.com/site/kpaarporn/research)确认题名、作者、期刊/卷/年；[NSF 作者稿入口](https://par.nsf.gov/servlets/purl/10574678)的搜索索引可读摘要及引言；[DBLP](https://dblp.dagstuhl.de/rec/journals/csysl/PaarpornX24.html)交叉确认 DOI 和页码（书目信息辅助，不作技术机制证据）。[IEEE 页面](https://ieeexplore.ieee.org/document/10735383/)遇机器人验证。只读取摘要/引言片段，不称全文已读，不填写正文页码。

可确认两阶段机制：预防资源影响攻陷概率，恢复资源影响攻陷后恢复过程；以期望受损时间建立对抗资源分配，作者声明刻画 Nash。与本项目并行发生的传播隔离/恢复有候选结构差异，但是否还有更广泛网络耦合须查全文。

## R4 Chen 等（2025）

Wei Chen; Jingrui Wang; Yongxiang Xia; Zhen Wang. *To protect, or to recover? The effect of defense resource allocation on network robustness*. Chaos 35(12), 123136 (2025)。DOI [10.1063/5.0267934](https://doi.org/10.1063/5.0267934)。

实际可读来源：[PubMed 的作者摘要与书目信息](https://pubmed.ncbi.nlm.nih.gov/41416673/)，Abstract 两段；[AIP DOI 入口](https://pubs.aip.org/aip/cha/article-lookup/doi/10.1063/5.0267934)未能打开。仅摘要。摘要已明确提出资源增长时恢复→保护→恢复的非单调分配，以及关键节点防御成本和冗余负载容量对恢复份额的影响。“发现保护恢复优先级切换”不能单独作为创新。

日期保留差异：PubMed 期刊字段为2025-12-01；搜索到的第三方预览写在线2025-12-19，但未取得出版社页面确认，正式引用仅保留2025年，不能把两个字段混为同一上线日期。

## R5 补充近邻（2023）

Hengwei Zhang; Yan Mi; Yumeng Fu; Xiaohu Liu; Yuchen Zhang; Jindong Wang; Jinglei Tan. *Security defense decision method based on potential differential game for complex networks*. Computers & Security 129, 103187 (2023)。DOI [10.1016/j.cose.2023.103187](https://doi.org/10.1016/j.cose.2023.103187)。[出版社](https://www.sciencedirect.com/science/article/pii/S0167404823000974)可读摘要和书目信息，标注开放获取不等于本次读到全文。复杂网络势微分博弈、鞍点策略及小世界/无标度仿真进一步否定“网络+微分博弈”本身的新颖性。相关全局最优声明未复核证明。

## 检索与访问失败记录

- 精确检索四个候选 DOI、四个题名，以及 preventive-reactive PDF、potential differential game；由近邻引文补充 R5。不是系统综述，不声称穷尽8–15篇相关工作。
- ScienceDirect 部分 direct-open 为403，但搜索返回出版社摘要/预览；IEEE 为机器人页；NSF PDF 多次 web-open 为502。
- 本地 Python 下载 NSF 合法作者稿先报 SSL ASN1 错误；备用文档 Python 报 DNS getaddrinfo 失败，未关闭证书校验、未保存伪PDF、未取得全文。
- AIP DOI/正文入口无法访问；PubMed 可读摘要。以上限制降低创新裁决强度，不阻断已完成数值验证。
- G1 建议：允许按有限机制研究继续探索，同时把 R1/R2 正文核查列为强创新表述前的未关闭项。所有“未核实”格不能当作“没有”。
