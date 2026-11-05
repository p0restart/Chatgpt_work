"""Render descriptive G1-C1 audit tables without inferring human approval."""
import argparse
import json
from pathlib import Path
import pandas as pd


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();root=Path(args.root)
    audit=json.loads((root/'audit.json').read_text());meta=json.loads((root/'metadata.json').read_text())
    effects=pd.read_csv(root/'robust_effects.csv');summary=pd.read_csv(root/'summary.csv')
    allocations=pd.read_csv(root/'source_allocations.csv')
    capacity=pd.read_csv(root/'capacity_summary.csv').merge(summary[['case','seed','B']],on='case',validate='many_to_one')
    out=['# G1-C1 匹配网络机制验证：数值报告','',
         '## Material Passport','',
         '- Origin Skill: academic-research-suite / experiment-agent',
         '- Origin Mode: run', '- Origin Date: 2026-10-27',
         '- Verification Status: ANALYZED（保存控制已重新积分；独立复跑另见复现文件）',
         '- Version Label: matched_mechanism_v1','',
         '## 范围与执行状态','',
         f"数据目录：`{root.as_posix()}`。执行状态：`{meta['status']}`；完成{len(summary)}/36配置；累计{meta['seconds']:.1f}秒。",
         'G1-C1已获用户批准；G2仍PENDING。所有结果仅限固定6节点、K=6、T=10、零终端损失的合成模型与局部响应候选。',
         '各四格组固定入口、初始条件、入边和路径距离；总价值及总传播权重相同。只改变2/3出强度分配及高价值位置。','',
         '## 数值核验','', '|检查|结果|','|---|---:|']
    for key,label in [('numerical_pass_count','数值门槛通过配置数'),('relative_improvement_max','最大相对观测改善'),
                      ('incumbent_residual_max','当前策略最大投影残差'),
                      ('initialization_control_difference_max','三初值两两控制最大差'),
                      ('integration_control_difference_max','12→48子步再优化控制最大差'),
                      ('integration_max_error','12对48子步目标最大误差'),
                      ('reintegration_max_error','保存控制重新积分最大差'),
                      ('budget_max_violation','逐槽最大预算违规'),('optimizer_runs','记录的优化调用数'),
                      ('all_optimizer_success','全部记录优化器成功'),('feasible_transfers','可行资源转移核验数'),
                      ('transfer_max_error','转移导数最大有限差分误差'),
                      ('source_hashes_match','运行后输入及源码哈希一致'),('states_in_domain','重新积分状态均在[0,1]')]:
        v=audit[key];out.append(f'|{label}|{v:.9g}|' if isinstance(v,float) else f'|{label}|{v}|')
    reproduction=root/'pilot_reproduction.json'
    if reproduction.exists():
        rep=json.loads(reproduction.read_text())
        out += ['', f"首组四格在同一运行环境独立复跑，共{rep['comparisons']}组控制比较，最大差{rep['max_control_difference']:.9g}。这不是全36配置独立复跑，也不是全新环境复现。"]
    out += ['', '相对观测改善不是未知全局gap的上界。多初值、局部残差、稀疏起点和积分精化不能证明全局Nash，也未完成K槽精化。',
            '', '## 四格交互效应（逐种子、逐预算）','',
            '`DID = (不等出强度下：高价值在3 − 高价值在2) − (等出强度下：高价值在3 − 高价值在2)`。',
            '表中为时间窗内平均控制变化；s为隔离、r为恢复。正负号为预先定义的差值方向，不能直接解释为成本好坏。',
            '工程分辨率为绝对平均差>0.001；不是统计显著性。完整等/不等价值效应、积分差和四初值/积分版本见paired_effects.csv。']
    for window,label in [('all','全6槽'),('first4','前4槽'),('last2','末2槽')]:
        out += ['',f'### {label}','', '|seed|B|s2 DID|s3 DID|r2 DID|r3 DID|稳健超分辨率通道|','|---:|---:|---:|---:|---:|---:|---|']
        for (seed,budget),group in effects[effects.window==window].groupby(['seed','B']):
            values={(r.kind,r.node):r.interaction for r in group.itertuples()}
            channels=','.join(f'{r.kind}{r.node}' for r in group.itertuples() if r.robust_resolved) or '无'
            out.append(f'|{seed}|{budget}|'+ '|'.join(f'{values[k]:.7f}' for k in [('s',2),('s',3),('r',2),('r',3)])+f'|{channels}|')
    out += ['',f"三初值与积分精化造成的DID最大跨度：{audit['interaction_uncertainty_max']:.7g}。稳健通道要求四版本同号、均超分辨率且跨度≤0.001，同时该四格组数值检查通过。",'',
            '## 源节点实际投入（48子步候选，全时域平均）','',
            '|seed|B|出强度|高价值位置|s2|s3|r2|r3|','|---:|---:|---|---|---:|---:|---:|---:|']
    for r in summary.itertuples():
        a=allocations[(allocations.case==r.case)&(allocations.initialization=='fine')&(allocations.window=='all')]
        values={(x.kind,x.node):x.average for x in a.itertuples()}
        out.append(f'|{r.seed}|{r.B}|{r.outgoing}|{r.value}|'+ '|'.join(f'{values[k]:.7f}' for k in [('s',2),('s',3),('r',2),('r',3)])+'|')
    out += ['', '全部源节点积分投入在source_allocations.csv；每槽投入在各fine_evaluation/controls.csv。',
            '', '## 容量是否实际绑定','',
            '下表为四格中绑定槽数的最小—最大值。控制变化本身不能证明容量竞争；预算有余量的时段单独解释。',
            '', '|seed|B|前4槽绑定数范围|末2槽绑定数范围|','|---:|---:|---:|---:|']
    for (seed,budget),group in capacity.groupby(['seed','B']):
        early=group[group.window=='first4'].binding_slots
        late=group[group.window=='last2'].binding_slots
        out.append(f'|{seed}|{budget}|{early.min()}—{early.max()}|{late.min()}—{late.max()}|')
    out += ['', '## 固定攻击与局部响应攻击的成本','',
            '保持同一最终防御，固定攻击为每入口0.4；局部响应攻击来自3起点48子步攻击优化。攻击者目标与防御损失非零和，攻击响应不保证提高J_D。',
            '', '|配置|固定攻击 J_D|局部响应攻击 J_D|','|---|---:|---:|']
    for r in summary.itertuples():
        out.append(f'|{r.case}|{r.fixed_attack_J_D:.7f}|{r.strict_response_attack_J_D:.7f}|')
    out += ['', '## 边际资源转移与证据边界','',
            'marginals.csv记录每槽每节点隔离/恢复的梯度、直接成本导数、安全收益导数和单位容量净收益；source_transfers.csv记录s2/s3/r2/r3之间全部有向转移。',
            '不可行转移单独标记，不能拿形式方向导数当可行改进。局部解上活跃控制的边际收益可能相等；本实验的四格效应来自参数干预，不等同于求解后仍可获益的资源挪动。',
            '不得将控制投入大小排序、末期下降或四格交互自动命名为优先级切换定理。数值为零、方向不一致、仅末期出现的通道都保留。',
            '', '## 复现与数据入口','',
            '```powershell',
            'python -m pytest -q',
            'python -m src.matched_mechanism --output results/matched_mechanism/reproduce_full',
            'python -m src.audit_matched --root results/matched_mechanism/reproduce_full',
            'python -m src.report_matched --root results/matched_mechanism/reproduce_full --output reports/MATCHED_MECHANISM_REPRODUCED.md',
            '```','',
            '若运行在四格组边界达到30分钟分段限制，先执行`python -m src.resume_matched --root results/matched_mechanism/reproduce_full`完成剩余组，再执行审计和报告命令；该命令仅接受纯时间停止，不重试失败组。',
            '数据包括完整model.json、边表、参数、源码快照与哈希、优化初末控制/退出码/残差、轨迹、预算、积分精化、四格差值和重新积分审计。原P2/P3/P4及负结果不覆盖。',
            'Python与依赖版本见metadata.json；本环境pytest为7.4.0，仍与原requirements>=8不符，未隐去。',
            '是否接受有限机制主张以及是否允许最终论文合稿，应由更新的G2审查包明确审批。']
    Path(args.output).write_text('\n'.join(out)+'\n',encoding='utf-8')


if __name__=='__main__':main()
