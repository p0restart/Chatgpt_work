from pathlib import Path
import numpy as np
import yaml
from src.matched_mechanism import matched_model
from src.core import simulate
from src.experiments import initial_controls


def test_matched_graph_invariants_and_equal_label_symmetry():
    base=yaml.safe_load(Path('configs/base.yaml').read_text(encoding='utf-8'))
    design=yaml.safe_load(Path('configs/proposed_mechanism_identification.yaml').read_text(encoding='utf-8'))
    for seed in design['seeds']:
        models=[matched_model({**base,'seed':seed},design,o,v) for o in ('equal','unequal') for v in ('high_at_node2','high_at_node3')]
        for m in models:
            np.testing.assert_array_equal(m.beta[:,2],m.beta[:,3])
            assert not m.entry[2] and not m.entry[3]
            assert m.x0[2]==m.x0[3]==0
            assert np.count_nonzero(m.beta)==8
            assert m.q.sum()==9
            np.testing.assert_allclose(m.beta.sum(),models[0].beta.sum(),atol=1e-15)
        np.testing.assert_array_equal(models[0].beta,models[1].beta)
        np.testing.assert_array_equal(models[2].beta,models[3].beta)
        np.testing.assert_allclose(models[2].beta.sum(axis=1)[[2,3]],[.24,.08])
        permutation=[0,1,3,2,4,5]
        u=list(initial_controls(models[0],6,'Uniform'))
        u[1][:,2]*=.7;u[2][:,3]*=.8
        first=simulate(models[0],*u,10,12)
        second=simulate(models[1],*[x[:,permutation] for x in u],10,12)
        np.testing.assert_allclose(first['J_D'],second['J_D'],atol=1e-12)
        np.testing.assert_allclose(first['states'][:,permutation],second['states'],atol=1e-12)
