"""D7 orchestration: fixed new graph; reuse original solvers, never old results."""
from pathlib import Path
import sys, json, hashlib, platform, time, argparse, shutil
from dataclasses import replace, asdict
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import scipy, yaml
from src.core import Model, validate_model, check_controls, simulate, dynamics
from src.game_solver import ResponseProblem, state_jacobian
from src.experiments import initial_controls, write_json
from src.supplement_c2 import dump_model, load_controls
from paper.work_d5.analysis.run_replanning import Run, random_pair, execute, objective, PARTS, DT

BASE=ROOT/'paper/work_d7'
ASSETS=['API网关工作负载实例组','Web应用工作负载实例组','订单处理服务实例组','身份认证服务实例组','核心数据库服务实例组','后台管理服务实例组']
EDGES=[(0,2,.08),(0,3,.09),(1,2,.10),(3,2,.11),(3,4,.07),(3,5,.12),(2,4,.10),(5,4,.05)]
ASSUMPTIONS=['网关服务凭证被滥用且订单接口存在可利用弱点','网关持有认证访问路径且认证接口存在可利用弱点','Web应用可访问订单服务且内部接口存在可利用弱点','认证服务凭证可用于订单接口越权','认证服务持有受限数据库访问凭证且授权边界失效','认证服务令牌可被滥用于后台管理授权路径','订单服务数据库凭证被窃取并被用于利用数据库弱点','后台管理服务持有数据库管理授权且凭证可被滥用']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def model(B):
    c=lambda x:np.full(6,x,dtype=float)
    beta=np.zeros((6,6))
    for j,i,w in EDGES: beta[j,i]=w
    return Model(beta=beta,alpha=np.array([.25,.25,0,0,0,0]),epsilon=c(1),delta=c(.1),gamma=c(.3),q=np.array([1,1,1,1,4,1.]),h=c(.05),c_s=c(1),c_r=c(1),g=c(1),c_a=c(1),omega=c(0),nu=c(0),b_s=c(1),b_r=c(1),d_a=c(1),entry=np.array([True,True,False,False,False,False]),x0=np.array([.1,0,0,0,0,0]),B=B,A=.8)

