from pathlib import Path
import numpy as np
import yaml
from src.core import synthetic_model_from_config, check_controls, simulate
from src.experiments import METHODS, initial_controls
from src.game_solver import response, observed_gaps, alternating_responses


def setup():
    cfg=yaml.safe_load(Path('configs/p2.yaml').read_text(encoding='utf-8'))
    return synthetic_model_from_config(cfg)


def test_baselines_budget_and_ablations():
    m=setup()
    for method in METHODS:
        controls=initial_controls(m,2,method)
        check_controls(m,*controls)
        if method in ('Isolation-only','Recovery-only'):
            mode='isolation' if method=='Isolation-only' else 'recovery'
            got,info=response(m,controls,2,4,'D',11,2,mode)
            assert np.max(np.abs(got[2 if mode=='isolation' else 1]))==0
            assert simulate(m,*got,2,4)['J_D']<=simulate(m,*controls,2,4)['J_D']+1e-10
            assert info['residual']<1e-4


def test_gap_nonnegative_and_same_pair():
    m=setup(); controls=initial_controls(m,2,'Uniform')
    original=[x.copy() for x in controls]
    gap,d,a=observed_gaps(m,controls,2,4,11,2)
    base=simulate(m,*controls,2,4)
    assert gap['gap_D']>=0 and gap['gap_A']>=0
    np.testing.assert_allclose(gap['gap_D'],base['J_D']-simulate(m,*d,2,4)['J_D'],atol=1e-12)
    np.testing.assert_allclose(gap['gap_A'],simulate(m,*a,2,4)['J_A']-base['J_A'],atol=1e-12)
    for before,after in zip(original,controls):
        np.testing.assert_array_equal(before,after)


def test_alternating_reproducible_and_feasible():
    m=setup(); controls=initial_controls(m,2,'Uniform')
    settings=dict(damping=.35,max_br_rounds=1,br_restarts=2,exploratory_relative_gap_target=0.)
    u,tr=alternating_responses(m,controls,2,3,11,settings)
    v,tr2=alternating_responses(m,controls,2,3,11,settings)
    for a,b in zip(u,v):
        np.testing.assert_array_equal(a,b)
    for step in tr:
        check_controls(m,*[np.array(a) for a in step['controls']])
    assert tr[-1]['relative_D']==tr2[-1]['relative_D']
