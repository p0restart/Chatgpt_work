"""Independent delivery checks; no new optimization or model mutation."""
import sys,json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
import yaml
from diagnostics import OUT,load,unpack,pack
from src.core import check_controls,simulate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seal',action='store_true');args=ap.parse_args()
    m,pair=load();cfg=yaml.safe_load((ROOT/'paper/work_d7/config_new_topology.yaml').read_text(encoding='utf-8'))
    for k,v in vars(m).items():assert np.array_equal(np.asarray(v),np.asarray(cfg[k])),k
    source=read(OUT/'source_manifest.json');assert all(sha(ROOT/p)==h for p,h in source.items())
    metrics=pd.read_csv(OUT/'E3_experiment_results.csv');errors=[]
    for name in metrics.point:
        data=np.load(OUT/f'results/{name}.npz');check_controls(m,*unpack(data['z']))
        assert np.max(abs(data['H']-(data['J']+data['J'].T)/2))<1e-14
        for block,key,val,vec in [('D','D','ed','vd'),('A','A','ea','va'),('H','H','eh','vh')]:
            error=float(np.max(abs(data[key]@data[vec]-data[vec]*data[val])))
            errors.append(error);assert error<1e-10
        row=metrics[metrics.point==name].iloc[0]
        assert abs(row.lambda_H-data['eh'][0])<1e-12
    summary=pd.read_csv(OUT/'results/new_multistart_summary.csv');opt_count=0;max_replay=0.
    for name in summary.path:
        folder=OUT/f'results/new_multistart/{name}'
        u=tuple(np.array(x) for x in read(folder/'controls.json'));check_controls(m,*u)
        attempts=pd.read_csv(folder/'optimizer_attempts.csv');assert attempts.success.all() and (attempts.status==0).all();opt_count+=len(attempts)
        budgets=pd.read_csv(folder/'per_slot_budgets.csv');assert len(budgets)==6 and budgets.passed.all()
        for H in (48,96):
            sim=simulate(m,*u,10,H);stored=read(folder/f'objectives_H{H}.json')
            states=pd.read_csv(folder/f'states_H{H}.csv')
            err=max(abs(sim['J_D']-stored['J_D']),abs(sim['J_A']-stored['J_A']),np.max(abs(sim['states']-states[[f'x{i}' for i in range(6)]].to_numpy())))
            max_replay=max(max_replay,float(err));assert err<1e-12
        audits=read(folder/'final_same_pair_audits.json')
        for audit in audits.values():
            for p in ('D','A'):
                for trial in audit[p]['raw']:
                    assert trial['success'] and trial['status']==0
                    opt_count+=1
    assert opt_count==90
    res=dict(passed=True,original_files_checked=len(source),original_files_changed=0,model_config_exact_match=True,matrix_eigenpair_max_residual=max(errors),new_paths=len(summary),optimizer_attempts_checked=opt_count,all_optimizer_status_zero=True,fixed_control_serialization_replay_error=max_replay,strict_global_certificate=False)
    if args.seal:
        (OUT/'verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
        files=sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS')
        (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in files),encoding='utf-8')
    else:
        for line in (OUT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            h,path=line.split('  ',1);assert sha(OUT/path)==h,path
        res['delivery_hashes_verified']=True
    print(json.dumps(res,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
