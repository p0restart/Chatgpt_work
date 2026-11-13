"""Bounded six-asset before/after regression; never writes historical results."""
import hashlib
import json
import platform
import sys
from pathlib import Path
import numpy as np
import scipy
from src.core import Model, simulate
from src.game_solver import ResponseProblem, local_best_response


def main():
    # Replay the frozen pre-fix implementation without replacing working sources.
    global Model, simulate, ResponseProblem, local_best_response
    source = Path('src')
    if '--before' in sys.argv[2:]:
        from handoffs.c1_evidence.before_source.core import Model, simulate
        from handoffs.c1_evidence.before_source.game_solver import ResponseProblem, local_best_response
        source = Path('handoffs/c1_evidence/before_source')
    case = Path('results/matched_mechanism/run01/seed11_B1.2_unequal_high_at_node3')
    inputs = [case/'model.json', case/'fine/controls.json']
    raw = json.loads(inputs[0].read_text())
    m = Model(**{k: np.asarray(v) if isinstance(v, list) else v for k, v in raw.items()})
    u = tuple(np.asarray(v) for v in json.loads(inputs[1].read_text()))
    out = dict(case=str(case), T=10, K=6, seed=11, starts=3,
               python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
               hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [*inputs, source/'core.py', source/'game_solver.py']})
    for steps in (12, 48):
        sim = simulate(m, *u, 10, steps)
        record = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in sim.items()}
        record['players'] = {}
        for player in ('D', 'A'):
            pr = ResponseProblem(m, *u, 10, steps, player)
            val, grad = pr.value_gradient(pr.initial)
            v, trace = local_best_response(pr, seed=11, starts=3)
            fv, fg = pr.value_gradient(v)
            for row in trace:
                row.pop('seconds')  # wall time is not a numerical invariant
            record['players'][player] = dict(value=val, gradient=grad.tolist(),
                violation=pr.violation(pr.initial), residual=pr.projected_residual(pr.initial, grad),
                control=v.tolist(), response_value=fv, response_gradient=fg.tolist(),
                response_violation=pr.violation(v), response_residual=pr.projected_residual(v, fg),
                slot_usage=(pr.C @ v).tolist(), trace=trace)
        out[str(steps)] = record
    target = Path(sys.argv[1])
    with target.open('x', encoding='utf-8') as f:
        json.dump(out, f, indent=2, allow_nan=False)
    print(target)


if __name__ == '__main__':
    main()
