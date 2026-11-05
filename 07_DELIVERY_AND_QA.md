# 07 · 最终交付物、严谨性与审核清单

## 必须交付的文件

| 目录 | 最低产物 |
|---|---|
| `src/` | 模型、目标函数、约束、最优响应与实验绘图程序；明确运行入口 |
| `tests/` | 状态界、出站隔离索引、攻击入口、预算、目标分解、积分收敛、最佳响应、复现性测试 |
| `configs/` | 基线和全部正式实验的参数/网络边表/种子，最好保存环境版本或 lockfile |
| `results/` | `summary.csv`, `trajectories.csv`, `solver_trace.csv`, `metadata.json` 和各图数据 |
| `figures/` | 至少 4 幅与结果 CSV 一一对应的图（能由代码重建） |
| `literature/` | `prior_art_matrix.md`, `novelty_decision.md`, `references_verified.md` |
| `reports/` | `verification.md`, `reproduce.md`, `final_audit.md`，如失败附 `blocker.md` |
| `reviews/` | `G1_submission.md`, `G2_submission.md`, `APPROVAL_LOG.md`，包含用户明确批复 |
| `paper/` | `manuscript.md`, `references.bib`, `evidence_map.md`, `review_checklist.md`；如环境允许另交 `.docx` 或 `.pdf` |
| 根目录 | `DECISIONS.md`, `logs/STATUS.md`, `README_RUN.md` |

## 审稿人式自检

- **原创性**：最相近三篇以上论文的机制差异是否被正文中的证据支持？不能只说“研究更全面”。
- **数学**：状态不变域证明成立？伴随方程与控制梯度符号正确？边 `j→i` 的索引一致？最优性条件是否只是必要条件？
- **算法**：哪些结果是单方局部数值最优？哪个是受限开环近似 Nash 的诊断？是否写明多起点、阈值、停止码和未收敛情况？
- **数据**：参数真是合成模拟？3 种预设种子是否完整保留？是否只挑成功案例？固定/自适应攻击两类基线是否区分？
- **成本**：`J_D` 分项是否求和一致？资源容量和二次经济成本是否混用？“提升 X%” 之类百分比是否能复核？
- **写作**：摘要/结论每条主要结果均可追溯到图、表、代码与 CSV；引用题名、DOI、年份实际核对，避免未证实“首次”。
- **可复现性**：README 一条最小运行命令、一条主要实验命令、对应环境/种子版本、预计运行资源说明（若已实际测得可提供）。
- **审批**：G1 与 G2 必须有用户批复；批准范围外的结果不许直接加到稿件结论。

## 交付质量声明

最终 `reports/final_audit.md` 需给出三栏：**已独立验证**、**数值证据支持但未有数学证明**、**尚未解决/阻碍投稿**。无论达到哪一个层次，都要如实记录。
