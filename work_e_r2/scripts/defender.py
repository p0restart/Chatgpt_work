"""Pilot certified B&B: all live leaves retained; no claim at budget stop."""
from common import *
from source_relaxation import make,lower_box
from heuristics import search
import heapq,csv
def tighten(lo,hi,cap):
    lo=lo.copy();hi=hi.copy()
    for k in range(6):
        ix=list(range(12*k,12*k+12));s=sum((lo[j] for j in ix),F(0))
        if s>cap:return None
        for j in ix:
            hi[j]=min(hi[j],cap-s+lo[j])
            if hi[j]<lo[j]:return None
    return lo,hi
def main():
    assert (OUT/'results/attacker_certificate.json').exists()
    model,z=frozen();u0,a0=z[:72],z[72:];cap=F(float(model['B']));H=24;limit=1999
    start=time.perf_counter();heur=search('D');UB=F(heur['validated']['B_D'][1]);base=read(OUT/'results/candidate_payoff_enclosure.json')
    source=make();dump(OUT/'results/defender_incumbent.json',dict(cost_B_upper=str(UB),source='heuristic_D.json',candidate_unchanged=True))
    # Fixed local gradients are used solely for branch priority, never bounds.
    r1=read(ROOT/'work_e_r1/results/candidate_VI_interval_certificate.json');fm=[(F(v[0])+F(v[1]))/2 for v in r1['gradient_intervals'][:72]]
    weights=[]
    for k in range(6):
        for j in range(12):
            direct=u0[12*k+j]+(F(float(model['h'][j])) if j<6 else 0)
            weights.append(max(F(3,100),abs(direct*F(5,3)-fm[12*k+j])))
    dump(OUT/'results/branch_priority.json',dict(weights=[str(v) for v in weights],purpose='branch ordering only; not a validity assumption'))
    cache={};evals=0;nextid=0;nodes={};heap=[];pruned=0;infeasible=0;log=[]
    nodepath=OUT/'results/defender_nodes.jsonl';evalpath=OUT/'results/defender_corner_evaluations.jsonl'
    assert not nodepath.exists() and not evalpath.exists()
    def corner(hi):
        nonlocal evals
        key=tuple(hi)
        if key in cache:return cache[key]
        value=evaluate(model,hi,a0,H);rec=dict(id=evals,upper=[str(x) for x in hi],evaluation=value)
        with evalpath.open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
        cache[key]=(evals,value);evals+=1;return cache[key]
    def create(lo,hi,parent=None,side=None,dim=None,split=None):
        nonlocal nextid,pruned,infeasible
        idx=nextid;nextid+=1;pair=tighten(lo,hi,cap)
        rec=dict(id=idx,parent=parent,side=side,branch_dimension=dim,branch_split=str(split) if split is not None else None)
        if pair is None:
            rec.update(status='infeasible',raw_low=[str(x) for x in lo],raw_high=[str(x) for x in hi]);infeasible+=1
        else:
            lo,hi=pair;ei,ev=corner(hi);Ilo=[F(v[0]) for v in ev['node_integrals']];emean=rk_error(H)['mean']
            q=[F(float(v)) for v in model['q']]
            sec=max(F(0),sum((q[i]*Ilo[i] for i in range(6)),F(0))-9*emean)
            down=max(F(0),sum((q[i]*Ilo[i] for i in range(2,6)),F(0))-7*emean)
            naive=sec+direct_cost(model,lo)
            src=lower_box(source,lo,hi)
            other=F(0)
            for k in range(6):
                for j in range(6):
                    s=lo[12*k+j];r=lo[12*k+6+j]
                    other+=F(5,3)*(F(float(model['h'][j]))*s+s*s/2+(r*r/2 if j>=2 else 0))
            enhanced=src+down+other;raw=max(naive,enhanced,F(0));lb=max(raw,nodes[parent]['lb']) if parent is not None else raw
            status='bound_pruned' if lb>=UB else 'live'
            if status=='bound_pruned':pruned+=1
            rec.update(status=status,low=[str(x) for x in lo],high=[str(x) for x in hi],corner_id=ei,naive_lower=str(naive),source_relaxation_lower=str(src),enhanced_lower=str(enhanced),raw_lower=str(raw),lower_bound=str(lb),UB_used=str(UB))
            nodes[idx]=dict(lo=lo,hi=hi,lb=lb,status=status)
            if status=='live':heapq.heappush(heap,(lb,idx))
        with nodepath.open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
        return idx
    lo=[F(0)]*72;hi=[F(1)]*72
    for k in range(6):hi[12*k+4]=0
    assert all(v==0 for v in model['beta'][4]) and all(v>0 for v in model['h'])
    create(lo,hi)
    initial=heap[0][0]
    def record():
        lower=heap[0][0] if heap else UB
        elapsed=time.perf_counter()-start
        row=dict(regions_created=nextid,corner_evaluations=evals,live_regions=len(heap),bound_pruned=pruned,infeasible=infeasible,lower_bound_B=float(lower),upper_bound_B=float(UB),gap_upper_B=float(F(base['B_D'][1])-lower),global_BR_width=float(UB-lower),seconds=elapsed,normalized_gap_upper=float((F(base['B_D'][1])-lower)/(1+F(base['B_D'][0]))))
        log.append(row)
        with (OUT/'results/defender_bounds.csv').open('w',newline='',encoding='utf-8') as f:
            wr=csv.DictWriter(f,fieldnames=list(row));wr.writeheader();wr.writerows(log)
        print('B&B',nextid,'LB',float(lower),'UB',float(UB),'leaves',len(heap),'sec',round(elapsed,1),flush=True)
    record()
    while heap and nextid+2<=limit:
        lb,idx=heapq.heappop(heap);node=nodes[idx];node['status']='split'
        lo,hi=node['lo'],node['hi'];dim=max(range(72),key=lambda j:float((hi[j]-lo[j])*weights[j]))
        assert hi[dim]>lo[dim];mid=(hi[dim]+lo[dim])/2
        lh=hi.copy();lh[dim]=mid;rl=lo.copy();rl[dim]=mid
        create(lo,lh,idx,'left',dim,mid);create(rl,hi,idx,'right',dim,mid)
        if nextid%100==99 or nextid>=limit:record()
    record();lower=heap[0][0] if heap else UB;eps=F(base['B_D'][1])-lower
    cert=dict(object='B exact ODE, fixed A0',original_strategy_dimension=72,branch_face_dimension=66,dominance_reduction='six database isolation controls set to zero on global optimum face; original domain unchanged',root_reduction_validated=True,generated_regions=nextid,region_budget=limit,corner_evaluations=evals,live_regions=len(heap),bound_pruned=pruned,infeasible_regions=infeasible,all_live_leaves_retained=True,frontier=[idx for _,idx in heap],initial_lower_bound=str(initial),global_BR_lower=str(lower),global_BR_upper=str(UB),candidate_payoff_B=base['B_D'],best_known_response_B=heur['validated']['B_D'],gap_lower=str(max(F(0),F(base['B_D'][0])-UB)),gap_upper=str(eps),normalized_gap_upper=str(eps/(1+F(base['B_D'][0]))),passed_1pct=eps/(1+F(base['B_D'][0]))<=F(1,100),passed_0_1pct=eps/(1+F(base['B_D'][0]))<=F(1,1000),termination='pilot_region_budget' if heap else 'all_regions_pruned',expanded_to_30000=False,seconds=time.perf_counter()-start,summary=dict(BR_lower=float(lower),BR_upper=float(UB),gap_upper=float(eps),normalized_gap_upper=float(eps/(1+F(base['B_D'][0])))))
    dump(OUT/'results/defender_certificate.json',cert);print(cert['summary'],flush=True)
if __name__=='__main__':main()
