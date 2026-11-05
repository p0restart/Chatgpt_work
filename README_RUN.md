# 运行说明（原G1及G1-C1有效；G2待审）

2026-10-28：G1-C1全部36配置已完成与审计。先读[机制结论](reports/MATCHED_MECHANISM_FINDINGS.md)及[完整数值表](reports/MATCHED_MECHANISM_RESULTS.md)；当前人工审查包为[匹配网络G2补充](reviews/G2_C1_submission.md)。实际数据results/matched_mechanism/run01，数值通过不代表普适切换成立。

G1批准：2026-10-26，路线A及五项范围；G2尚未批准。数值结果为合成K槽开环局部响应，不是连续反馈Nash证明。

```powershell
python -m pytest -q
python -m src.experiments --config configs/base.yaml --output results/p3/new_pilot --pilot
python -m src.experiments --config configs/base.yaml --output results/p3/new_main
python -m src.fair_evaluation --source results/p3/new_main --output results/p3/new_fair
python -m src.audit_p3 --root results/p3/new_fair
python -m src.summarize_p3 --root results/p3/new_fair
```

每次选择新输出目录。main保存原交替候选；fair保留每种方法的最终防御并补齐完整攻击响应，主公平比较使用fair。fair可在main完成后执行，也可读取已完成的配置；最多等待/执行30分钟，超时保留部分结果。audit_p3的pilot复现默认检查同级pilot01/pilot02，其他实验位置请相应配置目录。所有历史结果保留，不覆盖P2。

实际数据：results/p3/main01、fair01；最小复现：pilot01、pilot02。参数、边表、原始优化初末控制及退出码、逐槽预算、轨迹、12/24/48积分细化均在各配置子目录。数值环境沿用requirements-p2-observed.txt，pytest版本差异保留。图表QA依赖独立于数值实验环境。


审查入口：reviews/G2_submission.md；图表检查：reports/P3_figure_QA.md。实际主批次约1032秒，派生评价含等待约710秒，两过程部分重叠。

```powershell
python -m src.plot_p3 --root results/p3/fair01 --output figures/reproduced_p3 --qa-scripts C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts
```

绘图需要上述QA脚本路径；数值实验不依赖该技能目录。PDF碰撞检查专用依赖在.figure-deps，不能将该目录加入正式数值运行环境。历史测试和数据文件仍完整保留。

## 2026-10-27 补充诊断
当前主入口：reports/RESEARCH_EXPLANATION.md 与 reports/MECHANISM_EQUILIBRIUM_FINDINGS.md。原G2包需结合该补充，不代表核心机制已验证。

```powershell
python -m src.diagnose_equilibrium --output results/equilibrium_audit/new_run
python -m src.diagnose_counterexample --equilibrium-root results/equilibrium_audit/new_run --output results/equilibrium_audit/new_counterexample
python -m src.explain_counterexample --equilibrium-root results/equilibrium_audit/new_run --counterexample-root results/equilibrium_audit/new_counterexample
```

G1-C1匹配网络方案已于2026-10-27获用户明确批准；原提案文件名保留，状态已更新。执行与核验命令：

```powershell
python -m src.matched_mechanism --output results/matched_mechanism/new_run
python -m src.audit_matched --root results/matched_mechanism/new_run
python -m src.report_matched --root results/matched_mechanism/new_run --output reports/MATCHED_MECHANISM_REPRODUCED.md
```

先自动执行seed11/B1.2四格，数值通过后才扩展。任一组数值失败停止；30分钟在组边界保存，纯时间分段可在检查输入哈希后用`python -m src.resume_matched --root results/matched_mechanism/new_run`继续其余已批准配置。此命令拒绝重试数值失败、正在运行或不完整的组，不覆盖结果。

独立pilot复现：

```powershell
python -m src.matched_mechanism --output results/matched_mechanism/new_pilot --pilot-only
python -m src.compare_matched --original results/matched_mechanism/new_run --repeat results/matched_mechanism/new_pilot
```

G2未批准前不进入最终论文合稿。协议见reports/MATCHED_MECHANISM_PROTOCOL.md；当次状态见logs/STATUS.md。

## 2026-11-03 C2补充实验与写作入口
最新结果：reports/C2_FINDINGS.md；写作决定：manuscript/preparation/WRITING_DECISION.md；审阅：reviews/G2_C2_submission.md。
复现需要保留原matched_mechanism/run01、p3/fair01及equilibrium_audit/run01输入；源文件哈希见本轮source_provenance_audit.json。新输出目录不得已存在。

```powershell
python -m src.supplement_c2 --output results/supplement_c2/reproduction_new
python -m src.report_c2 --root results/supplement_c2/reproduction_new --report reports/C2_REPRODUCED.md
```

