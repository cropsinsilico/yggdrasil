import pytest
import shutil
import os
import yaml as pyyaml
from tests.examples import TestExample as base_class


class TestODE(base_class):
    r"""Test the ODE symbolic examples using numeric methods."""

    parametrize_example_name = ['ode1', 'ode2', 'ode3', 'ode4']

    @pytest.fixture(scope="class", autouse=True)
    def replace_yaml(self, example_name, yaml):
        r"""Replace the existing yaml with a version that uses numeric methods."""
        oldyaml = '_old'.join(os.path.splitext(yaml))
        shutil.copy2(yaml, oldyaml)
        contents = pyyaml.safe_load(open(yaml, 'r'))
        if example_name == 'ode2':
            contents['model']['odeint_kws'] = {'from_prev': True}
        else:
            contents['model']['use_numeric'] = True
        pyyaml.dump(contents, open(yaml, 'w'))
        yield
        shutil.move(oldyaml, yaml)
