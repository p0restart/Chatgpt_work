"""Local constrained responses in a K-slot open-loop class; no Nash certificate."""
from __future__ import annotations
import time
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize
from .core import dynamics, check_controls, validate_model


def state_jacobian(m, x, a, s, r):
    z = m.alpha * a + m.beta.T @ (x * (1 - m.epsilon * s))
    jac = (1 - x)[:, None] * m.beta.T * (1 - m.epsilon * s)[None, :]
    jac[np.diag_indices(m.n)] = -z - m.delta - m.gamma * r
    return jac


class ResponseProblem:
    """RK4 direct shooting with exact derivatives of the discrete RK4 map.

    The objective is extended outside the capacity polytope for line searches.
    Feasibility is enforced by linear constraints and checked before acceptance.
    """
    def __init__(self, m, a, s, r, T, substeps, player):
        validate_model(m)
        check_controls(m, a, s, r)
        if player not in ('D', 'A') or T <= 0 or substeps < 1:
            raise ValueError('Invalid response problem')
        self.m, self.a, self.s, self.r = m, a.copy(), s.copy(), r.copy()
        self.T, self.substeps, self.player = T, int(substeps), player
        self.K = a.shape[0]
        self.entries = np.flatnonzero(m.entry)
        self.width = 2*m.n if player == 'D' else len(self.entries)
        self.weights = np.r_[m.b_s, m.b_r] if player == 'D' else m.d_a[self.entries]
        self.capacity = m.B if player == 'D' else m.A
        self.C = np.kron(np.eye(self.K), self.weights[None, :])
        self.initial = (np.c_[s, r] if player == 'D' else a[:, self.entries]).ravel()

    def schedules(self, v):
        a, s, r = self.a.copy(), self.s.copy(), self.r.copy()
        u = np.asarray(v).reshape(self.K, self.width)
        if self.player == 'D':
            s, r = u[:, :self.m.n], u[:, self.m.n:]
        else:
            a[:, self.entries] = u
        return a, s, r

    def value_gradient(self, v):
        m, n, d = self.m, self.m.n, len(v)
        a_all, s_all, r_all = self.schedules(v)
        y = np.r_[m.x0, 0.0]
        sens = np.zeros((n+1, d))
        dt = self.T / (self.K * self.substeps)
        for k in range(self.K):
            a, s, r = a_all[k], s_all[k], r_all[k]
            def rhs(y0, S):
                x = y0[:n]
                J = np.zeros((n+1, n+1))
                J[:n, :n] = state_jacobian(m, x, a, s, r)
                U = np.zeros((n+1, self.width))
                if self.player == 'D':
                    cost = m.q @ x + m.h @ s + .5*(m.c_s @ (s*s) + m.c_r @ (r*r))
                    J[n, :n] = m.q
                    U[:n, :n] = -(1-x)[:, None] * m.beta.T * (m.epsilon*x)[None, :]
                    U[:n, n:] = np.diag(-m.gamma*x)
                    U[n] = np.r_[m.h + m.c_s*s, m.c_r*r]
                else:
                    cost = -m.g @ x + .5*m.c_a @ (a*a)
                    J[n, :n] = -m.g
                    U[:n] = np.diag(m.alpha*(1-x))[:, self.entries]
                    U[n] = (m.c_a*a)[self.entries]
                ds = J @ S
                ds[:, k*self.width:(k+1)*self.width] += U
                return np.r_[dynamics(m, x, a, s, r), cost], ds
            for _ in range(self.substeps):
                f1, g1 = rhs(y, sens)
                f2, g2 = rhs(y+dt/2*f1, sens+dt/2*g1)
                f3, g3 = rhs(y+dt/2*f2, sens+dt/2*g2)
                f4, g4 = rhs(y+dt*f3, sens+dt*g3)
                y += dt/6*(f1+2*f2+2*f3+f4)
                sens += dt/6*(g1+2*g2+2*g3+g4)
        terminal = m.omega if self.player == 'D' else -m.nu
        return float(y[n]+terminal @ y[:n]), sens[n]+terminal @ sens[:n]

    def violation(self, v):
        return float(max(0, np.max(-v), np.max(v-1), np.max(self.C @ v-self.capacity)))

    def projected_residual(self, v, grad):
        """Infinity norm of v-Proj_C(v-grad), unit-step first-order residual."""
        z = (v-grad).reshape(self.K, self.width)
        projected = []
        for row in z:
            lo, hi = 0.0, max(1.0, float(np.max(row/self.weights)))
            for _ in range(80):
                mid = (lo+hi)/2
                if self.weights @ np.clip(row-mid*self.weights, 0, 1) > self.capacity:
                    lo = mid
                else:
                    hi = mid
            projected.append(np.clip(row-hi*self.weights, 0, 1))
        return float(np.max(np.abs(v-np.asarray(projected).ravel())))


def local_best_response(problem, seed=11, starts=3, maxiter=300, ftol=1e-10):
    rng = np.random.default_rng(seed)
    initial = problem.initial.copy()
    candidates = [initial, np.zeros_like(initial)]
    for _ in range(max(0, starts-2)):
        z = rng.uniform(0, 1, (problem.K, problem.width))
        z *= np.minimum(1, problem.capacity/(z @ problem.weights+1e-30))[:, None]
        candidates.append(z.ravel())
    candidates = candidates[:starts]
    best_v = initial.copy()
    best_val = problem.value_gradient(initial)[0]
    trace = []
    for j, start in enumerate(candidates):
        t0 = time.perf_counter()
        f0 = problem.value_gradient(start)[0]
        res = minimize(problem.value_gradient, start, jac=True, method='SLSQP',
                       bounds=Bounds(0, 1),
                       constraints=[LinearConstraint(problem.C, -np.inf, problem.capacity)],
                       options={'maxiter': maxiter, 'ftol': ftol})
        val, grad = problem.value_gradient(res.x)
        violation = problem.violation(res.x)
        accepted = bool(np.isfinite(val) and violation <= 1e-10 and val <= best_val)
        if accepted:
            best_val, best_v = val, res.x.copy()
        trace.append(dict(start=j, initial_objective=f0, objective=val,
                          success=bool(res.success), status=int(res.status), message=str(res.message),
                          nit=int(res.nit), nfev=int(res.nfev), njev=int(res.njev),
                          seconds=time.perf_counter()-t0, violation=violation,
                          projected_residual=problem.projected_residual(res.x, grad),
                          accepted=accepted, initial_control=start.tolist(), control=res.x.tolist()))
    return best_v, trace
