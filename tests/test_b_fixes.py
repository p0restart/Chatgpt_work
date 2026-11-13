from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
import yaml
from src.core import synthetic_model_from_config, simulate, validate_model, check_integration
from src.game_solver import ResponseProblem, response, observed_gaps
import src.game_solver as solver

@pytest.fixture
def case():
    m = synthetic_model_from_config(yaml.safe_load(Path('configs/p2.yaml').read_text(encoding='utf-8')))
    a = np.zeros((2, m.n)); a[:, m.entry] = .2
    s = np.full_like(a, .1)
    return m, (a, s, s.copy())

@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf])
def test_b1_nonfinite_controls_gradient_and_gap(case, bad, monkeypatch):
    m, u = case
    p = ResponseProblem(m, *u, 3, 6, 'D')
    v = p.initial.copy(); v[0] = bad
    for call in (p.violation, p.value_gradient, p.schedules):
        with pytest.raises(ValueError, match='finite'):
            call(v)
    with pytest.raises(ValueError):
        p.projected_residual(p.initial, v)
    monkeypatch.setattr(solver, 'response', lambda *a, **kw: (u, {'objective': bad}))
    with pytest.raises(FloatingPointError, match='gap'):
        observed_gaps(m, u, 3, 6, 11)


def test_b1_signed_gap_preserved(case, monkeypatch):
    m, u = case
    sim = simulate(m, *u, 3, 6)
    def fake(*args, **kwargs):
        return u, {'objective': sim['J_D'] + 1 if args[4] == 'D' else -sim['J_A'] + 2}
    monkeypatch.setattr(solver, 'response', fake)
    audit, _, _ = observed_gaps(m, u, 3, 6, 11)
    assert audit['signed_gap_D'] == pytest.approx(-1)
    assert audit['signed_gap_A'] == pytest.approx(-2)
    assert audit['gap_D'] == audit['gap_A'] == 0

@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf, 0, -1])
def test_b2_time(case, bad):
    m, u = case
    for call in (lambda: simulate(m, *u, bad, 6), lambda: ResponseProblem(m, *u, bad, 6, 'D')):
        with pytest.raises(ValueError, match='T'):
            call()

@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf, 0, -1, 1.9, True])
def test_b2_integer_arguments(case, bad):
    m, u = case
    for call in (lambda: simulate(m, *u, 3, bad), lambda: ResponseProblem(m, *u, 3, bad, 'D'),
                 lambda: response(m, u, 3, 6, 'D', 11, starts=bad)):
        with pytest.raises(ValueError, match='positive integer'):
            call()

@pytest.mark.parametrize('kind', ['empty', 'one_dimensional', 'mismatched'])
def test_b2_plan_shape(case, kind):
    m, u = case
    if kind == 'empty': u = tuple(x[:0] for x in u)
    elif kind == 'one_dimensional': u = tuple(x[0] for x in u)
    else: u = (u[0], u[1][:1], u[2])
    for call in (lambda: simulate(m, *u, 3, 6), lambda: ResponseProblem(m, *u, 3, 6, 'D')):
        with pytest.raises(ValueError): call()


def test_b2_no_entries(case):
    m, u = case
    m = replace(m, entry=np.zeros(m.n, dtype=bool), alpha=np.zeros(m.n))
    u = (np.zeros_like(u[0]), *u[1:])
    simulate(m, *u, 3, 6)
    with pytest.raises(ValueError, match='entry'):
        ResponseProblem(m, *u, 3, 6, 'A')

@pytest.mark.parametrize('player', ['D', 'A'])
def test_b3_decay_failure_and_refinement(case, player):
    m, _ = case
    m = replace(m, beta=np.zeros_like(m.beta), delta=np.full(m.n, 10.))
    z = np.zeros((1, m.n))
    with pytest.raises(FloatingPointError, match='left'):
        simulate(m, z, z, z, 1, 1)
    p = ResponseProblem(m, z, z, z, 1, 1, player)
    with pytest.raises(FloatingPointError, match='left'):
        p.value_gradient(p.initial)
    sim = simulate(m, z, z, z, 1, 100)
    np.testing.assert_allclose(sim['states'][-1], m.x0*np.exp(-10), atol=5e-11, rtol=0)
    p = ResponseProblem(m, z, z, z, 1, 100, player)
    value, grad = p.value_gradient(p.initial)
    assert value == pytest.approx(sim['J_D'] if player == 'D' else -sim['J_A'])
    assert np.all(np.isfinite(grad))


def test_b3_capacity_extension(case):
    m, u = case
    p = ResponseProblem(m, *u, 3, 6, 'D')
    v = np.full_like(p.initial, .4)
    assert p.violation(v) > 0
    value, grad = p.value_gradient(v)
    assert np.isfinite(value) and np.all(np.isfinite(grad))
    dv = np.zeros_like(v); dv[0] = 1e-6
    assert (p.value_gradient(v+dv)[0]-p.value_gradient(v-dv)[0])/2e-6 == pytest.approx(grad[0], abs=1e-8)

@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf])
def test_b3_nonfinite_integration(case, bad, monkeypatch):
    m, u = case
    with pytest.raises(FloatingPointError): check_integration(np.array([bad, 0.]), 1)
    monkeypatch.setattr(solver, 'state_jacobian', lambda *args: np.full((m.n, m.n), bad))
    p = ResponseProblem(m, *u, 3, 6, 'D')
    with np.errstate(invalid='ignore'):
        with pytest.raises(FloatingPointError, match='sensitivity'):
            p.value_gradient(p.initial)

@pytest.mark.parametrize('diagonal', [1e-9, 1e-300, -1e-9])
def test_b4_strict_zero_diagonal(case, diagonal):
    m, _ = case
    b = m.beta.copy(); b[0, 0] = diagonal
    with pytest.raises(ValueError, match='diagonal'): validate_model(replace(m, beta=b))

@pytest.mark.parametrize('alpha', [0., -1.])
def test_b4_positive_entry(case, alpha):
    m, _ = case
    a = m.alpha.copy(); a[np.flatnonzero(m.entry)[0]] = alpha
    with pytest.raises(ValueError, match='positive'): validate_model(replace(m, alpha=a))

@pytest.mark.parametrize('player', ['D', 'A'])
def test_b1_failed_optimizer_cannot_return_quality(case, player, monkeypatch):
    from types import SimpleNamespace
    m, u = case
    monkeypatch.setattr(solver, 'minimize', lambda *a, **kw: SimpleNamespace(x=np.full_like(a[1], np.nan)))
    with pytest.raises(ValueError, match='finite'):
        response(m, u, 3, 6, player, 11, starts=1)


def test_b3_nonfinite_objective(case, monkeypatch):
    import src.core as core
    m, u = case
    monkeypatch.setattr(core, 'cost_rates', lambda *a: np.full(6, np.inf))
    with pytest.raises(FloatingPointError, match='Non-finite'):
        simulate(m, *u, 3, 6)
