"""Bounded read-only model diagnostics; writes audit evidence only, not experiments."""
from pathlib import Path
from dataclasses import replace
import hashlib
import json
import platform
import warnings
import numpy as np
import scipy
from scipy.optimize import minimize
import yaml
from src.core import synthetic_model_from_config, simulate, validate_model
from src.game_solver import ResponseProblem, response
from src.supplement_c2 import independent_values


def main():
    cfg = yaml.safe_load(Path('configs/p2.yaml').read_text(encoding='utf-8'))
    m = synthetic_model_from_config(cfg)
    a = np.zeros((2, m.n)); a[:, m.entry] = .2
    s = np.full_like(a, .1); r = s.copy()
    u = (a, s, r)
    out = {'date': '2026-11-05', 'python': platform.python_version(),
           'numpy': np.__version__, 'scipy': scipy.__version__}
    # Independent integrator and nonzero terminal weights, without optimization.
    mt = replace(m, omega=np.arange(m.n)*.2, nu=np.arange(m.n)*.1)
    ref = independent_values(mt, u, 3.)
    out['integration'] = []
    for h in (3, 6, 12, 24):
        v = simulate(mt, *u, 3., h)
        out['integration'].append({'substeps': h,
            'error': float(np.max(abs(ref-[v['J_D'], v['J_A']]))),
            'state_min': float(v['states'].min()), 'state_max': float(v['states'].max())})
    # Heterogeneous capacity weights: compare projection to independent QP.
    mw = replace(m, b_s=np.array([.2, .5, 1., 2.]), b_r=np.array([.3, .7, 1.2, 1.5]))
    pr = ResponseProblem(mw, *u, 3., 6, 'D')
    rng = np.random.default_rng(20261105)
    discrepancies = []
    for _ in range(6):
        grad = rng.normal(size=pr.initial.size)
        z = pr.initial-grad
        qp = minimize(lambda v: (.5*np.sum((v-z)**2), v-z), pr.initial,
                      jac=True, bounds=list(zip(np.zeros_like(z), pr.upper)),
                      constraints=[{'type': 'ineq', 'fun': lambda v: pr.capacity-pr.C@v,
                                    'jac': lambda v: -pr.C}], method='SLSQP',
                      options={'ftol': 1e-12, 'maxiter': 100})
        assert qp.success
        discrepancies.append(abs(pr.projected_residual(pr.initial, grad)-np.max(abs(pr.initial-qp.x))))
    out['weighted_projection_max_residual_difference'] = float(max(discrepancies))
    pr = ResponseProblem(m, *u, 3., 6, 'D')
    out['nan_violation'] = pr.violation(np.full_like(pr.initial, np.nan))
    out['invalid_response_inputs'] = []
    for T, steps in [(float('nan'), 6), (float('inf'), 6), (3., 1.9)]:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                p = ResponseProblem(m, *u, T, steps, 'D')
                val, grad = p.value_gradient(p.initial)
                result = {'accepted': True, 'stored_steps': p.substeps,
                          'finite_value': bool(np.isfinite(val)), 'finite_gradient': bool(np.all(np.isfinite(grad)))}
            except Exception as e:
                result = {'accepted': False, 'exception': type(e).__name__}
        out['invalid_response_inputs'].append({'T': str(T), 'steps': steps, **result})
    try:
        _, info = response(m, u, 3., 6, 'D', 11, starts=0)
        out['zero_starts'] = {'all_starts_success': info['all_starts_success'], 'raw_count': len(info['raw'])}
    except Exception as e:
        out['zero_starts'] = {'exception': type(e).__name__, 'message': str(e)}
    # Valid continuous model, deliberately inadequate RK4 step: x'=-10x.
    stiff = replace(m, beta=np.zeros_like(m.beta), delta=np.full(m.n, 10.))
    zero = np.zeros((1, m.n))
    coarse = simulate(stiff, zero, zero, zero, 1., 1)
    out['coarse_rk4_counterexample'] = {'returned_without_exception': True,
        'terminal_first': float(coarse['states'][-1, 0]), 'exact_terminal_first': float(m.x0[0]*np.exp(-10)),
        'J_D': coarse['J_D']}
    # Validator's zero-diagonal tolerance versus analytic Jacobian assumption.
    b = m.beta.copy(); b[0, 0] = 1e-9
    validate_model(replace(m, beta=b))
    out['accepted_nonzero_diagonal'] = 1e-9
    validate_model(replace(m, alpha=np.zeros(m.n)))
    out['accepted_zero_entry_alpha'] = True
    # Check existing finite tables algebraically; no new trajectories/table generation.
    out['saved_finite_tables'] = []
    for folder in sorted(Path('results/supplement_c2/run02/finite').glob('B*/step*')):
        t = np.load(folder/'payoffs_48.npz'); d, a = t['J_D'], t['J_A']
        regret = np.maximum(d-d.min(axis=0)[None, :], a.max(axis=1)[:, None]-a)
        out['saved_finite_tables'].append({'path': str(folder), 'pairs': int(d.size),
            'all_finite': bool(np.all(np.isfinite(d)) and np.all(np.isfinite(a))),
            'pure_count_at_1e_8': int(np.sum(regret <= 1e-8)), 'minimum_max_regret': float(regret.min())})
    sources = ['02_MODEL_SPEC.md', 'DECISIONS.md', 'src/core.py', 'src/game_solver.py',
               'src/supplement_c2.py', 'src/matched_mechanism.py', *[str(p) for p in Path('tests').glob('test_*.py')]]
    out['source_sha256'] = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}
    target = Path('handoffs/B_math_diagnostic.json')
    target.write_text(json.dumps(out, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
