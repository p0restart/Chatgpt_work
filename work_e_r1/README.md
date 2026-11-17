# Work E-R1 读取与复核

先读R1_final_report.md，再读R1_01至R1_06。proofs/保留完整二阶推导、交叉界与全域RK4误差证明；results/保存精确分数证书、区间端点及检查结果。原Work E及D7/D8全部保留。

本阶段只做数学推导和必要的辅助认证，没有新随机策略采样、没有新SLSQP/交替优化、没有改参数或正式求解器。结论仍待用户审阅；不是论文第三章新增均衡定理的授权。

## 实际执行及复核命令

在项目根目录，Python 3.11.7，沿用NumPy/SymPy；整数分数运算使用标准库fractions，无新依赖安装：

```powershell
python -B work_e_r1/scripts/register.py
python -B work_e_r1/scripts/certify_bounds.py
python -B work_e_r1/scripts/certify_rk4_error.py
python -B work_e_r1/scripts/verify_derivatives.py
python -B work_e_r1/scripts/verify_certificates.py
python -B work_e_r1/scripts/certify_candidate_vi.py
python -B work_e_r1/scripts/check_candidate_gap.py
```

上列为最终可复核脚本流程。实际首次结构界计算先取得十进制证书，binary64精确分数序列化超限后修复继续；不是模型/数值失败重跑。register校验Work E封存哈希及原来源，确认前序辅助运算未改任何保护文件。初步曲率界曾用普通浮点作公式代入探索，其数值未当证书；最终认证均由有理数不等式决定。

只复核、避免覆盖原始计算：

```powershell
python -B work_e_r1/scripts/verify_derivatives.py
python -B work_e_r1/scripts/verify_certificates.py
python -B work_e_r1/scripts/check_candidate_gap.py
python -B work_e_r1/scripts/verify_delivery.py
```

验证脚本重写自己的通过记录；数据与理论文件不变。SHA256SUMS封存本次最终文件；重新运行带计时的计算脚本可能改变哈希，须先保留原包，再比较新的精确结果。不要把重新执行命令描述为已经发生的复现。

## 核心结果

- B中攻击强凹（5/3）及唯一全局攻击响应严格证明完成。
- 防御只认证-65I全域下界，没有证明凸性，也没有负曲率反例。
- 存在/唯一定理为条件性，实际防御条件未闭合。
- 已证C0与B的全域目标误差上界；C0表示精确算术RK4公式，机器舍入和全域状态保护另列未证。
- 一个严格可行副本获得C0线性VI gap<6.9658700e−5的区间证书，未成为B的Nash误差界。

## 证据与恢复

source_manifest.json保护1185个原文件（含Work E的83个文件）。run_config.json固定所有系数、对象及本轮零随机/零优化范围。双参数解释证书区分十进制与binary64作为精确实数，避免把数值存储精度隐去。

serialization_failure01.json公开大分数序列化限制；candidate_VI_before_capacity_audit.json保留首次较小LP域的结果，最终gap已用完整原容量域复核。所有状态、梯度区间和LP见candidate_VI_interval_certificate.json。没有更换正式候选；仅供数学认证的可行副本修复量<3.488e−16。

最终文件哈希和源文件无变更检查见delivery_checks.json、SHA256SUMS。它们和有理算术检查不等于形式化证明助手或外部审查。