def register():
    m=model(1.2);validate_model(m)
    cfg={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in asdict(m).items()}
    cfg.update(topology_id='D7_asymmetric_cloud_fixed_20261114',T=10,K=6,budgets=[1.2,.6,1.8],H=48,a0=[.4,.4,0,0,0,0],seed=20261114,event={'tau':5,'alpha0_after':.5})
    (BASE/'config_new_topology.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),encoding='utf-8')
    pd.DataFrame([dict(paper_node=f'v{i+1}',code_index=i,asset=a,entry=i<2,q=m.q[i],out_strength=m.beta[i].sum(),isolation='来源端访问限制/凭证权限收缩的归一化投入',recovery='清理或重建受损工作负载的归一化投入') for i,a in enumerate(ASSETS)]).to_csv(BASE/'topology_assets.csv',index=False,encoding='utf-8-sig')
    rows=[dict(source=j,target=i,paper_source=f'v{j+1}',paper_target=f'v{i+1}',beta=w,security_assumption=ASSUMPTIONS[k],empirically_verified=False) for k,(j,i,w) in enumerate(EDGES)]
    pd.DataFrame(rows).to_csv(BASE/'topology_edges.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame([{**r,'source_asset':ASSETS[r['source']],'target_asset':ASSETS[r['target']]} for r in rows]).to_csv(BASE/'topology_assets_edges.csv',index=False,encoding='utf-8-sig')
    shutil.copyfile(BASE/'03_experiment_protocol.md',BASE/'D7_experiment_protocol.md')
    paths=[ROOT/'02_MODEL_SPEC.md',ROOT/'DECISIONS.md',ROOT/'reviews/APPROVAL_LOG.md',ROOT/'paper/work_d6.zip',*list((ROOT/'src').glob('*.py')),ROOT/'paper/work_d5/analysis/run_replanning.py',*list((ROOT/'paper/work_d6').glob('*.md')),ROOT/'paper/work_d6/references.bib',ROOT/'paper/work_d6/analysis/verification.json',BASE/'sources/instruction_source.md',BASE/'03_experiment_protocol.md',BASE/'config_new_topology.yaml',Path(__file__)]
    write_json(BASE/'sources/source_manifest.json',{str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths})
    (BASE/'02_topology_spec.md').write_text('# 新主拓扑与归一化参数\n\n全部8条边见topology_edges.csv；来源为行、接收为列。安全关联均为人工预设、带条件的场景假设，不是已验证漏洞或业务调用图。参数见config_new_topology.yaml。\n\n状态为相似工作负载实例组的受损比例；s为源端隔离，r为本地恢复。隔离可对应访问限制或凭证权限收缩的资源投入，恢复可对应清理/重建工作负载的投入；二者不是可直接执行的防火墙规则或Pod命令。数据库无出边，隔离不会改善状态，正成本下固定其他行动的最优隔离为零。\n\n时间采用未标定模型单位；alpha、beta、delta、gamma为每模型时间的归一化率/效率；q、g为单位受损比例的损失/收益率，h为单位隔离投入的业务损失率，c为二次成本率，容量系数为每单位投入的资源占用。所有成本均为相对单位，没有货币或实测量纲校准。x0只表示v1初始10%受损；其余未受损，随后允许传播。\n',encoding='utf-8')
    (BASE/'01_decisions_and_provenance.md').write_text('# D7 决策与来源\n\n2026-11-14：本轮用户明确授权新拓扑实验与待审第二版论文，指令原文保存sources/instruction_source.md。此授权不批准任何尚未生成结果。\n\n原G1/G2、G-D2记录以reviews/APPROVAL_LOG.md为准；D4-P0-1、D5-P0和D5结果仍待审，不修改其状态。新拓扑与参数按用户D7任务书固定，未改变ODE、目标或瞬时约束。所有新结果必须有D7标识。\n\nD6原始压缩包、解包稿、数学检查、主张映射、审阅清单、数据和verification.json可访问。独立D6审计任务书和候选BibTeX未定位，已请求路径，不声称完整继承其未见内容。源文件SHA256见sources/source_manifest.json。\n',encoding='utf-8')

def preflight(out):
    out.mkdir(exist_ok=False);checks=[]
    def add(name,value,tol=1e-6): checks.append(dict(check=name,value=float(value),threshold=tol,passed=bool(value<=tol)))
    m=model(1.2);validate_model(m)
    assert list(np.flatnonzero(m.entry))==[0,1] and m.q[4]==4 and np.count_nonzero(m.beta)==8
    for j,i,w in EDGES: assert m.beta[j,i]==w
    assert np.all(m.beta[4]==0)
    for K in (6,3,2,1):
        mm=m if K==6 else replace(m,alpha=np.array([.5,.25,0,0,0,0]),x0=np.array([.15,.12,.07,.05,.02,.01]))
        u=tuple(v*.5 for v in random_pair(mm,K,20261114+K)); check_controls(mm,*u)
        for player in ('D','A'):
            pr=ResponseProblem(mm,*u,K*DT,48,player);v=pr.initial
            assert len(v)==K*(12 if player=='D' else 2)
            value,g=pr.value_gradient(v);errors=[]
            for j in range(len(v)):
                d=np.zeros_like(v);d[j]=1e-6
                fd=(pr.value_gradient(v+d)[0]-pr.value_gradient(v-d)[0])/2e-6
                errors.append(abs(fd-g[j]))
            add(f'K{K}_{player}_all_gradient_components',max(errors))
            sim=simulate(mm,*u,K*DT,48)
            add(f'K{K}_{player}_objective',abs(value-(sim['J_D'] if player=='D' else -sim['J_A'])))
            assert pr.C.shape==(K,len(v)) and np.all(pr.weights==1)
        x=np.linspace(.1,.8,6)
        fd=np.column_stack([(dynamics(mm,x+np.eye(6)[j]*1e-6,*[z[0] for z in u])-dynamics(mm,x-np.eye(6)[j]*1e-6,*[z[0] for z in u]))/2e-6 for j in range(6)])
        add(f'K{K}_state_jacobian',np.max(abs(fd-state_jacobian(mm,x,*[z[0] for z in u]))))
        for i in range(6):
            y=x.copy();y[i]=0;assert dynamics(mm,y,*[z[0] for z in u])[i]>=0
            y[i]=1;assert dynamics(mm,y,*[z[0] for z in u])[i]<=0
        sims={H:simulate(mm,*u,K*DT,H) for H in (48,96,192)}
        add(f'K{K}_integration',max(max(abs(sims[48]['J_D']-sims[H]['J_D']),np.max(abs(sims[48]['states']-sims[H]['states'][::H//48]))) for H in (96,192)))
        u0=[v.copy() for v in u];u0[1][:,4]=0
        s0=simulate(mm,*u0,K*DT,48)
        add(f'K{K}_database_state_independent',np.max(abs(s0['states']-sims[48]['states'])),1e-12)
        assert s0['J_D']<sims[48]['J_D']
    pd.DataFrame(checks).to_csv(out/'checks.csv',index=False)
    write_json(out/'gate1.json',dict(passed=all(r['passed'] for r in checks),checks=checks,multistart_status='deferred_to_Gate2_same_solver'))
    assert all(r['passed'] for r in checks)

def save_pair(out,m,u,label):
    check_controls(m,*u);sims={H:simulate(m,*u,10,H) for H in (48,96,192)}
    sim=sims[48]
    err=max(max(abs(sim['J_D']-sims[H]['J_D']),abs(sim['J_A']-sims[H]['J_A']),np.max(abs(sim['states']-sims[H]['states'][::H//48])),max(abs(sim['parts'][p]-sims[H]['parts'][p]) for p in sim['parts'])) for H in (96,192))
    write_json(out/f'{label}_controls.json',[v.tolist() for v in u])
    pd.DataFrame([dict(t=t,**{f'x{i}':x[i] for i in range(6)}) for t,x in zip(sim['times'],sim['states'])]).to_csv(out/f'{label}_states.csv',index=False)
    rows=[];x=m.x0.copy()
    for k in range(6):
        seg=simulate(replace(m,x0=x),*(v[k:k+1] for v in u),DT,48)
        for i in range(6):
            rows.append(dict(slot=k,t_start=k*DT,t_end=(k+1)*DT,node=i,asset=ASSETS[i],a=u[0][k,i],s=u[1][k,i],r=u[2][k,i],resource=u[1][k,i]+u[2][k,i],total_resource=float((u[1][k]+u[2][k]).sum()),attack_resource=float(u[0][k].sum()),x_start=x[i],x_end=seg['states'][-1,i],business=DT*m.h[i]*u[1][k,i],isolation=DT*.5*m.c_s[i]*u[1][k,i]**2,recovery=DT*.5*m.c_r[i]*u[2][k,i]**2,solver_status='see decision.json'))
        x=seg['states'][-1].copy()
    pd.DataFrame(rows).to_csv(out/f'{label}_decisions.csv',index=False,encoding='utf-8-sig')
    row=dict(B=m.B,method=label,J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts'],integration_error=err,state_min=float(sim['states'].min()),state_max=float(sim['states'].max()),mean_resource=float((u[1]+u[2]).sum(axis=1).mean()),database_isolation=float(abs(u[1][:,4]).max()))
    write_json(out/f'{label}_evaluation.json',row)
    assert err<=1e-6 and row['database_isolation']<=1e-8
    return row

def static(run,B,b):
    out=run.out/f'B{B}';out.mkdir();m=model(B);dump_model(out/'model.json',m)
    warm=initial_controls(m,6,'Uniform');seed=20261114+1000*b
    run.context=dict(B=B,evaluation='offline',method='G',update=-1)
    folder=out/'G';folder.mkdir();g,good=run.game(m,warm,seed,folder,-3);run.save()
    save_pair(out,m,g,'G')
    if not good: raise RuntimeError(f'Gate2/3 G numerical gate failed B={B}')
    run.context=dict(B=B,evaluation='offline',method='F',update=-1)
    folder=out/'F';folder.mkdir();f,good=run.unilateral(m,warm,'D',seed+100,folder,-3);run.save()
    save_pair(out,m,f,'F')
    if not good: raise RuntimeError(f'Gate2/3 F numerical gate failed B={B}')
    write_json(out/'static_gate.json',dict(passed=True,B=B))
    return g,f

def cross(run,B,b):
    out=run.out/f'B{B}';m=model(B)
    g=load_controls(out/'G_controls.json');f=load_controls(out/'F_controls.json')
    folder=out/'F_attack_response';folder.mkdir()
    run.context=dict(B=B,evaluation='cross',method='F_attack_response',update=-1)
    af,good=run.unilateral(m,f,'A',20261114+1000*b+200,folder,-3,strong=True);run.save()
    if not good: raise RuntimeError('F attack response quality failed')
    rows=[]
    for method,u in [('G',g),('F',f)]:
        for name,a in [('a0',f[0]),('aG',g[0]),('aBR_F',af[0])]:
            sim=simulate(m,a,u[1],u[2],10,48)
            rows.append(dict(B=B,method=method,attack=name,J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts']))
    pd.DataFrame(rows).to_csv(out/'cross_evaluation.csv',index=False)
    write_json(out/'cross_attacks.json',dict(a0=f[0].tolist(),aG=g[0].tolist(),aBR_F=af[0].tolist(),max_attack_change=float(abs(g[0]-af[0]).max())))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['register','preflight','static','cross']);ap.add_argument('--budget',type=float,default=1.2);args=ap.parse_args()
    if args.stage=='register': register();return
    out=BASE/'results'
    if args.stage=='preflight': preflight(out/'gate1');return
    b=[1.2,.6,1.8].index(args.budget)
    if b and not (out/'static/B1.2/static_gate.json').exists(): raise RuntimeError('Pilot not passed')
    root=out/'static'
    root.mkdir(exist_ok=True)
    run=Run(root)
    # Preserve preceding budgets' CSV rows while appending calls to the JSONL.
    names={'attempts':'optimizer_attempts','audit':'solver_audit','timing':'timing','plans':'planned_controls','executed':'executed_controls','trajectories':'trajectories','objectives':'objectives','comparisons':'comparisons','attacks':'attack_scenarios','quality':'quality','tasks':'tasks'}
    for attr,name in names.items():
        p=root/f'{name}.csv'
        if p.exists(): setattr(run,attr,pd.read_csv(p).to_dict('records'))
    # Save per-invocation environment; never imply remote/cloud execution.
    write_json(root/f'environment_{args.stage}_{args.budget}.json',dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),argv=sys.argv))
    try:
        if args.stage=='static': static(run,args.budget,b)
        else: cross(run,args.budget,b)
    except Exception as exc:
        run.save();write_json(root/f'FAILED_{args.stage}_{args.budget}.json',dict(error=repr(exc)));raise
    finally: run.save()

if __name__=='__main__': main()
