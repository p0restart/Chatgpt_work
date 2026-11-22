import argparse
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter

for thread_variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[thread_variable] = '1'

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
REVISION = '1409b7e71451564613c1ded61762a2724d0d0b98'
FILES = ('src/__init__.py', 'src/core.py', 'src/game_solver.py', 'paper/work_d7/config_new_topology.yaml')
ASSETS = ('API 网关', 'Web 应用', '订单处理', '身份认证', '核心数据库', '后台管理')
PARTS = ('security', 'business', 'isolation', 'recovery', 'terminal_defense')
K, H = 12, 48
OPTIONS = dict(starts=3, maxiter=300, ftol=1e-10)
CHINA = timezone(timedelta(hours=8))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                               default=lambda element: element.tolist()) + '\n', encoding='utf-8')


def table(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False, encoding='utf-8-sig', float_format='%.17g')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def maximum(values):
    return float(np.max(np.abs(values)))


def sources(out):
    bundled = HERE / 'A_source'
    if bundled.is_dir():
        reference = json.loads((HERE / 'A_run_config.json').read_text(encoding='utf-8'))
        checksums = reference['source_sha256']
        for name in FILES:
            if digest(bundled / name) != checksums[name]:
                raise RuntimeError(f'Frozen source hash mismatch: {name}')
        return bundled, checksums
    for name in FILES:
        committed = subprocess.check_output(['git', 'show', f'{REVISION}:{name}'], cwd=REPO)
        working = (REPO / name).read_bytes()
        if committed.replace(b'\r\n', b'\n') != working.replace(b'\r\n', b'\n'):
            raise RuntimeError(f'Working source differs from frozen revision: {name}')
        target = out / 'A_source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(working)
    return out / 'A_source', {name: digest(out / 'A_source' / name) for name in FILES}


