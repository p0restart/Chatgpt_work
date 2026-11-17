"""Reconstruct the entire pilot cover and check every rational lower bound."""
from common import *
from source_relaxation import objective,lower_box
import argparse
def tighten_independent(lo,hi,cap):
    ans=list(hi)
    for k in range(6):
        s=sum(lo[12*k:12*k+12],F(0))
        if s>cap:return None
        for j in range(12*k,12*k+12):
            ans[j]=min(ans[j],cap-s+lo[j])
            if ans[j]<lo[j]:return None
    return list(lo),ans
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');args=ap.parse_args()
    model,z=frozen();a=z[72:];cap=F(float(model['B']));c=read(OUT/'results/defender_certificate.json')
    src=read(OUT/'results/source_relaxation_certificate.json');ref=[F(v) for v in src['reference']];st=F(src['step']);m=F(5,3)
    value=objective(model,a,ref);assert [str(v) for v in value]==src['reference_value']
    for j,p in enumerate(src['probes']):
        plus=ref.copy();minus=ref.copy();plus[j]+=st;minus[j]-=st
        pv=objective(model,a,plus);nv=objective(model,a,minus)
        assert [str(v) for v in pv]==p['plus'] and [str(v) for v in nv]==p['minus']
        g=[(value[0]-nv[1])/st+m*st/2,(pv[1]-value[0])/st-m*st/2]
        assert [str(v) for v in g]==src['gradient_intervals'][j]
    heuristic=read(OUT/'results/heuristic_D.json');u=[F(v) for v in heuristic['strict_feasible_response']]
    for k in range(6):assert all(0<=v<=1 for v in u[12*k:12*k+12]) and sum(u[12*k:12*k+12],F(0))<=cap
    UB=F(heuristic['validated']['B_D'][1]);assert UB==F(c['global_BR_upper'])
    if args.full:assert evaluate(model,u,a,192)==heuristic['validated']
    q=[F(float(v)) for v in model['q']];H=24;eta=rk_error(H)['mean']
    corner={}
    for n,line in enumerate((OUT/'results/defender_corner_evaluations.jsonl').read_text(encoding='utf-8').splitlines()):
        item=json.loads(line);ev=item['evaluation'];upper=[F(v) for v in item['upper']]
        assert item['id']==n
        if args.full:assert evaluate(model,upper,a,H)==ev
        corner[n]=(upper,ev)
        if n%200==0:print('verified_corner',n,flush=True)
    nodes={};children={};leaves=set();valid=0;pruned=0;infeasible=0
    records=[json.loads(line) for line in (OUT/'results/defender_nodes.jsonl').read_text(encoding='utf-8').splitlines()]
    for expected,rec in enumerate(records):
        idx=rec['id'];assert idx==expected
        if rec['parent'] is None:
            rawlo=[F(0)]*72;rawhi=[F(1)]*72
            for k in range(6):rawhi[12*k+4]=0
            assert idx==0
        else:
            parent=rec['parent'];assert parent in nodes
            children.setdefault(parent,[]).append(idx);leaves.discard(parent)
            pl,ph,_=nodes[parent];rawlo=pl.copy();rawhi=ph.copy();d=rec['branch_dimension'];t=F(rec['branch_split'])
            assert pl[d]<t<ph[d] and t==(pl[d]+ph[d])/2
            if rec['side']=='left':rawhi[d]=t
            else:assert rec['side']=='right';rawlo[d]=t
        reduced=tighten_independent(rawlo,rawhi,cap)
        if reduced is None:
            assert rec['status']=='infeasible';infeasible+=1;continue
        lo,hi=reduced;assert [str(v) for v in lo]==rec['low'] and [str(v) for v in hi]==rec['high']
        upper,ev=corner[rec['corner_id']];assert upper==hi
        integ=[F(v[0]) for v in ev['node_integrals']]
        naive=max(F(0),sum((q[i]*integ[i] for i in range(6)),F(0))-9*eta)+direct_cost(model,lo)
        sc=lower_box(src,lo,hi);down=max(F(0),sum((q[i]*integ[i] for i in range(2,6)),F(0))-7*eta)
        other=F(0)
        for k in range(6):
            for j in range(6):
                ss=lo[12*k+j];rr=lo[12*k+6+j]
                other+=F(5,3)*(F(float(model['h'][j]))*ss+ss*ss/2+(rr*rr/2 if j>=2 else 0))
        raw=max(F(0),naive,sc+down+other);lb=max(raw,nodes[rec['parent']][2]) if rec['parent'] is not None else raw
        assert naive==F(rec['naive_lower']) and sc==F(rec['source_relaxation_lower']) and sc+down+other==F(rec['enhanced_lower']) and raw==F(rec['raw_lower']) and lb==F(rec['lower_bound'])
        nodes[idx]=(lo,hi,lb);valid+=1
        if rec['status']=='bound_pruned':assert lb>=UB;pruned+=1
        else:assert rec['status']=='live' and lb<UB;leaves.add(idx)
    for parent,ids in children.items():
        assert len(ids)==2
        left,right=[records[j] for j in ids]
        assert left['side']=='left' and right['side']=='right'
        assert left['branch_dimension']==right['branch_dimension'] and left['branch_split']==right['branch_split']
    assert leaves==set(c['frontier']) and len(records)==c['generated_regions']<=2000
    assert len(corner)==c['corner_evaluations']
    lower=min(nodes[j][2] for j in leaves) if leaves else UB
    assert lower==F(c['global_BR_lower']) and F(c['gap_upper'])==F(c['candidate_payoff_B'][1])-lower
    original=read(OUT/'source_manifest.json');assert all(sha(ROOT/p)==h for p,h in original.items())
    obj=dict(passed=True,full_interval_reintegration=args.full,source_convex_relaxation_checked=True,generated_regions=len(records),valid_regions=valid,infeasible=infeasible,bound_pruned=pruned,retained_frontier=len(leaves),every_branch_pair_covers_parent=True,global_BR_lower=str(lower),global_BR_upper=str(UB),candidate_unchanged=True,protected_files=len(original),changed_files=0,one_percent_pass=c['passed_1pct'])
    dump(OUT/'results/defender_verification.json',obj);print('DEFENDER COVER VERIFIED',len(records),float(lower),flush=True)
if __name__=='__main__':main()
