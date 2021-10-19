import pytest
import shutil
import os
import numpy as np
import yaml as pyyaml
from yggdrasil import serialize
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

    @pytest.fixture(scope="class")
    def read_file(self):
        r"""Read a file."""
        def read_file_w(fname):
            with open(fname, 'rb') as fd:
                return serialize.table_to_array(fd.read(), comment='#')
        return read_file_w
    
    @pytest.fixture(scope="class")
    def check_file_size(self, wait_on_function):
        r"""Check that file is the correct size.

        Args:
            fname (str): Full path to the file that should be checked.
            fsize (int): Size that the file should be in bytes.
            timeout (float, optional): Time that should be waited when checking
                the file size. Defaults to 2.

        """
        def check_file_size_w(fname, fsize, timeout=2):
            pass
        return check_file_size_w

    @pytest.fixture(scope="class")
    def check_file_contents(self, read_file):
        r"""Check that the contents of a file are correct.

        Args:
            fname (str): Full path to the file that should be checked.
            result (str): Contents of the file.

        """
        def check_file_contents_w(fname, result):
            ocont = read_file(fname)
            np.testing.assert_allclose(ocont, result, rtol=1e-5, atol=1e-8)
        return check_file_contents_w
