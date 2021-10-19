import pytest
import numpy as np
import pandas
from tests.communication.test_AsciiTableComm import (
    TestAsciiTableComm as base_class)


@pytest.mark.usefixtures("pandas_equality_patch")
class TestPandasFileComm(base_class):
    r"""Test for PandasFileComm communication class."""

    @pytest.fixture(scope="class", autouse=True)
    def filetype(self):
        r"""Communicator type being tested."""
        return "pandas"

    @pytest.fixture(scope="class", autouse=True,
                    params=[{}, {'no_names': True}])
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    @pytest.fixture(scope="class")
    def map_sent2recv(self, testing_options):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            return obj
        return wrapped_map_sent2recv


class TestPandasFileComm_single(TestPandasFileComm):
    r"""Test for PandasFileComm communication class with field names sent."""

    @pytest.fixture(scope="class", autouse=True)
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {}
    
    @pytest.fixture(scope="class")
    def testing_options(self):
        r"""Testing options."""
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

    def test_send_dict_default(self, send_comm, recv_comm, testing_options,
                               do_send_recv):
        r"""Test automated conversion of dictionary to pandas data frame."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'message': testing_options['dict']},
                     recv_params={'message': testing_options['msg']})
