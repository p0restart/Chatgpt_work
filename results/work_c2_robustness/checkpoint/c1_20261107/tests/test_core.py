"""Checks starter dynamics only. Work must add full optimizer and experiment tests."""
from pathlib import Path
import numpy as np
import pytest
import yaml
from src.core import (Model, check_controls, dynamics, simulate,
                      synthetic_model_from_config, validate_model)


@pytest.fixture
def m():
    config = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    model = synthetic_model_from_config(config)
    validate_model(model)
    return model


def test_budget_and_entry(m):
    K = 3
    a = np.zeros((K, m.n))
    s = np.zeros_like(a)
    r = np.zeros_like(a)
    a[:, np.flatnonzero(m.entry)[0]] = 0.3
    s[:, 0] = 0.4
    r[:, 1] = 0.3
    check_controls(m, a, s, r)
    a[:, np.flatnonzero(~m.entry)[0]] = 0.01
    with pytest.raises(ValueError, match="Non-entry"):
        check_controls(m, a, s, r)
    a[:, ~m.entry] = 0
    s[:, :] = 1
    with pytest.raises(ValueError, match="Defense"):
        check_controls(m, a, s, r)


def test_origin_isolation_index(m):
    # Only source 0 outgoing terms vary when s_0 is increased.
    n = m.n
    x = np.linspace(0.2, 0.4, n)
    a = np.zeros(n)
    r = np.zeros(n)
    s0 = np.zeros(n)
    s1 = s0.copy()
    s1[0] = 0.8
    df = dynamics(m, x, a, s1, r) - dynamics(m, x, a, s0, r)
    expected = -(1 - x) * m.beta[0, :] * m.epsilon[0] * s1[0] * x[0]
    np.testing.assert_allclose(df, expected, atol=1e-12)
    assert df[0] == pytest.approx(0)


def test_invariant_domain_and_cost_decomposition(m):
    K = 6
    a = np.zeros((K, m.n))
    a[:, np.flatnonzero(m.entry)[0]] = 0.3
    s = np.zeros_like(a)
    r = np.zeros_like(a)
    r[:, 2] = 0.5
    out = simulate(m, a, s, r, T=10, substeps_per_slot=12)
    assert out["states"].shape == (6 * 12 + 1, m.n)
    assert np.min(out["states"]) >= -1e-8
    assert np.max(out["states"]) <= 1 + 1e-8
    p = out["parts"]
    assert out["J_D"] == pytest.approx(sum(p[k] for k in ("security", "business", "isolation", "recovery", "terminal_defense")))
    assert out["J_A"] == pytest.approx(p["attacker_value"] - p["attacker_effort"] + p["terminal_attacker"])


def test_rk4_step_refinement(m):
    K = 6
    a = np.zeros((K, m.n))
    a[:, 0] = 0.3
    s = np.zeros_like(a)
    r = np.zeros_like(a)
    rough = simulate(m, a, s, r, T=10, substeps_per_slot=6)
    fine = simulate(m, a, s, r, T=10, substeps_per_slot=24)
    assert abs(rough["J_D"] - fine["J_D"]) < 1e-5


def test_all_zero_state_stays_zero(m):
    # No attack input: zero initial state remains zero under all allowed defenses.
    d = {field: getattr(m, field) for field in m.__dataclass_fields__}
    d["x0"] = np.zeros(m.n)
    m0 = Model(**d)
    z = np.zeros((2, m.n))
    out = simulate(m0, z, z, z, T=2, substeps_per_slot=10)
    np.testing.assert_allclose(out["states"], 0, atol=1e-14)
