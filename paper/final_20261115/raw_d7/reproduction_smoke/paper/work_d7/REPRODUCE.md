# D7复算与重新优化

## 环境

当次环境：Windows、本地Python 3.11.7、NumPy 1.26.4、SciPy 1.11.4；其余版本见sources/environment_final.json及每次运行environment*.json。需要NumPy、SciPy、Pandas、PyYAML、Matplotlib、tabulate；PDF碰撞检查另需PyMuPDF。优化过程无联网需求。使用不同版本时应重新执行质量检查，不能只比较舍入后的论文表值。

压缩包以项目根目录布局保存src、02_MODEL_SPEC.md、paper/work_d5/analysis/run_replanning.py和paper/work_d7。解压到新目录，在该根目录执行以下命令。不要覆盖原项目。D7目录还含source_snapshot副本及当次文件SHA。

## 先复算已有轨迹

```powershell
python paper/work_d7/analysis/verify_d7.py
python paper/work_d7/analysis/summarize_results.py
python paper/work_d7/analysis/make_figures.py
python paper/work_d7/analysis/assemble_paper.py
python paper/work_d7/analysis/check_figures.py
```

第一步用独立实现的DOP853重新积分六条离线与24条执行控制轨迹，核对状态、成本、约束、数据库隔离、公共攻击及原源码SHA。它不会重新优化。第二步补充1080行逐资产行动成本并核对30组总成本；后两步仅生成图表与正文。PDF检查依赖PyMuPDF；已交付全部当次检查报告。

## 全部重新优化（新目录）

```powershell
python paper/work_d7/analysis/reproduce.py D7_independent_run --run
```

目标目录必须不存在。程序复制源码与固定设置后，按以下顺序执行，不覆盖本包：Gate1预检查→B1.2 G/F→主容量交叉→其他容量离线及交叉→B1.2事件→B1.2无扰动→其他容量事件→独立复算→表图及论文生成。原种子、路径选择、阈值与模型参数保持不变。

若只准备目录而不开始优化，去掉`--run`。任何步骤非零退出即停止，不自动重试、换参数或选收益更好的路径。应保存该新目录的失败证据并诊断。

## 当次已经完成的验证与尚未声称的验证

已完成原登记的全部新数值阶段，以及不同积分实现的固定控制独立复算。还在新建目录进行了源码载入和Gate1预检查，检验移交路径及依赖。未再次整批重新优化，也未在第二台机器独立复现；不得把准备目录或预检查写作已完成独立全流程优化。重新运行的耗时可能受机器状态影响，不能要求与原日志完全一致。

原始日志中`online_seconds`沿用D5字段；离线G/F报告为离线求解时间。`timing.csv`中的总任务时间包含嵌套响应优化，不能重复相加。正式原始结果只读保留；再生成的派生表和图可以与原件SHA/数值比较。

## 数据定位

- `results/static/B*/`：三个容量的模型、G/F控制、逐时状态、完整交叉表及局部响应记录。
- `results/rolling_event_B*/`：三容量事件执行结果；`rolling_control_B1.2/`为无扰动对照。
- `planned_controls.csv`：各次内部规划；`executed_controls.csv`：实际首区间拼接后的行动。不可互换。
- `optimizer_calls.jsonl`：各次输入、种子、退出码及返回控制；`solver_audit.csv`：同一完整对的最终诊断。
- `results/derived/all_asset_decisions.csv`：统一1080行节点—区间输出；各分项和诊断源路径完整。
- `results/verification.json`、`independent_checks.csv`：114项独立固定控制复算。
- `sources/source_manifest.json`：运行前来源快照；`runtime_manifest.json`：交付执行代码快照；二者时间含义不同，不覆盖历史SHA。

本包不复制第三方论文全文，引用核验依据与访问层级在reference_claim_map.md中。数值复算不需要论文原件、旧拓扑结果、网络访问或外部审批服务。
