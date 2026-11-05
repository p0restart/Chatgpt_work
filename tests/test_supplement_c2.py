import numpy as np
import yaml
from pathlib import Path
from dataclasses import replace
from src.core import synthetic_model_from_config, simulate
from src.experiments import initial_controls
from src.game_solver import ResponseProblem
from src.supplement_c2 import batch_values, StaticDefense, plans, independent_values


def test_batch_matches_scalar_and_independent_integrator():
    m=synthetic_model_from_config(yaml.safe_load(Path('configs/base.yaml').read_text(encoding='utf-8')))
    u=initial_controls(m,2,'Uniform')
    v=batch_values(m,*(x[None] for x in u),10,48)[0]
    s=simulate(m,*u,10,48)
    np.testing.assert_allclose(v,[s['J_D'],s['J_A']],rtol=1e-13,atol=1e-13)
    np.testing.assert_allclose(v,independent_values(m,u,10),rtol=1e-7,atol=1e-7)


def test_static_chain_gradient():
    m=synthetic_model_from_config(yaml.safe_load(Path('configs/base.yaml').read_text(encoding='utf-8')))
    u=initial_controls(m,2,'Uniform')
    p=StaticDefense(ResponseProblem(m,*u,10,12,'D'))
    v=p.initial.copy();_,g=p.value_gradient(v)
    for j in (0,m.n,m.n+2):
        delta=np.zeros_like(v);delta[j]=1e-6
        fd=(p.value_gradient(v+delta)[0]-p.value_gradient(v-delta)[0])/2e-6
        np.testing.assert_allclose(g[j],fd,rtol=1e-5,atol=1e-6)


def test_finite_menu_complete_count_and_budget():
    cfg=yaml.safe_load(Path('configs/base.yaml').read_text(encoding='utf-8'))
    cfg.update(n=3,network='chain',attack_entry_indices=[0],x0=[.1,0,0],B=.6)
    m=synthetic_model_from_config(cfg)
    p=plans(m,.3)
    assert p.shape==(28**2,2,6)
    assert np.max(p.sum(axis=-1))<=.6+1e-12
    assert len(np.unique(p.reshape(len(p),-1),axis=0))==len(p)
    assert np.any(np.all(p==0,axis=(1,2)))
