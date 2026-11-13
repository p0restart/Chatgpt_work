# 攻防交互下异质传播网络的隔离与恢复配置：匹配对照与收益边界

## 中文摘要

资产的直接价值与出向传播能力并不总是一致，其相对位置如何影响隔离与恢复配置，需要在匹配条件下检验。本文采用隔离与恢复共享逐时容量的非零和开环攻防模型，构造上游暴露匹配的六节点合成网络，交叉改变高价值位置与出向传播条件。在三个种子、三个容量的36个分段开环局部候选中，九组价值—传播损失交互均为正，为0.018274—0.029192，相当于同组C格损失的0.170%—0.261%。控制记录显示，低容量下两个价值交换节点的隔离近零，中容量存在时窗与种子异质性，高容量大多松弛，因而正向目标交互不对应普遍动作切换。九个D格配置中，联合动态计划相对固定攻击训练计划的损失改善在响应攻击评价下仅为0.029%—0.286%，在公共固定攻击下均为负；原网络另有联合计划不占优反例。两组控制槽精化保持目标交互方向，但六槽嵌入后仍可发现十二槽单边改善。结果表明，该构造族中的价值位置效应依赖传播条件，联合防御收益同时受训练与攻击评价规则限制；证据不构成连续控制全局Nash或真实云环境有效性证明。

**关键词：** 开环微分博弈；传播网络；隔离与恢复；匹配对照；资源配置

## English title

Isolation and Recovery Allocation in Heterogeneous Propagation Networks under Attack–Defense Interaction: Matched Comparisons and Limits of Benefit

## Abstract

The direct value of an asset need not align with its capacity to propagate damage. We examine how this mismatch affects isolation and recovery allocation using a non-zero-sum open-loop attack–defense model with shared instantaneous defense capacity. A six-node synthetic network matches upstream exposure while crossing high-value location with outgoing propagation conditions. Across 36 piecewise-constant local candidates covering three seeds and three capacity levels, all nine loss interactions are positive, ranging from 0.018274 to 0.029192, or 0.170%–0.261% of the corresponding cell-C loss. Control records show negligible isolation at the two value-swapped nodes under low capacity, heterogeneous temporal responses under medium capacity, and mostly slack capacity at the highest level. Thus, positive loss interactions do not imply a universal switch between actions. Across nine cell-D configurations, the joint dynamic plan improves loss over fixed-attack-trained plans by only 0.029%–0.286% under local attack-response evaluation and performs worse under the common fixed attack. A separate original-network case also shows joint defense failing to outperform recovery alone. Refinement from six to twelve control intervals preserves the interaction direction in two selected four-cell groups, while unilateral improvements remain detectable against embedded six-interval plans. These findings establish a conditional value-location effect within the tested construction and identify evaluation-dependent limits on joint-defense benefits. They do not certify a global continuous-control Nash equilibrium or effectiveness in operational clouds.

**Keywords:** open-loop differential game; propagation network; isolation and recovery; matched comparisons; resource allocation
