import pandas as pd
import numpy as np
from cis_interface import serialize, backwards
from cis_interface.communication.tests import test_AsciiTableComm as parent


class TestPandasFileComm(parent.TestAsciiTableComm):
    r"""Test for PandasFileComm communication class."""

    comm = 'PandasFileComm'


class TestPandasFileComm_nonames(TestPandasFileComm):
    r"""Test for PandasFileComm communication class without field names sent."""

    def get_testing_options(self):
        r"""Get testing options."""
        out = super(TestPandasFileComm_nonames, self).get_testing_options()
        for i, k in enumerate(out['kwargs']['field_names']):
            out['contents'] = out['contents'].replace(
                k, backwards.unicode2bytes('f%d' % i))
        del out['kwargs']['field_names']
        return out


class TestPandasFileComm_single(TestPandasFileComm):
    r"""Test for PandasFileComm communication class with field names sent."""

    def get_testing_options(self):
        r"""Get testing options."""
        nele = 5
        out = {'kwargs': {},
               'contents': (b'f0\n' + 2 * nele * b'0.0\n'),
               'send': [[np.zeros((nele, ))], [np.zeros((nele, ))]],
               'recv': [[np.zeros((2 * nele, ))]],
               'dict': {'f0': np.zeros((nele, ))}}
        out['msg'] = out['send'][0]
        return out
