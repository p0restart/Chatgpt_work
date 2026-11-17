"""Independent saved-artifact checks and descriptive evidence tables for C2."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import check_controls, simulate
from .supplement_c2 import load_model, load_controls, independent_values
from .experiments import write_json


def markdown(df):
    columns=list(df.columns)
    def cell(v):return f'{v:.8g}' if isinstance(v,(float,np.floating)) else str(v)
    return '|'+ '|'.join(columns)+'|\n|'+'|'.join(['---']*len(columns))+'|\n'+'\n'.join('|'+ '|'.join(cell(v) for v in row)+'|' for row in df.itertuples(index=False,name=None))


def optimizer_records(value):
    if isinstance(value,dict):
        if all(k in value for k in ('success','status','nit','initial_control','control')):yield value
        else:
            for v in value.values():yield from optimizer_records(v)
    elif isinstance(value,list):
        for v in value:yield from optimizer_records(v)


def audit(root):
    meta=json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    if meta['status']!='COMPLETED':raise RuntimeError('Run is not completed')
    checks=[];counts=[]
    for case in sorted((root/'finite').glob('B*')):
        m=load_model(case/'model.json')
        for folder in sorted(case.glob('step*')):
            saved=json.loads((folder/'audit.json').read_text(encoding='utf-8'))
            strategies=np.load(folder/'strategies.npz');d=strategies['defense'];a=strategies['attack']
            table=np.load(folder/'payoffs_48.npz');jd=table['J_D'];ja=table['J_A']
            assert jd.shape==(len(d),len(a)) and ja.shape==jd.shape
            assert len(np.unique(d.reshape(len(d),-1),axis=0))==len(d)
            assert np.all(d[:,:,:m.n]@m.b_s+d[:,:,m.n:]@m.b_r<=m.B+1e-10)
            assert np.all(a@m.d_a<=m.A+1e-10)
            rd=np.maximum(0,jd-jd.min(axis=0)[None]);ra=np.maximum(0,ja.max(axis=1)[:,None]-ja)
            count=int(np.sum(np.maximum(rd,ra)<=1e-8))
            assert count==saved['pure_equilibria']
            coarse=np.load(folder/'payoffs_12.npz')
            cjd,cja=coarse['J_D'],coarse['J_A']
            coarse_mask=np.maximum(cjd-cjd.min(axis=0)[None],cja.max(axis=1)[:,None]-cja)<=1e-8
            fine_mask=np.maximum(rd,ra)<=1e-8
            # Independent integrator probes are selected by a fixed random seed, not favorable payoff.
            rng=np.random.default_rng(20261102)
            for _ in range(5):
                i=int(rng.integers(len(d)));j=int(rng.integers(len(a)))
                u=(a[j],d[i,:,:m.n],d[i,:,m.n:]);check_controls(m,*u)
                independent=independent_values(m,u,10.)
                scalar=simulate(m,*u,10.,48)
                checks.append(dict(case=case.name,grid=folder.name,defense=i,attack=j,
                                   vector_scalar_error=float(np.max(np.abs([jd[i,j]-scalar['J_D'],ja[i,j]-scalar['J_A']]))),
                                   independent_error=float(np.max(abs(independent-[jd[i,j],ja[i,j]])))))
            # Record selected grid equilibrium cost; a coarse grid can change the allocation substantially.
            i,j=np.unravel_index(np.argmin(np.maximum(rd,ra)),jd.shape)
            counts.append(dict(B=m.B,grid=folder.name,selected_J_D=jd[i,j],selected_J_A=ja[i,j],pure_count=count,
                               equilibrium_mask_stable=bool(np.array_equal(coarse_mask,fine_mask)),
                               candidate_J_D=saved['candidate_J_D'],cost_difference_grid_minus_candidate=jd[i,j]-saved['candidate_J_D']))
    pd.DataFrame(checks).to_csv(root/'independent_finite_checks.csv',index=False)
    pd.DataFrame(counts).to_csv(root/'finite_selected_costs.csv',index=False)
    trace_rows=[];solver=[];opt=[]
    for trace in sorted(root.rglob('trace.jsonl')):
        records=[json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()]
        last=records[-1]
        trace_rows.append(dict(path=str(trace.relative_to(root)),passed=last['passed'],iteration=last['iteration'],
                               gap_D=last['gap_D'],gap_A=last['gap_A'],residual=max(last[p]['incumbent_residual'] for p in ('D','A'))))
        for row in records:
            for item in optimizer_records(row):opt.append(dict(path=str(trace.relative_to(root)),success=item['success'],status=item['status'],residual=item['projected_residual'],violation=item['violation']))
    for path in root.rglob('multistart.json'):
        v=json.loads(path.read_text(encoding='utf-8'));solver.append(dict(path=str(path.relative_to(root)),**v))
    # Final evaluation calls are distinct from trajectory optimization calls.
    for path in (root/'comparison').glob('*/*response.json'):
        for item in optimizer_records(json.loads(path.read_text(encoding='utf-8'))):
            opt.append(dict(path=str(path.relative_to(root)),success=item['success'],status=item['status'],residual=item['projected_residual'],violation=item['violation']))
    evaluated=[]
    for path in (root/'comparison').glob('*/*evaluation_audit.json'):
        v=json.loads(path.read_text(encoding='utf-8'))
        label=path.name.removesuffix('_evaluation_audit.json')
        if label in ('Joint-dynamic','Joint-static','Recovery-only','Isolation-only'):
            s=json.loads((path.parent/f'{label}_adaptive_attack/summary.json').read_text(encoding='utf-8'))
            rel=max(0,s['J_D']-v['D']['objective'])/(1+abs(s['J_D']))
            passed=bool(rel<=1e-7 and v['D']['incumbent_residual']<=1e-4 and v['A']['residual']<=1e-4 and v['D']['success'] and v['A']['success'])
            evaluated.append(dict(case=path.parent.name,method=label,relative_D=rel,
                                  incumbent_D_residual=v['D']['incumbent_residual'],attack_residual=v['A']['residual'],passed=passed))
        for item in optimizer_records(v):
            opt.append(dict(path=str(path.relative_to(root)),success=item['success'],status=item['status'],residual=item['projected_residual'],violation=item['violation']))
    pd.DataFrame(trace_rows).to_csv(root/'solver_final_audit.csv',index=False)
    pd.DataFrame(solver).to_csv(root/'multistart_audit.csv',index=False)
    pd.DataFrame(opt).to_csv(root/'optimizer_audit.csv',index=False)
    pd.DataFrame(evaluated).to_csv(root/'final_local_candidate_audit.csv',index=False)
    reintegrated=[];provenance=[]
    for case in (root/'comparison').iterdir():
        if not case.is_dir():continue
        m=load_model(case/'model.json')
        if 'unequal' in case.name:
            original=Path('results/matched_mechanism/run01')/case.name
            control_source=original/'fine/controls.json'
        else:
            original=Path('results/p3/fair01')/case.name
            control_source=Path('results/equilibrium_audit/run01')/case.name/'warm/controls.json'
        reference=load_controls(control_source)
        frozen=load_controls(case/'Joint-dynamic_adaptive_attack/controls.csv')
        defense_difference=max(float(np.max(abs(reference[j]-frozen[j]))) for j in (1,2))
        assert defense_difference<1e-10
        assert json.loads((case/'model.json').read_text(encoding='utf-8'))==json.loads((original/'model.json').read_text(encoding='utf-8'))
        provenance.append(dict(case=case.name,model_source=str(original/'model.json'),control_source=str(control_source),
                               control_sha256=hashlib.sha256(control_source.read_bytes()).hexdigest(),
                               model_sha256=hashlib.sha256((original/'model.json').read_bytes()).hexdigest(),
                               frozen_defense_max_difference=defense_difference))
        for path in case.glob('*_attack'):
            u=load_controls(path/'controls.csv');check_controls(m,*u)
            sim=simulate(m,*u,10,192);s=json.loads((path/'summary.json').read_text(encoding='utf-8'))
            b=pd.read_csv(path/'budgets.csv')
            assert np.max(abs(b.defense_use-(u[1]@m.b_s+u[2]@m.b_r)))<1e-10
            reintegrated.append(dict(case=case.name,method=s['method'],evaluation=s['evaluation'],
                                     error=abs(sim['J_D']-s['fine_J_D'])))
    pd.DataFrame(reintegrated).to_csv(root/'new_reintegration.csv',index=False)
    write_json(root/'source_provenance_audit.json',provenance)
    result=dict(finite_tables=len(counts),finite_random_checks=len(checks),
                max_vector_scalar_error=max(x['vector_scalar_error'] for x in checks),
                max_independent_integrator_error=max(x['independent_error'] for x in checks),
                solver_runs=len(trace_rows),failed_solver_runs=sum(not x['passed'] for x in trace_rows),
                multistart_groups=len(solver),max_multistart_control_spread=max(x['control_spread'] for x in solver),
                multistart_failed_groups=sum(not(x['all_pass'] and x['fine_pass'] and x['control_spread']<=1e-3) for x in solver),
                optimizer_calls=len(opt),failed_optimizer_calls=sum(not x['success'] for x in opt),
                evaluated_local_candidates=len(evaluated),failed_final_local_candidates=sum(not x['passed'] for x in evaluated),
                max_optimizer_violation=max(x['violation'] for x in opt),new_reintegrated=len(reintegrated),
                max_reintegration_error=max(x['error'] for x in reintegrated),continuous_global_certificate=False,
                integration_error_bound='empirical_only_not_rigorous')
    write_json(root/'independent_audit.json',result)
    return result


def summarize(root):
    df=pd.read_csv(root/'comparison/summary.csv')
    assert len(df)==160 and df.case.nunique()==10
    pairs=[]
    for (case,ev),group in df.groupby(['case','evaluation']):
        joint=group[group.method=='Joint-dynamic'].iloc[0]
        for _,r in group.iterrows():
            if r.method=='Joint-dynamic':continue
            pairs.append(dict(case=case,evaluation=ev,B=r.B,seed=r.seed,baseline=r.method,
                              joint=joint.fine_J_D,baseline_cost=r.fine_J_D,
                              reduction_percent=100*(r.fine_J_D-joint.fine_J_D)/r.fine_J_D))
    pair=pd.DataFrame(pairs);pair.to_csv(root/'paired.csv',index=False)
    matched=pair[pair.case.str.contains('unequal')]
    stats=matched.groupby(['evaluation','baseline']).reduction_percent.agg(['count','min','median','max']).reset_index()
    stats['positive_count']=[int(((matched.evaluation==r.evaluation)&(matched.baseline==r.baseline)&(matched.reduction_percent>1e-8)).sum()) for r in stats.itertuples()]
    stats['at_least_1pct']=[int(((matched.evaluation==r.evaluation)&(matched.baseline==r.baseline)&(matched.reduction_percent>=1)).sum()) for r in stats.itertuples()]
    stats.to_csv(root/'comparison_statistics.csv',index=False)
    byb=matched[matched.evaluation=='adaptive_attack'].groupby(['B','baseline']).reduction_percent.agg(['min','median','max']).reset_index()
    byb.to_csv(root/'comparison_by_budget.csv',index=False)
    pivot=df[df.evaluation=='adaptive_attack'].pivot(index='case',columns='method',values='fine_J_D')
    pivot.to_csv(root/'adaptive_costs.csv')
    matched_rows=df[df.case.str.contains('unequal') & (df.evaluation=='adaptive_attack')]
    components=matched_rows.groupby(['B','method'])[['security','business','isolation','recovery','defense_use_mean','binding_slots']].mean().reset_index()
    components.to_csv(root/'components_by_budget.csv',index=False)
    audit_result=audit(root)
    finite=pd.read_csv(root/'finite/summary.csv')
    old=pd.read_csv(root/'existing_paired.csv')
    oldstats=old[old.evaluation=='adaptive_attack'].groupby('baseline').reduction_percent.agg(['min','median','max']).reset_index()
    counter=pair[(pair.case=='seed33_business_cost_B0.6')&(pair.evaluation=='adaptive_attack')]
    text=['# C2补充实验：结果与写作证据','',
          '2026-11-02。实验已完成；本报告为G2审阅依据，未预填最终论文审批。全部参数和范围在SUPPLEMENT_C2_PROTOCOL.md中预先登记。',
          '', '## 1 有限策略核验',markdown(finite),
          '', '四个表分别覆盖两个容量与两个网格，不是四个现实样本。零遗憾是保存数值收益表及有限菜单内的结果；不认证连续控制域。积分误差来自精化和独立积分器对照，不是严格数学误差界。',
          '', '### 网格均衡成本与连续候选',markdown(pd.read_csv(root/'finite_selected_costs.csv')),
          '', '网格均衡与连续候选的成本不能作为同一游戏内算法优劣的直接排序，因为双方策略空间不同。该表用于揭示离散化改变了允许的选择。',
          '', '## 2 九个匹配配置的主要比较',
          '下表为各自局部攻击响应后的J_D降低百分比；正数表示动态联合损失较低。1%为预登记工程描述阈值，不是统计显著性。',
          '各方法容量上限相同，实际资源用量不强制相等。启发式按固定份额投入，优化方法可以保留容量。因此，相对启发式优势不能单独归因于博弈考虑。',
          markdown(stats[stats.evaluation=='adaptive_attack'].drop(columns='evaluation')),
          '', '### 按容量列出完整范围',markdown(byb),
          '', '### 动态联合配置的容量与成本分解',
          '下表为每个容量下三个指定种子的算术均值，用于描述这三张合成图，不估计现实总体。binding_slots是六槽中的平均绑定槽数。',
          markdown(components[components.method=='Joint-dynamic'].drop(columns='method')),
          '', '### 公共固定攻击下，同一最终防御的交叉评价',markdown(stats[stats.evaluation=='common_fixed_attack'].drop(columns='evaluation')),
          '', '固定训练方法面对固定攻击求防御响应，联合方法的防御来自双方交替响应。公共固定攻击评价冻结两者防御，不重新训练，不把不同防御策略冒充同一策略在不同攻击下的效果。',
          '', '## 3 原负结果的补充复核',markdown(counter[['baseline','joint','baseline_cost','reduction_percent']]),
          '', '这是原模块化网络反例，与九个匹配配置分开统计，不把十个配置当成同一抽样总体。',
          '', '## 4 复用的原27配置结果',markdown(oldstats),
          '', '旧324条评价已全部重新积分，误差见existing_audit.json。旧表保留原局部求解精度；不能与本次强化结果混写成同等强度的均衡认证。',
          '', '## 5 独立检查与失败记录', '```json',json.dumps(audit_result,indent=2,ensure_ascii=False),'```',
          '', '首次编码/目录错误保留在run01与C2_EXECUTION_LOG.md；未覆盖负实验结果。数值门槛失败如非零，必须在写作包中显式处理，不能只引用完成状态。',
          '', '## 6 数据与重现',
          '- 主输出：results/supplement_c2/run02；完整收益表在finite；新增逐槽控制、预算、状态及积分精化在comparison。',
          '- 结果统计：paired.csv、comparison_statistics.csv、comparison_by_budget.csv、adaptive_costs.csv。',
          '- 原36配置的机制结果仍见reports/MATCHED_MECHANISM_FINDINGS.md，不由本次九配置比较替代。',
          '```powershell',
          'python -m pytest -q',
          'python -m src.supplement_c2 --output results/supplement_c2/reproduction_new',
          'python -m src.report_c2 --root results/supplement_c2/reproduction_new --report reports/C2_REPRODUCED.md',
          '```',
          '主实验拒绝覆盖已有目录。报告生成器重新计算统计并检查保存策略；重建报告不等于完整重新优化。']
    return '\n\n'.join(text),audit_result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--report',required=True);args=ap.parse_args()
    report,result=summarize(Path(args.root))
    Path(args.report).write_text(report,encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()

