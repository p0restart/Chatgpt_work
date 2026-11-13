"""Deterministic multi-asset attack propagation model.

IMPORTANT: This module provides validated dynamics and trajectory integration only.
It does NOT compute a best response or a Nash equilibrium.

Conventions: beta[j, i] = propagation rate from origin j TO destination i;
s[j] reduces all effective propagation outgoing from origin j.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Model:
    beta: np.ndarray
    alpha: np.ndarray
    epsilon: np.ndarray
    delta: np.ndarray
    gamma: np.ndarray
    q: np.ndarray
    h: np.ndarray
    c_s: np.ndarray
    c_r: np.ndarray
    g: np.ndarray
    c_a: np.ndarray
    omega: np.ndarray
    nu: np.ndarray
    b_s: np.ndarray
    b_r: np.ndarray
    d_a: np.ndarray
    entry: np.ndarray
    x0: np.ndarray
    B: float
    A: float

    @property
    def n(self) -> int:
        return self.x0.size


def validate_model(m: Model) -> None:
    n = m.n
    if n < 2 or m.beta.shape != (n, n):
        raise ValueError("Invalid beta matrix or n")
    if not np.all(np.isfinite(m.beta)) or np.any(m.beta < 0) or np.any(np.diag(m.beta) != 0):
        raise ValueError("beta must be nonnegative, finite, and have a zero diagonal")
    for name in ("alpha", "epsilon", "delta", "gamma", "q", "h", "c_s", "c_r", "g", "c_a", "omega", "nu", "b_s", "b_r", "d_a", "x0"):
        x = getattr(m, name)
        if x.shape != (n,) or not np.all(np.isfinite(x)):
            raise ValueError(f"Invalid vector {name}")
    if m.entry.shape != (n,) or m.entry.dtype != np.dtype(bool):
        raise ValueError("entry must be a length-n boolean mask")
    if np.any(m.alpha[m.entry] <= 0) or np.any(m.alpha[~m.entry] != 0):
        raise ValueError("alpha must be positive on entry assets and zero elsewhere")
    if np.any(m.epsilon <= 0) or np.any(m.epsilon > 1):
        raise ValueError("isolation effectiveness epsilon must lie in (0,1]")
    for name in ("delta", "gamma", "q", "h", "g", "omega", "nu"):
        if np.any(getattr(m, name) < 0):
            raise ValueError(f"{name} must be nonnegative")
    for name in ("c_s", "c_r", "c_a", "b_s", "b_r", "d_a"):
        if np.any(getattr(m, name) <= 0):
            raise ValueError(f"{name} must be strictly positive")
    if (np.any(m.x0 < 0) or np.any(m.x0 > 1) or
            not np.isfinite(m.A) or not np.isfinite(m.B) or m.A < 0 or m.B < 0):
        raise ValueError("Initial state must be in [0,1] and capacities nonnegative")


def check_controls(m: Model, a: np.ndarray, s: np.ndarray, r: np.ndarray, tol: float = 1e-10) -> None:
    """Validate single-slot or K-slot controls (same shapes) and per-slot budgets."""
    a, s, r = np.asarray(a), np.asarray(s), np.asarray(r)
    if a.ndim not in (1, 2) or a.shape != s.shape or a.shape != r.shape or a.shape[-1] != m.n:
        raise ValueError("a, s, r must have matching shape (..., n)")
    for name, control in (("a", a), ("s", s), ("r", r)):
        if not np.all(np.isfinite(control)) or np.any(control < -tol) or np.any(control > 1 + tol):
            raise ValueError(f"{name} outside [0,1]")
    if np.any(np.abs(a[..., ~m.entry]) > tol):
        raise ValueError("Non-entry asset has nonzero direct attack input")
    if np.any(np.sum(s * m.b_s + r * m.b_r, axis=-1) > m.B + tol):
        raise ValueError("Defense per-slot capacity exceeded")
    if np.any(np.sum(a * m.d_a, axis=-1) > m.A + tol):
        raise ValueError("Attack per-slot capacity exceeded")


def dynamics(m: Model, x: np.ndarray, a: np.ndarray, s: np.ndarray, r: np.ndarray) -> np.ndarray:
    """f_i = (1-x_i)(alpha_i a_i + sum_j beta[j,i](1-eps_j s_j)x_j) - (delta_i+gamma_i r_i)x_i."""
    outgoing_source_infectivity = x * (1 - m.epsilon * s)
    exposure = m.alpha * a + m.beta.T @ outgoing_source_infectivity
    return (1 - x) * exposure - (m.delta + m.gamma * r) * x


def cost_rates(m: Model, x: np.ndarray, a: np.ndarray, s: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Order: security, business, isolation, recovery, attacker_value, attacker_effort."""
    return np.array([
        np.dot(m.q, x),
        np.dot(m.h, s),
        0.5 * np.dot(m.c_s, s * s),
        0.5 * np.dot(m.c_r, r * r),
        np.dot(m.g, x),
        0.5 * np.dot(m.c_a, a * a),
    ], dtype=float)


def positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not np.isscalar(value) or not np.isfinite(value) or value < 1 or int(value) != value:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def validate_plan(m, a, s, r, T, substeps):
    if not np.isscalar(T) or not np.isfinite(T) or T <= 0:
        raise ValueError("T must be finite and positive")
    steps = positive_integer(substeps, 'substeps')
    a, s, r = (np.asarray(u, dtype=float) for u in (a, s, r))
    if a.ndim != 2 or a.shape[0] < 1:
        raise ValueError("Expected nonempty 2D schedules")
    check_controls(m, a, s, r)
    return a, s, r, steps


