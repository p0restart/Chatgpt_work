# 1 引言

网络化工作负载之间的访问与信任关系可能形成有向攻击传播通道，使局部受损影响下游资产。在资源容量有限时，防御者既需要抑制传播，也需要恢复已受损服务。两类行动面向不同的状态变化过程，其配置不能仅由资产的直接业务价值决定：高价值节点未必具有较强的出向传播能力，而传播较强的节点也未必承担较高的直接损失。云工作负载为这一问题提供了应用动机，本文则在合成网络上分析相应的资源取舍。

联合配置传播抑制与恢复资源已有充分研究基础。Preciado等[1]在有向异质网络中联合调整感染率与恢复率，通过几何规划求解预算约束下的传播控制问题。Paarporn和Xu[2]进一步研究攻击竞争下预防与恢复共享资源的取舍，给出特定零和资源竞赛的均衡刻画。前者采用静态率参数优化，后者以独立节点的攻破概率及恢复时长描述损失。两者说明，联合防御和资源竞争本身不能作为本文的原创性依据。

传播微分博弈为动态攻防提供了另一条研究路径。Tian等[3]已针对云恶意软件传播建立非零和开环攻防模型，并利用状态和伴随方程求取控制计划。价值异质性与网络位置的共同作用同样已有先例：Botteghi等[4]在Stackelberg安全博弈中分析双方估值与传播风险对保护配置的影响。Chen等[5]则从负载级联角度考察保护—恢复比例，表明资源条件会改变两类行动的取舍。因此，动态博弈、价值异质性及条件性配置均不是尚未涉及的领域空白。

这些研究基础仍需落实到可区分的配置问题。本文关注：在上游攻击暴露匹配时，高价值位置变化对防御计划和损失的影响，是否依赖节点的出向传播条件？进一步地，在指定训练与攻击评价协议下，联合计划相对单动作、静态计划及固定攻击训练计划的配对损失差异有多大？回答这些问题需要把价值位置干预与传播条件交叉比较，并在相同攻击评价规则下设置不同的强基线。直接价值、出向传播强度与未来动态损失须分别处理，不能用一个静态节点指标替代三者。

本文采用有限时域非零和开环微分博弈，将攻击入口投入、来源节点出边隔离和本地恢复纳入同一状态模型，隔离与恢复共享逐时容量。双方事前确定时间计划，数值上以分段常值控制和直接射击计算目标，通过交替局部响应形成候选。Hamiltonian分析用于解释资源边际作用，多初值、单边偏离及积分精化用于检查数值质量；这些检查不构成连续控制全局Nash证明。

本文主要贡献是在匹配上游暴露的合成网络中，以价值位置交换和传播条件变化构造四格对照，分析两因素对损失与资源计划的交互响应。支撑贡献是在指定训练与攻击评价协议下，分别与单动作、静态联合及固定攻击训练方案进行配对比较，并将小增益、容量松弛与负反例纳入解释。这三层差异不可相加为总收益，也不构成可独立归因的因果效应。动作语义明确的模型为上述分析提供统一研究设置，不作为独立方法创新。研究结论限于具体模型与已检验配置，不主张新的均衡算法或普遍配置规律。

下文第2节给出系统模型与问题定义，第3节分析控制的必要条件并说明数值求解及诊断边界，第4节介绍匹配实验和评价设计，第5节报告结果及适用限制，第6节总结研究发现。

## 参考文献

[1] Preciado V M, Zargham M, Enyioha C, Jadbabaie A, Pappas G J. Optimal Resource Allocation for Network Protection Against Spreading Processes. IEEE Transactions on Control of Network Systems, 2014, 1(1): 99–108. DOI: [10.1109/TCNS.2014.2310911](https://doi.org/10.1109/TCNS.2014.2310911). [已核公开全文](https://arxiv.org/html/1309.6270).

[2] Paarporn K, Xu S. Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests. IEEE Control Systems Letters, 2024, 8: 2421–2426. DOI: [10.1109/LCSYS.2024.3486629](https://doi.org/10.1109/LCSYS.2024.3486629). [公开稿](https://par.nsf.gov/servlets/purl/10574678).

[3] Tian L, Gan C, Lin J, Shang F, Zhu Q. Analysis of attack-defense game for advanced malware propagation control in cloud. Computer Communications, 2025, 237: 108148. DOI: [10.1016/j.comcom.2025.108148](https://doi.org/10.1016/j.comcom.2025.108148).

[4] Botteghi E, Centonze M, Pastorello D, Tantari D. Contagion Effects of Heterogeneous Cyber Risk on Network Security and Systemic Stability. arXiv:2601.16805v2, 2026-10-05. [所引版本全文](https://arxiv.org/html/2601.16805v2).

[5] Chen W, Wang J, Xia Y, Wang Z. To protect, or to recover? The effect of defense resource allocation on network robustness. Chaos, 2025, 35: 123136. DOI: [10.1063/5.0267934](https://doi.org/10.1063/5.0267934).
