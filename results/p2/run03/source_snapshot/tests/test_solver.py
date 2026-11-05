from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
import yaml
from src.core import dynamics, simulate, synthetic_model_from_config, validate_model
from src.game_solver import ResponseProblem, state_jacobian, local_best_response


@pytest.fixture
def setup():
    cfg=yaml.safe_load(Path('configs/p2.yaml').read_text(encoding='utf-8'))
    m=synthetic_model_from_config(cfg)
    a=np.zeros((2,m.n)); a[:,m.entry]=.2
    s=np.full_like(a,.1); r=s.copy()
    return m,a,s,r


def test_jacobian_and_boundary(setup):
    m,a,s,r=setup
    x=np.linspace(.1,.8,m.n)
    eps=1e-6
    fd=np.column_stack([(dynamics(m,x+np.eye(m.n)[j]*eps,a[0],s[0],r[0])-dynamics(m,x-np.eye(m.n)[j]*eps,a[0],s[0],r[0]))/(2*eps) for j in range(m.n)])
    np.testing.assert_allclose(state_jacobian(m,x,a[0],s[0],r[0]),fd,atol=1e-9)
    for j in range(m.n):
        y=x.copy(); y[j]=0
        assert dynamics(m,y,a[0],s[0],r[0])[j]>=0
        y[j]=1
        assert dynamics(m,y,a[0],s[0],r[0])[j]<=0


@pytest.mark.parametrize('player',['D','A'])
def test_discrete_gradient_and_objective(setup,player):
    m,a,s,r=setup
    m=replace(m,omega=np.arange(m.n)*.2,nu=np.arange(m.n)*.1)
    pr=ResponseProblem(m,a,s,r,3,6,player)
    v=pr.initial
    val,g=pr.value_gradient(v)
    sim=simulate(m,a,s,r,3,6)
    assert val==pytest.approx(sim['J_D'] if player=='D' else -sim['J_A'],abs=1e-12)
    fd=[]
    for j in range(len(v)):
        dv=np.eye(len(v))[j]*1e-5
        fd.append((pr.value_gradient(v+dv)[0]-pr.value_gradient(v-dv)[0])/2e-5)
    np.testing.assert_allclose(g,fd,atol=1e-8)


@pytest.mark.parametrize('player',['D','A'])
def test_response_nonworsening_feasible_reproducible(setup,player):
    m,a,s,r=setup
    pr=ResponseProblem(m,a,s,r,2,4,player)
    v,tr=local_best_response(pr,seed=11,starts=2)
    w,tr2=local_best_response(pr,seed=11,starts=2)
    assert pr.value_gradient(v)[0]<=pr.value_gradient(pr.initial)[0]+1e-10
    assert pr.violation(v)<=1e-10
    assert all(z['success'] for z in tr)
    np.testing.assert_allclose(v,w,atol=1e-12,rtol=0)
    assert pr.projected_residual(v,pr.value_gradient(v)[1])<1e-4


def test_invalid_capacity_and_time(setup):
    m,a,s,r=setup
    for field in ('A','B'):
        with pytest.raises(ValueError):
            validate_model(replace(m,**{field:float('nan')}))
    with pytest.raises(ValueError):
        simulate(m,a,s,r,float('inf'),4)


def test_projection_residual_active_budget(setup):
    m,a,s,r=setup
    pr=ResponseProblem(m,a,s,r,2,4,'D')
    # Unit weights: equal v exactly fills each budget; equal negative gradient
    # is balanced by a positive budget multiplier, not by zero raw gradient.
    v=np.full_like(pr.initial,m.B/pr.width)
    assert pr.projected_residual(v,-np.ones_like(v))<1e-12
    assert pr.projected_residual(v,np.ones_like(v))>.1
