import numpy as np
from yggdrasil.communication.tests import test_AsciiTableComm as parent


class TestPandasFileComm(parent.TestAsciiTableComm):
    r"""Test for PandasFileComm communication class."""

    comm = 'PandasFileComm'


class TestPandasFileComm_nonames(TestPandasFileComm):
    r"""Test for PandasFileComm communication class without field names sent."""

    testing_option_kws = {'no_names': True}


class TestPandasFileComm_single(TestPandasFileComm):
    r"""Test for PandasFileComm communication class with field names sent."""

    def get_options(self):
        r"""Get testing options."""
        nele = 5
        dtype = np.dtype(dict(formats=['float'], names=['f0']))
        arr = np.zeros((nele, ), dtype)
        out = {'kwargs': {},
               'contents': (b'f0\n' + 2 * nele * b'0.0\n'),
               'send': [[arr['f0']], [arr['f0']]],
               'recv': [[np.hstack([arr, arr])['f0']]],
               'dict': {'f0': arr['f0']}}
        out['msg'] = out['send'][0]
        out['msg_array'] = arr
        return out

    def test_send_dict_default(self):
        r"""Test automated conversion of dictionary to pandas data frame."""
        self.do_send_recv(msg_send=self.testing_options['dict'],
                          msg_recv=self.testing_options['msg'])