class Experiment:
    def __init__(self, out):
        self.out = out
        source, checksums = sources(out)
        sys.path.insert(0, str(source))
        from src import core, game_solver

        self.core, self.solver = core, game_solver
        frozen = yaml.safe_load((source / FILES[-1]).read_text(encoding='utf-8'))
        self.model = core.Model(**{field.name: np.asarray(frozen[field.name])
                                 if isinstance(frozen[field.name], list) else frozen[field.name]
                                 for field in fields(core.Model)})
        core.validate_model(self.model)
        self.dt = frozen['T'] / K
        self.seed = frozen['seed']
        self.base = np.asarray(frozen['a0'], dtype=float)
        self.cap = min(1., (self.model.A - self.base[1:] @ self.model.d_a[1:]) / self.model.d_a[0])
        self.request = np.repeat([.20, .50, .20], 4)
        self.actual = np.clip(self.request, 0., self.cap)
        self.checks = []
        self.uniform = min(.5, self.model.B / np.sum(self.model.b_s + self.model.b_r))
        self.plans = {}
        self.traces = {}
        dump(out / 'A_run_config.json', dict(
            model=asdict(self.model), assets=ASSETS, frozen_config=frozen, T=frozen['T'], K=K,
            slot_width=self.dt, H=H, refine_H=[96, 192], requested_api=self.request,
            executed_api=self.actual, api_ceiling=self.cap, event_slots=[5, 9],
            seeds=dict(D0=self.seed, slot5=self.seed+1, slot9=self.seed+2), solver=OPTIONS,
            initial_uniform_control=self.uniform, random_generator='numpy.default_rng',
            revision=REVISION, source_sha256=checksums, driver_sha256=digest(Path(__file__)),
            protocol_sha256=digest(HERE / 'A_experiment_protocol.md'),
            packages={item: importlib.metadata.version(item)
                      for item in ('numpy', 'scipy', 'PyYAML', 'pandas', 'matplotlib')},
            python=sys.version, platform=platform.platform(), numeric_threads=1))

    def check(self, label, measured, limit):
        passed = bool(np.isfinite(measured) and measured <= limit)
        self.checks.append(dict(check=label, measured=float(measured), limit=limit, passed=passed))
        if not passed:
            raise RuntimeError(f'{label}: {measured:.6g} > {limit:.6g} or non-finite')

    def attack(self, observed):
        observed = np.asarray(observed)
        attack = np.tile(self.base, (len(observed), 1))
        attack[:, 0] = observed
        return attack

    def evaluate(self, initial, controls, steps=H):
        model = replace(self.model, x0=initial)
        return self.core.simulate(model, *controls, self.dt * len(controls[0]), steps)

    def integrate_and_audit(self, label, initial, controls):
        coarse = self.evaluate(initial, controls)
        for steps in (2*H, 4*H):
            fine = self.evaluate(initial, controls, steps)
            self.check(f'{label} H{steps} time grid', maximum(fine['times'][::steps//H]-coarse['times']), 1e-12)
            self.check(f'{label} H{steps} state', maximum(fine['states'][::steps//H]-coarse['states']), 1e-6)
            self.check(f'{label} H{steps} J_D', abs(fine['J_D']-coarse['J_D']), 1e-6)
            for key in PARTS:
                self.check(f'{label} H{steps} {key}', abs(fine['parts'][key]-coarse['parts'][key]), 1e-6)
        usage = controls[1] * self.model.b_s + controls[2] * self.model.b_r
        self.check(f'{label} defense capacity', max(0., float(usage.sum(1).max()-self.model.B)), 1e-10)
        self.check(f'{label} attack capacity', max(0., float((controls[0] @ self.model.d_a).max()-self.model.A)), 1e-10)
        self.check(f'{label} control box', max(0., float(-np.min(controls)), float(np.max(controls)-1)), 1e-10)
        self.check(f'{label} state bounds', max(0., float(-coarse['states'].min()), float(coarse['states'].max()-1)), 1e-10)
        return coarse

    def plan(self, label, start, initial, current_api, warm, seed):
        count = K-start
        forecast = self.attack(np.full(count, current_api))
        model = replace(self.model, x0=initial.copy())
        problem = self.solver.ResponseProblem(model, forecast, *warm, self.dt*count, H, 'D')
        logging.info('%s start_slot=%d count=%d observed_api=%.2f seed=%d x0=%s',
                     label, start+1, count, current_api, seed, initial.tolist())
        begin = perf_counter()
        vector, attempts = self.solver.local_best_response(problem, seed=seed, **OPTIONS)
        solve_seconds = perf_counter()-begin
        value, gradient = problem.value_gradient(vector)
        controls = problem.schedules(vector)
        self.traces[label] = dict(start_slot=start+1, seed=seed, observed_api=current_api,
                                  x0=initial, solve_seconds=solve_seconds, objective=value,
                                  selected_control=vector, attempts=attempts)
        dump(self.out / 'A_optimizer_trace.json', self.traces)
        for attempt in attempts:
            logging.info('%s start=%d status=%d nit=%d J0=%.12g J=%.12g residual=%.6g seconds=%.3f %s',
                         label, attempt['start'], attempt['status'], attempt['nit'], attempt['initial_objective'],
                         attempt['objective'], attempt['projected_residual'], attempt['seconds'], attempt['message'])
        self.check(f'{label} failed exits', sum(not attempt['success'] for attempt in attempts), 0)
        self.check(f'{label} worst start residual', max(attempt['projected_residual'] for attempt in attempts), 1e-4)
        self.check(f'{label} worst start violation', max(attempt['violation'] for attempt in attempts), 1e-10)
        self.check(f'{label} selected violation', problem.violation(vector), 1e-10)
        self.check(f'{label} selected residual H48', problem.projected_residual(vector, gradient), 1e-4)
        self.check(f'{label} spread of start objectives normalized', np.ptp([attempt['objective'] for attempt in attempts])/(1+abs(value)), 1e-7)
        self.check(f'{label} spread of start controls', maximum(np.ptp([attempt['control'] for attempt in attempts], axis=0)), 1e-3)
        self.check(f'{label} immutable attack forecast', maximum(controls[0]-forecast), 0)
        fine = self.solver.ResponseProblem(model, *controls, self.dt*count, 2*H, 'D')
        fine_value, fine_gradient = fine.value_gradient(vector)
        self.check(f'{label} selected residual H96', fine.projected_residual(vector, fine_gradient), 1e-4)
        probe = np.full_like(vector, self.uniform/2)
        _, derivative = problem.value_gradient(probe)
        for index in (0, len(vector)//2, len(vector)-1):
            perturb = np.zeros_like(probe)
            perturb[index] = 1e-6
            central = (problem.value_gradient(probe+perturb)[0]-problem.value_gradient(probe-perturb)[0])/2e-6
            self.check(f'{label} gradient {index}', abs(central-derivative[index]), 1e-6)
        replay = self.integrate_and_audit(label, initial, controls)
        self.check(f'{label} solver-vs-replay', abs(replay['J_D']-value), 1e-10)
        self.check(f'{label} fine solver-vs-replay', abs(self.evaluate(initial, controls, 2*H)['J_D']-fine_value), 1e-10)
        self.plans[label] = (start, controls, replay)
        logging.info('%s accepted; optimization %.3fs, replay J_D %.12g', label, solve_seconds, replay['J_D'])
        return controls

    def slot_rows(self, label, start, controls, replay):
        attack, isolation, recovery = controls
        resources = isolation*self.model.b_s + recovery*self.model.b_r
        for slot in range(len(attack)):
            for asset, name in enumerate(ASSETS):
                yield dict(label=label, slot=start+slot+1, asset=asset+1, asset_name=name,
                           t_start=(start+slot)*self.dt, t_end=(start+slot+1)*self.dt,
                           a=attack[slot, asset], s=isolation[slot, asset], r=recovery[slot, asset],
                           resource=resources[slot, asset], total_defense=resources[slot].sum(),
                           total_attack=attack[slot] @ self.model.d_a,
                           x_start=replay['states'][slot*H, asset], x_end=replay['states'][(slot+1)*H, asset])

    def run(self):
        model = self.model
        actual_attack = self.attack(self.actual)
        normal_attack = self.attack(np.full(K, self.actual[0]))
        normal, high, restored = self.actual[[0, 4, 8]]
        candidate = self.attack(self.request)
        self.check('requested peak budget excess is 0.10', abs((candidate[4]@model.d_a-model.A)-.1), 1e-12)
        self.check('actual attack events at slots 5 and 9', maximum(np.flatnonzero(np.diff(self.actual))+2-[5, 9]), 0)
        self.check('other assets unchanged from D7', maximum(actual_attack[:, 1:]-self.base[1:]), 0)
        uniform = np.full((K, model.n), self.uniform)
        self.core.check_controls(model, actual_attack, uniform, uniform)
        self.core.check_controls(model, normal_attack, uniform, uniform)
        logging.info('Feasibility: requested=%s applied=%s', self.request.tolist(), self.actual.tolist())
        initial_plan = self.plan('D0', 0, model.x0, normal, (uniform, uniform), self.seed)
        first = (actual_attack[:4], initial_plan[1][:4], initial_plan[2][:4])
        x4 = self.evaluate(model.x0, first)['states'][-1]
        warm5 = (initial_plan[1][4:], initial_plan[2][4:])
        raised = self.plan('D1', 4, x4, high, warm5, self.seed+1)
        second = (actual_attack[4:8], raised[1][:4], raised[2][:4])
        x8 = self.evaluate(x4, second)['states'][-1]
        warm9 = (raised[1][4:], raised[2][4:])
        lowered = self.plan('D2', 8, x8, restored, warm9, self.seed+2)
        self.plan('M5_old', 4, x4, normal, warm5, self.seed+1)
        self.plan('M9_old', 8, x8, high, warm9, self.seed+2)
        systems = dict(C0=initial_plan, C1=(actual_attack, *initial_plan[1:]),
                       C2=(actual_attack, *(np.concatenate((first[channel], second[channel], lowered[channel]))
                                             for channel in (1, 2))))
        runs = {key: self.integrate_and_audit(key, model.x0, controls) for key, controls in systems.items()}
        self.check('C1/C2 share attack', maximum(systems['C1'][0]-systems['C2'][0]), 0)
        for name in systems:
            self.check(f'{name} initial state', maximum(runs[name]['states'][0]-model.x0), 0)
            self.check(f'{name} first 4 slots same prefix', maximum(runs[name]['states'][:4*H+1]-runs['C0']['states'][:4*H+1]), 1e-12)
        self.check('C2 passes actual t4 state', maximum(runs['C2']['states'][4*H]-x4), 1e-12)
        self.check('C2 passes actual t8 state', maximum(runs['C2']['states'][8*H]-x8), 1e-12)
        self.check('D1 does not foresee slot9 drop', maximum(raised[0][:, 0]-high), 0)
        self.check('D0 has only normal input', maximum(initial_plan[0][:, 0]-normal), 0)
        self.check('D2 has only restored input', maximum(lowered[0][:, 0]-restored), 0)
        for new, old in (('D1', 'M5_old'), ('D2', 'M9_old')):
            self.check(f'{new}/{old} matched state', maximum(self.traces[new]['x0']-self.traces[old]['x0']), 0)
            for new_start, old_start in zip(self.traces[new]['attempts'], self.traces[old]['attempts']):
                self.check(f'{new}/{old} matched start {new_start["start"]}',
                           maximum(np.asarray(new_start['initial_control'])-old_start['initial_control']), 0)
        self.export(systems, runs)

    def export(self, systems, runs):
        out = self.out
        table(out / 'A_results.csv', [row for label, controls in systems.items()
                                      for row in self.slot_rows(label, 0, controls, runs[label])])
        table(out / 'A_plans.csv', [row for label, plan in self.plans.items() for row in self.slot_rows(label, *plan)])
        matched = []
        for new, old in (('D1', 'M5_old'), ('D2', 'M9_old')):
            for lhs, rhs in zip(self.slot_rows(new, *self.plans[new]), self.slot_rows(old, *self.plans[old])):
                row = {key: lhs[key] for key in ('slot', 'asset', 'asset_name', 't_start', 't_end')}
                row.update(event_slot=self.plans[new][0]+1, state_at_event=self.traces[new]['x0'][row['asset']-1],
                           old_api=self.traces[old]['observed_api'], new_api=self.traces[new]['observed_api'])
                for key in ('a', 's', 'r', 'resource', 'total_defense', 'x_start', 'x_end'):
                    row.update({f'old_{key}': rhs[key], f'new_{key}': lhs[key], f'delta_{key}': lhs[key]-rhs[key]})
                matched.append(row)
        table(out / 'A_matched_response.csv', matched)
        trajectories, metrics = [], []
        for label, result in runs.items():
            states = result['states']
            weighted = states @ self.model.q / self.model.q.sum()
            trajectories.extend(dict(label=label, time=instant, weighted_damage=value,
                                     **{f'x{number}': state[number-1] for number in range(1, 7)})
                                for instant, state, value in zip(result['times'], states, weighted))
            _, isolation, recovery = systems[label]
            use = (isolation*self.model.b_s + recovery*self.model.b_r).sum(axis=1)
            metrics.append(dict(label=label, J_D=result['J_D'], **{key: result['parts'][key] for key in PARTS},
                                api_terminal=states[-1, 0], api_peak=states[:, 0].max(),
                                db_terminal=states[-1, 4], db_peak=states[:, 4].max(),
                                weighted_terminal=weighted[-1], weighted_peak=weighted.max(),
                                max_defense=use.max(), capacity_ok=bool(use.max() <= self.model.B+1e-10),
                                binding_slots=int(np.count_nonzero(abs(use-self.model.B) <= 1e-8)),
                                loss_improvement_vs_C1=runs['C1']['J_D']-result['J_D'] if label != 'C0' else None,
                                relative_improvement_vs_C1=(runs['C1']['J_D']-result['J_D'])/runs['C1']['J_D'] if label != 'C0' else None))
        table(out / 'A_state_trajectories.csv', trajectories)
        table(out / 'A_metrics.csv', metrics)
        logging.info('Full replays J_D: %s', {label: result['J_D'] for label, result in runs.items()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'A_execution.log').exists():
        parser.error('use a fresh output directory; existing results are not overwritten')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s CST %(message)s',
                        handlers=[logging.FileHandler(out / 'A_execution.log', encoding='utf-8'), logging.StreamHandler()])
    logging.Formatter.converter = staticmethod(lambda timestamp: datetime.fromtimestamp(timestamp, CHINA).timetuple())
    experiment = None
    try:
        logging.info('Work A starts; frozen revision %s', REVISION)
        experiment = Experiment(out)
        experiment.run()
        logging.info('PASS %d numerical checks', len(experiment.checks))
    except Exception:
        logging.exception('Stopped; partial output preserved')
        raise
    finally:
        if experiment is not None:
            table(out / 'A_validation_checks.csv', experiment.checks)


if __name__ == '__main__':
    main()
