"""D5-P0: extract frozen C2 plans and replay their payoff matrix; no optimization."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.core import Model, simulate, check_controls

C2 = ROOT / 'results/supplement_c2/run02'
METHODS = {'G': 'Joint-dynamic', 'F': 'Fixed-trained'}
SEEN = {}


def read(path):
    path = Path(path)
    data = path.read_bytes()
    SEEN[path] = hashlib.sha256(data).hexdigest()
    return data.decode('utf-8-sig')


def js(path):
    return json.loads(read(path))


def csv(path):
    return pd.read_csv(io.StringIO(read(path)), float_precision='round_trip')


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def controls(path):
    df = csv(path)
    assert len(df) == 36 and not df.duplicated(['slot', 'node']).any()
    return tuple(df.pivot(index='slot', columns='node', values=x).to_numpy() for x in ('a', 's', 'r'))


def md(df, digits=6):
    def f(x):
        return f'{x:.{digits}g}' if isinstance(x, (float, np.floating)) else str(x)
    return '\n'.join(['|'+'|'.join(map(str, df.columns))+'|', '|'+'|'.join(['---']*len(df.columns))+'|'] +
                     ['|'+'|'.join(f(x) for x in row)+'|' for row in df.itertuples(index=False, name=None)])


def extrema(df, col):
    return f'{df[col].min():.6g}–{df[col].max():.6g}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='reports/work_d5/p0/run01')
    args = ap.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    # Protect relevant source material, without changing its status or approval record.
    for p in [ROOT/'AGENTS.md', ROOT/'DECISIONS.md', ROOT/'02_MODEL_SPEC.md',
              ROOT/'reviews/APPROVAL_LOG.md', ROOT/'reports/SUPPLEMENT_C2_PROTOCOL.md',
              ROOT/'reports/C2_FINDINGS.md', ROOT/'reports/mathematical_audit.md',
              ROOT/'reports/work_t1/T1_equilibrium_provability_review_zh.md',
              ROOT/'paper/work_t1/T1_proofs_zh.md', ROOT/'handoffs/C2_robustness.md',
              ROOT/'reviews/G_D4_direction_20261112_submission.md',
              ROOT/'src/core.py', ROOT/'src/supplement_c2.py', ROOT/'src/game_solver.py',
              ROOT/'src/experiments.py', Path(__file__)]:
        read(p)
    for folder in ['paper/work_d3', 'paper/work_d1', 'paper/work_d2']:
        for p in (ROOT/folder).glob('*.md'):
            read(p)
    original_manifest = js(C2/'manifest.json')
    original_hashes = {(C2/x['path']).resolve(): x['sha256'] for x in original_manifest}
    old_core_path = C2/'source_snapshot/core.py'
    read(old_core_path)
    spec = importlib.util.spec_from_file_location('d5_c2_original_core', old_core_path)
    old_core = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old_core
    spec.loader.exec_module(old_core)
    all_d, all_a, all_pay, all_b, all_q, all_raw, summaries, checks = [], [], [], [], [], [], [], []
    traces = []
    delta_reports = []
    for seed in (11, 22, 33):
        for B in (.6, 1.2, 1.8):
            case = f'seed{seed}_B{B}_unequal_high_at_node3'
            p = C2/'comparison'/case
            d = js(p/'model.json')
            cfg = js(p/'config.json')
            inputs = js(p/'inputs.json')
            assert d['B'] == B and cfg['K'] == 6 and cfg['T'] == 10
            assert hashlib.sha256((p/'model.json').read_bytes()).hexdigest() == inputs['model_sha256']
            m = Model(**{k: np.array(v, dtype=bool if k == 'entry' else float) if isinstance(v, list) else v for k, v in d.items()})
            T, K, dt = cfg['T'], cfg['K'], cfg['T']/cfg['K']
            assert m.n == 6 and np.array_equal(np.flatnonzero(m.entry), [0, 1])
            assert np.all(m.b_s == 1) and np.all(m.b_r == 1) and np.all(m.d_a == 1)
            plans, common, audits, saved = {}, {}, {}, {}
            for key, method in METHODS.items():
                plans[key] = controls(p/f'{method}_adaptive_attack/controls.csv')
                common[key] = controls(p/f'{method}_common_fixed_attack/controls.csv')
                assert max(np.max(abs(plans[key][j]-common[key][j])) for j in (1, 2)) < 1e-14
                audits[key] = js(p/f'{method}_evaluation_audit.json')
                for ev in ('adaptive_attack', 'common_fixed_attack'):
                    saved[key, ev] = js(p/f'{method}_{ev}/summary.json')
                    csv(p/f'{method}_{ev}/refinement.csv')
                    csv(p/f'{method}_{ev}/budgets.csv')
            assert np.array_equal(common['G'][0], common['F'][0])
            a0 = common['F'][0]
            assert np.all(a0[:, :2] == .4) and np.all(a0[:, 2:] == 0)
            source = ROOT/inputs['joint_source']
            source_model = js(source/'model.json')
            assert source_model == d
            old_u = tuple(np.array(v) for v in js(source/'fine/controls.json'))
            source_diff = max(float(np.max(abs(old_u[j]-plans['G'][j]))) for j in (1, 2))
            assert source_diff < 1e-14
            ft = js(p/'Fixed-trained_response.json')
            # Saved response controls are reconstructed from the selected optimizer return.
            for key in METHODS:
                ai = audits[key]['A']
                raw_controls = [np.array(x['control']) for x in ai['raw']]
                selected = [x for x in ai['raw'] if x['accepted']]
                selected_a = np.array(selected[-1]['control']).reshape(K, 2) if selected else old_u[0][:, :2]
                assert np.max(abs(selected_a-plans[key][0][:, :2])) < 1e-14
                assert len(ai['raw']) == 3 and ai['success']
                assert abs(-ai['objective']-saved[key, 'adaptive_attack']['J_A']) < 1e-11
                for role, info in [('A', ai), ('D_at_own_response', audits[key]['D'])]:
                    vals = [x['objective'] for x in info['raw']]
                    arr = [np.array(x['control']) for x in info['raw']]
                    all_q.append(dict(case=case, method=METHODS[key], role=role,
                        objective=info['objective'], residual=info['residual'],
                        incumbent_residual=info['incumbent_residual'], violation=info['violation'],
                        success=info['success'], starts=len(vals), objective_spread=float(np.ptp(vals)),
                        control_spread=max(float(np.max(abs(x-y))) for x in arr for y in arr),
                        signed_D_improvement=saved[key, 'adaptive_attack']['J_D']-info['objective'] if role.startswith('D') else 0.))
                    for r in info['raw']:
                        all_raw.append(dict(case=case, method=METHODS[key], role=role, **r))
            chosen = [x for x in ft['raw'] if x['accepted']][-1]
            fd = np.array(chosen['control']).reshape(K, 12)
            assert np.max(abs(fd[:, :6]-plans['F'][1])) < 1e-14
            assert np.max(abs(fd[:, 6:]-plans['F'][2])) < 1e-14
            assert abs(ft['objective']-saved['F', 'common_fixed_attack']['J_D']) < 1e-11
            for r in ft['raw']:
                all_raw.append(dict(case=case, method=METHODS['F'], role='D_training_common', **r))
            all_q.append(dict(case=case, method=METHODS['F'], role='D_training_common',
                objective=ft['objective'], residual=ft['residual'], incumbent_residual=ft['incumbent_residual'],
                violation=ft['violation'], success=ft['success'], starts=len(ft['raw']),
                objective_spread=float(np.ptp([r['objective'] for r in ft['raw']])),
                control_spread=max(float(np.max(abs(np.array(x['control'])-np.array(y['control'])))) for x in ft['raw'] for y in ft['raw']),
                signed_D_improvement=saved['F', 'common_fixed_attack']['J_D']-ft['objective']))
            local_pay = {}
            attacks = {'a0': a0, 'aG': plans['G'][0], 'aF': plans['F'][0]}
            for key in METHODS:
                for alabel, a in attacks.items():
                    u = (a, plans[key][1], plans[key][2])
                    check_controls(m, *u)
                    coarse = simulate(m, *u, T, 48)
                    fine = simulate(m, *u, T, 192)
                    original = old_core.simulate(m, *u, T, 48)
                    error = max(abs(coarse[x]-fine[x]) for x in ('J_D', 'J_A'))
                    drift = max(abs(coarse[x]-original[x]) for x in ('J_D', 'J_A'))
                    assert drift < 1e-12
                    ev = 'common_fixed_attack' if alabel == 'a0' else 'adaptive_attack' if alabel == 'a'+key else 'cross_response'
                    saved_error = max(abs(fine[x]-saved[key, ev]['fine_'+x]) for x in ('J_D', 'J_A')) if ev != 'cross_response' else 0.
                    assert saved_error < 1e-11
                    row = dict(case=case, seed=seed, B=B, defense=key, attack=alabel,
                               evaluation=ev, J_D=fine['J_D'], J_A=fine['J_A'], **fine['parts'],
                               error_48_192=error, original_core_error=drift, saved_fine_error=saved_error)
                    all_pay.append(row); local_pay[key, alabel] = row
                    traces.extend(dict(case=case, defense=key, attack=alabel, t=float(t),
                                       **{f'x{i}': float(v) for i, v in enumerate(x)}) for t, x in zip(fine['times'], fine['states']))
                    for k in range(K):
                        du = float(u[1][k]@m.b_s+u[2][k]@m.b_r); au = float(a[k]@m.d_a)
                        all_b.append(dict(case=case, defense=key, attack=alabel, slot=k,
                            defense_use=du, defense_slack=B-du, attack_use=au, attack_slack=m.A-au))
            gs, gr = plans['G'][1:]; fs, fr = plans['F'][1:]
            ds, dr = gs-fs, gr-fr
            da = plans['G'][0]-plans['F'][0]
            slot_l1 = (abs(ds)*m.b_s+abs(dr)*m.b_r).sum(axis=1)
            rows_case = []
            for k in range(K):
                for i in range(m.n):
                    row = dict(case=case, seed=seed, B=B, slot=k, t_start=k*dt, t_end=(k+1)*dt,
                        node=i, s_G=gs[k,i], s_F=fs[k,i], delta_s=ds[k,i],
                        r_G=gr[k,i], r_F=fr[k,i], delta_r=dr[k,i])
                    all_d.append(row); rows_case.append(row)
                    for alabel, a in attacks.items():
                        total = float(a[k].sum())
                        all_a.append(dict(case=case, slot=k, t_start=k*dt, t_end=(k+1)*dt,
                            node=i, attack=alabel, a=a[k,i], entry=bool(m.entry[i]),
                            share=a[k,i]/total if total else 0., attack_total=total,
                            dominant_node=int(np.argmax(a[k]))))
            D = lambda key, a: local_pay[key, a]['J_D']
            A = lambda key, a: local_pay[key, a]['J_A']
            advantage = D('F','aF')-D('G','aG')
            common_effect = D('F','a0')-D('G','a0')
            exposure_F = D('F','aF')-D('F','a0')
            exposure_G = D('G','aG')-D('G','a0')
            assert abs(advantage-(common_effect+exposure_F-exposure_G)) < 1e-12
            gain_G = A('G','aG')-A('G','aF'); gain_F = A('F','aF')-A('F','aG')
            assert min(gain_G, gain_F) > -1e-10
            summaries.append(dict(case=case, seed=seed, B=B,
                max_abs_delta_s=float(abs(ds).max()), max_abs_delta_r=float(abs(dr).max()),
                mean_slot_defense_L1=float(slot_l1.mean()), defense_L1_percent_of_B=float(100*slot_l1.mean()/B),
                half_L1_percent_of_B=float(50*slot_l1.mean()/B),
                mean_use_G=float((gs@m.b_s+gr@m.b_r).mean()),mean_use_F=float((fs@m.b_s+fr@m.b_r).mean()),
                isolation_change_time_integral=float(dt*ds.sum()), recovery_change_time_integral=float(dt*dr.sum()),
                max_abs_delta_attack=float(abs(da).max()),
                attack_total_change_time_integral=float(dt*da.sum()),
                dominant_attack_changed_slots=int(np.sum(np.argmax(plans['G'][0],axis=1)!=np.argmax(plans['F'][0],axis=1))),
                s_dominant_changed_slots=int(np.sum(np.argmax(gs,axis=1)!=np.argmax(fs,axis=1))),
                r_dominant_changed_slots=int(np.sum(np.argmax(gr,axis=1)!=np.argmax(fr,axis=1))),
                active_s_changed=int(np.sum((gs>1e-3)!=(fs>1e-3))),
                active_r_changed=int(np.sum((gr>1e-3)!=(fr>1e-3))),
                own_response_D_advantage=advantage,
                own_response_D_advantage_percent=100*advantage/D('F','aF'),
                common_D_advantage=common_effect,common_D_advantage_percent=100*common_effect/D('F','a0'),
                exposure_F=exposure_F,exposure_G=exposure_G,
                attacker_gain_G_own_vs_cross=gain_G,attacker_gain_F_own_vs_cross=gain_F,
                attacker_gain_G_own_vs_a0=A('G','aG')-A('G','a0'),
                attacker_gain_F_own_vs_a0=A('F','aF')-A('F','a0'),
                source_defense_error=source_diff))
            detail = pd.DataFrame(rows_case)
            sections = [f'## {case}', '\n节点和时槽从0编号，T=10、Δt=5/3；每个单元为 G / F / (G−F)。',
                        '\n### 隔离 s', matrix(gs, fs), '\n### 恢复 r', matrix(gr, fr),
                        '\n### 攻击投入（仅入口0、1；其余严格为0）',
                        md(pd.DataFrame([dict(slot=k, aG_0=attacks['aG'][k,0],aG_1=attacks['aG'][k,1],
                           aF_0=attacks['aF'][k,0],aF_1=attacks['aF'][k,1],a0_0=.4,a0_1=.4) for k in range(K)])),
                        '\n### 六个冻结计划配对的双方目标',
                        md(pd.DataFrame(list(local_pay.values()))[['defense','attack','evaluation','J_D','J_A']]),
                        '\n### 逐槽投入总量',
                        md(pd.DataFrame([dict(slot=k,s_G=gs[k].sum(),s_F=fs[k].sum(),r_G=gr[k].sum(),r_F=fr[k].sum(),
                            use_G=gs[k].sum()+gr[k].sum(),use_F=fs[k].sum()+fr[k].sum(),L1=slot_l1[k]) for k in range(K)]))]
            delta_reports.append('\n\n'.join(sections))
            checks.append(dict(case=case, model_equal=True, defense_frozen=True,
                               common_attack_equal=True, raw_response_reconstructed=True, source_defense_error=source_diff))
            print(f'AUDITED {case}', flush=True)
    dfs = {'defense_by_node_slot': pd.DataFrame(all_d), 'attack_by_node_slot': pd.DataFrame(all_a),
           'payoff_matrix': pd.DataFrame(all_pay), 'budgets': pd.DataFrame(all_b),
           'response_quality': pd.DataFrame(all_q), 'case_summary': pd.DataFrame(summaries)}
    for name, df in dfs.items():
        df.to_csv(out/f'{name}.csv',index=False)
    pd.DataFrame(traces).to_csv(out/'replayed_states_192.csv',index=False)
    write_json(out/'optimizer_returns.json', all_raw)
    write_json(out/'case_checks.json',checks)
    (out/'all_nine_cases_zh.md').write_text('# 九配置逐节点、逐时槽完整对照\n\n'+ '\n\n'.join(delta_reports),encoding='utf-8')
    write_report(out, dfs)
    mismatches = []
    legacy_checked = 0
    sources = []
    for p, digest in SEEN.items():
        after = hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest == after, f'Input changed: {p}'
        legacy = original_hashes.get(p.resolve())
        if legacy:
            legacy_checked += 1
            if legacy != digest:
                mismatches.append(str(p.relative_to(ROOT)))
        sources.append(dict(path=str(p.relative_to(ROOT)), sha256=digest, bytes=p.stat().st_size,
                            matches_original_C2_manifest=legacy == digest if legacy else None))
    assert not mismatches
    write_json(out/'source_manifest.json', sources)
    quality = dfs['response_quality']
    pay = dfs['payoff_matrix']
    write_json(out/'verification.json', dict(status='PASS', analysis='extraction_and_fixed_plan_replay_only',
        starts_per_saved_response=3, new_optimizer_calls=0, cases=9, strategy_pairs=54,
        original_C2_manifest_entries_checked=legacy_checked, original_C2_manifest_mismatches=mismatches,
        protected_inputs=len(SEEN), protected_inputs_unchanged=True,
        defense_rows=len(all_d), attack_rows=len(all_a), budget_rows=len(all_b),
        historical_optimizer_returns=len(all_raw), all_saved_optimizers_success=bool(quality.success.all()),
        max_saved_response_residual=float(quality.residual.max()),
        max_replay_error_48_192=float(pay.error_48_192.max()),
        max_original_core_difference=float(pay.original_core_error.max()),
        max_saved_192_replay_difference=float(pay.saved_fine_error.max()),
        continuous_global_certificate=False))
    write_json(out/'metadata.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),
        date_Asia_Shanghai='2026-11-13',python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
        platform=platform.platform(),source=str(C2.relative_to(ROOT)),
        command=f'python reports/work_d5/analysis/audit_decision_difference.py --output {args.output}',
        optimization='not_run; historical seed and returns retained',
        G1_G2='No model or strategy class change; no approval asserted; no downstream manuscript revision'))
    write_json(out/'output_manifest.json',[dict(path=str(p.relative_to(out)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                              bytes=p.stat().st_size) for p in sorted(out.iterdir()) if p.is_file()])
    print(dfs['case_summary'].to_string(index=False),flush=True)


def matrix(g, f):
    return md(pd.DataFrame([{'slot': k, **{f'node{i}':f'{g[k,i]:.6f} / {f[k,i]:.6f} / {g[k,i]-f[k,i]:+.6f}'
                                         for i in range(6)}} for k in range(6)]))


def write_report(out, dfs):
    s, p, q = dfs['case_summary'], dfs['payoff_matrix'], dfs['response_quality']
    rep = 'seed11_B1.2_unequal_high_at_node3'
    sr = s[s.case == rep].iloc[0]
    own = s[['seed','B','max_abs_delta_s','max_abs_delta_r','defense_L1_percent_of_B',
             'max_abs_delta_attack','own_response_D_advantage','own_response_D_advantage_percent','common_D_advantage_percent']]
    rp = p[p.case == rep][['defense','attack','evaluation','J_D','J_A']]
    d = dfs['defense_by_node_slot']; rd = d[d.case==rep]
    node = rd.groupby('node')[['s_G','s_F','r_G','r_F','delta_s','delta_r']].sum()*(10/6)
    node = node.reset_index()
    ar = dfs['attack_by_node_slot']; ar = ar[(ar.case==rep)&(ar.node<2)]
    attack_integral = ar.groupby(['attack','node']).a.sum().unstack()*10/6
    text = f'''# Work D5-P0：攻防博弈与固定攻击优化的决策差异审计

## Material Passport

- 日期：2026-11-13（Asia/Shanghai）；来源：`results/supplement_c2/run02/comparison`。
- 状态：ANALYZED；保存策略收益重放 VERIFIED（见 verification.json），未重新优化；本报告为同一执行者审计，不是外部独立评审。
- 范围：原 C2 预先指定的 unequal/high_at_node3，seed11/22/33 × B0.6/1.2/1.8，共9组同场景配对。每对的模型、初态、入口、容量、T=10、K=6相同；跨种子网络不同，不能合成一张图。未将 Work-C2 的 K=12 四格稳健性数据混入此方法比较。
- 当前授权仅完成三项审计。模型、历史结果、D3、人工审批不改；D4新参数实验及论文定向审批仍保持原状态。本报告完成不等于用户接受新结论，不进入受限下游写作。

## 1. 直接判断

**现有证据体现了有限、可测的战略相互依赖，并且确实改变防御配置；影响以局部资源微调为主，九组防御目标改善均低于原定1%工程描述门槛。**不能据此称博弈求解对这些实例的防御决策必不可少，也不能把动态隔离/恢复配置本身归因于博弈独有机制。

这里有两个不同命题。第一，“防御计划变化后，攻击者是否改变最优响应？”可以固定计划，提取两条响应并交叉评价。第二，“考虑对方响应是否带来很大的防御收益？”应看防御配置距离和收益幅度。两者不能用“有博弈方程”或“存在PMP/KKT”替代检验。

## 2. 两类防御如何产生，哪些攻击相同

记 G=Joint-dynamic，F=Fixed-trained，u=(s,r)。G来自既有交替局部响应候选；F在公共恒定攻击 a0 下求防御局部最优响应。a0在每槽入口0、1各投入0.4，其余节点为0，A=0.8。F也有六槽动态隔离和恢复；两者的动态能力、行动类型与预算约束相同。

固定两种防御后，C2分别保存三起点攻击响应 aG≈BR_A(uG)、aF≈BR_A(uF)。本次不改防御、不重训、不重求攻击，直接重构保存优化器返回值并核对逐分量一致性。“最佳响应”在数据层均指已保存的局部数值响应，非已获精确全局证书。

|对照|防御|攻击|可解释的内容|
|---|---|---|---|
|公共固定评价|uG vs uF|两边严格相同 a0|对固定均分攻击假设的适配；不含攻击调整|
|各自响应评价|uG vs uF|分别 aG、aF|在各自攻击响应下的结果；两边攻击不同|
|公共响应轨迹交叉评价|uG vs uF|两边严格相同 aG，或严格相同 aF|在一个已保存攻击轨迹下改变防御的效果|
|攻击自身的偏离比较|同一个 uG 或 uF|aG vs aF，或各自响应 vs a0|防御冻结后攻击调整的价值|

最后两项只是对同一保存计划的算术交叉评价，不是新增攻击情景，也不构造新均衡。G的同时行动开环候选不等于防御者预见响应映射后求解的Stackelberg计划；不能据此宣布G全局最小化了 J_D(u,BR_A(u))。

## 3. 逐节点、逐时槽的防御差异

完整324行防御对照见 `defense_by_node_slot.csv`。`all_nine_cases_zh.md` 为每组列出六槽×六节点的 s、r 原值与差值，单元顺序 G/F/(G−F)。节点、时槽均从0编号，每槽长度5/3。投入为无量纲控制，时间积分不是费用；费用由平方行动成本与业务项另算。

下表覆盖全部9组。`max_abs_delta_s/r` 为36个分量中的最大绝对变化；防御 L1 比例是 100×六槽平均 Σ_i(b_s|Δs|+b_r|Δr|)/B。它既包含节点/行动间重新配置，也包含总用量变化；不是“有这么多资源被搬走”。只有总用量相等时，L1的一半才等于搬移量。`max_abs_delta_attack` 为两条各自响应的最大分量差。

{md(own)}

每组最大隔离变化为 **{extrema(s,'max_abs_delta_s')}**，最大恢复变化为 **{extrema(s,'max_abs_delta_r')}**；平均槽防御L1/B为 **{extrema(s,'defense_L1_percent_of_B')}%**。这些差异远大于本次读取精度及已保存三起点优化返回控制分散，但不是连续控制最优计划间距离的严格界。

按1e−3作为显示活跃控制的描述分辨率（不是新验收门槛），隔离活跃分量变化总数为{s.active_s_changed.sum()}，恢复为{s.active_r_changed.sum()}；隔离最大投入节点变化{s.s_dominant_changed_slots.sum()}个槽，恢复变化{s.r_dominant_changed_slots.sum()}个槽。近零分量、并列与微小差异须结合原值阅读，不能仅靠最大值节点推断普适优先级切换。

为便于阅读，以下固定展示seed11、中容量B1.2，不按改善率挑选；全部其他配置均在附表。其逐节点时间积分如下（G−F正表示增加）：

{md(node)}

该例原值和逐槽方向均可在完整对照中核查。全时积分会掩盖同一节点早晚方向相反的变化，因此不以该表代替逐槽对照。

## 4. 攻击目标、投入与双方目标

9组中，直接攻击始终只允许入口0、1，其余4个节点的直接攻击严格为0；高价值节点3受传播影响，不能把它称作已被攻击者直接选中的入口。两种防御下入口0、1的响应投入均为正，目标集合不变。攻击最大投入节点在两种防御之间改变的槽数为 **{s.dominant_attack_changed_slots.sum()}/54**。因此证据主要是既有入口间强度及时间安排的调整，不是创造新目标、改变入口集或大规模改换攻击路径。

两条响应的逐分量最大差各组为 **{extrema(s,'max_abs_delta_attack')}**。完整972行（9组×3条攻击×6槽×6节点）见 `attack_by_node_slot.csv`，含各槽总量、份额、入口标记及最大投入节点；它也显示末段可不耗尽A，不能假定每条攻击始终满预算。

seed11/B1.2攻击强度的时间积分：

{md(attack_integral.reset_index())}

这与a0的每个入口积分4.0分开；aG与aF的相互差异才是防御计划变化引发的响应变化，不能把a0→最佳响应的全部变化归因于uF→uG。

该例双方目标全矩阵如下。J_D是防御损失，越小越好；J_A是攻击收益，越大越好，两者单位可能不同，禁止相减作为社会收益。F防御者效用若需写为收益则是−J_D。

{md(rp)}

攻击者在同一防御下采用自身响应，相对另一防御对应的响应，J_A改善分别为：uG上 **{extrema(s,'attacker_gain_G_own_vs_cross')}**，uF上 **{extrema(s,'attacker_gain_F_own_vs_cross')}**。逐组均为正。这是最直接的数值战略依赖证据：两条攻击计划不可完全互换；它们对各自防御的适配有非零价值。改善幅度小，不支持“攻击战略发生根本改变”。相对a0的攻击收益改善另列case_summary.csv，不能混同这项交叉差值。

## 5. 防御收益有多大，差值由什么组成

各自响应下，G相对F的防御损失降低 **{extrema(s,'own_response_D_advantage')}**，相对降低 **{extrema(s,'own_response_D_advantage_percent')}%**，中位数 **{s.own_response_D_advantage_percent.median():.6g}%**。9/9正向、0/9达到预登记1%工程描述门槛。公共a0下，G的相对降低为 **{extrema(s,'common_D_advantage_percent')}%**，9/9反向，表明固定攻击训练确实更适合其训练攻击。

令 Δown=J_D(uF,aF)−J_D(uG,aG)，Δ0=J_D(uF,a0)−J_D(uG,a0)，E_F=J_D(uF,aF)−J_D(uF,a0)，E_G同理，则有精确算术恒等式：

Δown = Δ0 + E_F − E_G。

seed11/B1.2为 **{sr.own_response_D_advantage:.9f} = {sr.common_D_advantage:.9f} + {sr.exposure_F:.9f} − {sr.exposure_G:.9f}**。全9组分解见case_summary.csv。这是对冻结策略收益的分解，不是加性因果机制识别。攻击者最大化J_A，不是J_D；因此各自响应未必是防御损失的最坏攻击，E的正负也不能预设为非负。

局部投入变化可以达到若干百分点，而总损失变化仍小：目标积分了全网安全损失、业务损失与行动成本；投入方向变化不与目标改善一一对应。`payoff_matrix.csv`保存每个配对的所有成本分项，不从少量投入差异反推重要性。

## 6. PMP/KKT、偏离审计分别支持什么

原数学审计给出 ∂H_D/∂s_i=h_i+c_i^s s_i−M_i^s，∂H_D/∂r_i=c_i^r r_i−M_i^r；M_i^s=ε_i x_i Σ_j β_ij(1−x_j)p_j^D，M_i^r=γ_i x_i p_i^D。攻击边际为 α_i(1−x_i)p_i^A−c_i^a a_i。攻击改变状态和伴随，从而改变防御边际；防御改变状态及攻击伴随，从而改变攻击边际。预算乘子再联结同一槽的资源配置。这给出结构上的相互依赖解释。

但固定a0的防御优化同样满足其单方PMP/KKT，同样产生动态、异质配置。瞬时Hamiltonian的严格凸/凹、clip形式与单方驻点不能单独证明战略价值、全局最优或Nash。六槽直接射击必须使用槽积分梯度条件，不能将连续时间逐点clip当作已实现求解器；本次也未声称重算了连续伴随或新增PMP验证。

本次提取原始优化返回：9组×(G的A/D响应、F的A/D响应、F对a0训练)共45组，每组3起点、共135条返回，含退出码、每个起点控制、目标和残差，见optimizer_returns.json与response_quality.csv。所有保存调用成功；最大返回点投影残差 **{q.residual.max():.6g}**。G在自身攻击响应下的防御当前点残差与可发现改善用于检查局部候选；F在a0下满足训练响应诊断，在aF下可发现防御改善并不构成失败，因为F没有训练应对aF。不能要求F自动满足博弈候选条件，也不能将G的很小已发现改善升级为全局gap上界。

T1进一步提出精确ODE攻击目标严格凹、最佳响应唯一的证明稿。该证明尚是同一执行者推导、未获外部或形式化验证；即使接受它，也需连接精确目标与RK4离散误差，不能追认历史SLSQP返回为全局证书。原普通纯开环Nash存在性仍未闭合。

Work-C2已获接受的K精化结果还显示：指定八格K6复制到K12后，存在防御绝对改善约0.01438–0.02618、攻击约0.01246–0.01277。这是不同指定配置和不同对照，不能直接扣除本次0.029%–0.286%的方法差值，却足以限制外推：当前九组比较是K6保存计划的决策差异，不是连续控制下博弈价值的精确估计。没有K12的G/F九组同口径比较。

## 7. 审计结论与边界

1. **结构依赖有数学表达，数值响应依赖也有直接证据。**防御冻结后的aG/aF不相同，各自在本方对应防御上有严格正的交叉收益改善。
2. **防御决策确实改变，但以现有入口、节点和时槽内的再分配为主。**隔离、恢复差异可逐分量复核；它没有伴随攻击入口集的改变，收益改善也没有达到原定工程门槛。
3. **现有证据不支持“博弈不可替代”或“战略调整具有很大实际收益”。**在这些指定合成实例、K6策略类和保存局部候选中，博弈训练提供小的响应环境适配收益；固定攻击优化仍是非常接近的强基线。这个负向边界与“存在战略相互依赖”同时成立。不能推出所有参数下博弈均无价值、现实云收益或新算法优越。

原C2额外保留的seed33/business_cost/B0.6来自另一网络族，不并入本次9组；其联合相对仅恢复不占优的反例保留在原C2报告，未删除、重算或用本次正向结果覆盖。

## 8. 校验、复现与交付

本次只提取并对54个冻结配对作RK4每槽48/192子步重放（含18个新交叉配对，不含新优化或新参数）。对既有36个配对核对保存192子步目标；对全部54个配对核对C2原core快照与当前core的48子步目标。输入来源指纹、原C2 manifest匹配、预算、入口和防御冻结核对见source_manifest.json、verification.json。误差比较是保存候选上的实测积分精化，不是统一严格误差界。

```powershell
python reports/work_d5/analysis/audit_decision_difference.py --output reports/work_d5/p0/reproduction_new
```

输出拒绝覆盖已有目录；命令从项目根运行。不得把这条分析复现命令写成完整C2重新优化命令。原实验完整重跑入口仍为reports/SUPPLEMENT_C2_PROTOCOL.md；本次未执行。

主要文件：本报告、all_nine_cases_zh.md（所有节点/时槽原值）、defense_by_node_slot.csv、attack_by_node_slot.csv、payoff_matrix.csv、case_summary.csv、response_quality.csv、optimizer_returns.json、budgets.csv、replayed_states_192.csv、source_manifest.json、verification.json、metadata.json。

统计解释检查11/11：分组反转（分容量全部列出、未合并评价口径）；生态谬误（仅合成组，不推单服务器概率）；选择偏差（沿用原9组预指定集合）；碰撞变量偏差（无回归调整）；基率忽略（无诊断概率）；均值回归（无按极值挑选）；幸存者偏差（9组全部保留，历史失败不删除）；多重寻找（无显著性检验，全量输出）；分析分叉（差异指标为本次事后描述，不冒充预登记）；相关因果混淆（交叉重放仅限模型内算术）；反向因果（明确固定一方后比较，不从各自响应差值声称单方因果效应）。不报p值、置信区间或总体统计显著性，1%仅沿用原工程描述阈值。
'''
    (out/'D5_P0_decision_difference_audit_zh.md').write_text(text,encoding='utf-8')


if __name__ == '__main__':
    main()
