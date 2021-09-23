import numpy as np
import pandas
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
        arr1 = np.zeros((nele, ), dtype)
        arr2 = np.ones((nele, ), dtype)
        pd1 = pandas.DataFrame(arr1)
        pd2 = pandas.DataFrame(arr2)
        pdcat = pandas.DataFrame(np.hstack([arr1, arr2]))
        out = {'kwargs': {},
               'contents': (b'f0\n' + nele * b'0.0\n' + nele * b'1.0\n'),
               'send': [pd1, pd2],
               'recv': [pdcat],
               'recv_partial': [[pd1], [pdcat]],
               'dict': {'f0': arr1['f0']},
               'objects': [pd1, pd2]}
        out['msg'] = out['send'][0]
        out['msg_array'] = arr1
        return out

    def test_send_dict_default(self):
        r"""Test automated conversion of dictionary to pandas data frame."""
        self.do_send_recv(msg_send=self.testing_options['dict'],
                          msg_recv=self.testing_options['msg'])