def check_integration(y, n, enforce_domain=True):
    """Check completed RK4 steps, without clipping or changing the step size."""
    if not np.all(np.isfinite(y)):
        raise FloatingPointError("Non-finite RK4 state or accumulated objective")
    if enforce_domain and (np.any(y[:n] < -1e-10) or np.any(y[:n] > 1 + 1e-10)):
        raise FloatingPointError("RK4 state left [0,1]; refine integration explicitly")


def simulate(m: Model, a_schedule: np.ndarray, s_schedule: np.ndarray, r_schedule: np.ndarray,
             T: float, substeps_per_slot: int = 12) -> dict:
    """Run fixed-piecewise-constant open-loop schedules with augmented RK4 costs.

    Note: these controls are GIVEN, not optimized. Does not imply best response/Nash.
    """
    validate_model(m)
    a_schedule, s_schedule, r_schedule, substeps_per_slot = validate_plan(
        m, a_schedule, s_schedule, r_schedule, T, substeps_per_slot)
    K = a_schedule.shape[0]
    if K < 1:
        raise ValueError("Expected at least one control slot")
    h = T / (K * substeps_per_slot)
    y = np.r_[np.asarray(m.x0, dtype=float), np.zeros(6)]
    times = [0.0]
    states = [y[:m.n].copy()]

    def augmented_rhs(z: np.ndarray, a: np.ndarray, s: np.ndarray, r: np.ndarray) -> np.ndarray:
        x = z[:m.n]
        return np.r_[dynamics(m, x, a, s, r), cost_rates(m, x, a, s, r)]

    for k in range(K):
        a, s, r = a_schedule[k], s_schedule[k], r_schedule[k]
        for j in range(substeps_per_slot):
            k1 = augmented_rhs(y, a, s, r)
            k2 = augmented_rhs(y + (h / 2) * k1, a, s, r)
            k3 = augmented_rhs(y + (h / 2) * k2, a, s, r)
            k4 = augmented_rhs(y + h * k3, a, s, r)
            y = y + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            check_integration(y, m.n)
            times.append((k * substeps_per_slot + j + 1) * h)
            states.append(y[:m.n].copy())

    security, business, isolation, recovery, attacker_value, attacker_effort = y[m.n:]
    terminal_defense = float(np.dot(m.omega, y[:m.n]))
    terminal_attacker = float(np.dot(m.nu, y[:m.n]))
    parts = {
        "security": float(security),
        "business": float(business),
        "isolation": float(isolation),
        "recovery": float(recovery),
        "terminal_defense": terminal_defense,
        "attacker_value": float(attacker_value),
        "attacker_effort": float(attacker_effort),
        "terminal_attacker": terminal_attacker,
    }
    J_D = sum(parts[key] for key in ("security", "business", "isolation", "recovery", "terminal_defense"))
    J_A = parts["attacker_value"] - parts["attacker_effort"] + parts["terminal_attacker"]
    if not np.all(np.isfinite([*parts.values(), J_D, J_A])):
        raise FloatingPointError("Non-finite terminal objective")
    return {"times": np.asarray(times), "states": np.asarray(states), "parts": parts,
            "J_D": float(J_D), "J_A": float(J_A)}


def synthetic_model_from_config(cfg: dict) -> Model:
    """Deterministic example graph; explicitly exploratory, not a calibrated cloud graph.

    For formal experiments Work must save the exact edge list and check network strength.
    """
    n = int(cfg["n"])
    rng = np.random.default_rng(int(cfg["seed"]))
    beta = np.zeros((n, n))
    topology = cfg.get("network", "modular")
    if topology == "modular":
        edges = [(j, (j + 1) % n) for j in range(n)]
        edges += [(j, (j + 2) % n) for j in range(0, n, 2)]
        edges += [(0, n - 1), (1, n - 2)]
    elif topology == "chain":
        edges = [(j, j + 1) for j in range(n - 1)]
    elif topology == "star":
        edges = [(0, j) for j in range(1, n)] + [(j, 0) for j in range(1, n)]
    else:
        raise ValueError("unknown network topology")
    w_min, w_max = map(float, cfg["beta_nonzero_range"])
    if not (0 <= w_min <= w_max):
        raise ValueError("invalid beta weight range")
    for j, i in sorted(set(edges)):
        if j != i:
            beta[j, i] = rng.uniform(w_min, w_max)
    entry = np.zeros(n, dtype=bool)
    entry[np.asarray(cfg["attack_entry_indices"], dtype=int)] = True
    def const(key: str) -> np.ndarray:
        return np.full(n, float(cfg[key]))
    alpha = np.where(entry, float(cfg["alpha_entry"]), 0.0)
    out_strength = beta.sum(axis=1)
    high_spread = int(np.argmax(out_strength))
    low_spread = int(np.argmin(out_strength))
    scenario = cfg.get("scenario", "separated")
    q = const("q_normal")
    h = const("h_normal")
    if scenario == "aligned":
        q[high_spread] = float(cfg["q_high"])
    elif scenario == "separated":
        q[low_spread] = float(cfg["q_high"])
    elif scenario == "business_cost":
        q[low_spread] = float(cfg["q_high"])
        h[high_spread] = float(cfg["h_high"])
    else:
        raise ValueError("unknown scenario")
    return Model(beta=beta, alpha=alpha, epsilon=const("epsilon"), delta=const("delta"),
                 gamma=const("gamma"), q=q, h=h, c_s=const("c_s"), c_r=const("c_r"),
                 g=const("g"), c_a=const("c_a"), omega=const("omega"), nu=const("nu"),
                 b_s=const("b_s"), b_r=const("b_r"), d_a=const("d_a"), entry=entry,
                 x0=np.asarray(cfg["x0"], dtype=float), B=float(cfg["B"]), A=float(cfg["A"]))
