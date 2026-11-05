# 03 · 文献查新、引文核查与贡献裁决

## 核心目的

证实或推翻拟议的**具体差异化贡献**，不是给预定的创新点找包装。Work 独立检索最新可访问的原始论文、期刊页面、DOI 数据，保存核验 URL、发表年份/版本、访问状态与关键页码（如有），绝不虚构已读全文。

## 优先核对的高重合文献线索（均须再次核实）

1. Tian 等，*Analysis of attack-defense game for advanced malware propagation control in cloud*，Computer Communications (2025)，候选 DOI `10.1016/j.comcom.2025.108148`。关注云工作负载/VM 传播、博弈类型、均衡和求解机制。
2. Zhang 等，*A differential game approach for real-time security defense decision in scale-free networks*，Computer Networks (2023)，候选 DOI `10.1016/j.comnet.2023.109635`。关注拓扑和传播状态下的动态安全决策。
3. Paarporn 与 Xu，*Preventive-Reactive Defense Tradeoffs in Resource Allocation Contests*，IEEE Control Systems Letters (2024)，候选 DOI `10.1109/LCSYS.2024.3486629`。关注保护/恢复资源权衡，谨防错误宣称新发明。
4. Chen 等，*To protect, or to recover? The effect of defense resource allocation on network robustness*，Chaos (2025)，候选 DOI `10.1063/5.0267934`。核查预算变化、优先级切换是否已存在。

以上条目仅为**优先检索线索**，不代表新项目已核实其标题、DOI、机制或全文内容。若不准确，必须纠正记录；不能只凭摘要断言先前研究“没有”某机制。

## 必须制作的差异矩阵 `literature/prior_art_matrix.md`

列：作者/年份/可核验链接/查阅范围（全文/摘要/未核实）/安全状态/资产异构/攻击策略/隔离控制/恢复控制/业务中断成本/双方预算/均衡类型/求解算法/理论贡献/实验类型/与本研究重叠/本研究尚可能成立的实质差异/证据位置。

另输出 `literature/novelty_decision.md`，区分：

- **已知构件**：网络 SIS 类传播、微分攻防博弈、多资产、双边资源限制、保护-恢复权衡；这些组合不可自动视为“首次”。
- **有可能差异化的机制**：在价值-传播影响相分离时，隔离业务损失与攻击者资源响应共同影响的**动态资源分配**；必须指出确切不同于最相近论文的建模假设、命题或实证发现。
- **创新性不足风险**：只有 KKT 边际式及展示几张仿真图时，可能只是重述常规结论。必须在 G1 前明确到底以理论性质、策略可解释性、算法或经验规律哪条路径作为主线。

## 写作与引用纪律

- 文献支持的事实与本项目的假设/推论分开标示；不得用论文摘要推断不可见正文的空白。
- 引用必须可回溯到真实 DOI/出版社/预印本条目；无从核实时不要把该文献加入正式参考文献。
- 优先 8–15 篇强相关且已核实文献，数量服从质量。基础理论引用可包含经典最优控制/微分博弈权威资料。
- 若核实发现创新主线已被覆盖，G1 必须提交修订选项，不能悄悄改变名称继续声称新颖。
