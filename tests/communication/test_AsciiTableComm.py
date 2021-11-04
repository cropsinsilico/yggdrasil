import pytest
import os
import numpy as np
from yggdrasil import units, tools
from yggdrasil.communication import AsciiTableComm
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    data2dtype)
from tests.communication.test_FileComm import TestFileComm as base_class


def test_AsciiTableComm_nofmt():
    r"""Test read of asciitable without format."""
    test_file = os.path.join(os.getcwd(), 'temp_file.txt')
    rows = [('one', 1, 1.0), ('two', 2, 2.0), ('three', 3, 3.0)]
    lines = [('%5s\t%d\t%f\n' % r) for r in rows]
    contents = (''.join(lines)).encode("utf-8")
    with open(test_file, 'wb') as fd:
        fd.write(contents)
    inst = AsciiTableComm.AsciiTableComm('test', test_file, direction='recv')
    inst.open()
    for ans in rows:
        flag, x = inst.recv_dict()
        assert(flag)
        irow = [e for e in ans]
        irow[0] = irow[0].encode("utf-8")
        idict = {'f%d' % i: irow[i] for i in range(len(irow))}
        # irow = tuple(irow)
        assert(x == idict)
    flag, x = inst.recv()
    assert(not flag)
    inst.close()
    os.remove(test_file)


class TestAsciiTableComm(base_class):
    r"""Test for AsciiTableComm communication class."""

    test_send_recv_comment = None

    @pytest.fixture(scope="class", autouse=True)
    def filetype(self):
        r"""Communicator type being tested."""
        return "table"

    @pytest.fixture(scope="class")
    def map_sent2recv(self, testing_options):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            if (not isinstance(obj, bytes)) or (obj != tools.YGG_MSG_EOF):
                field_units = testing_options.get('field_units', None)
                if field_units:
                    if isinstance(obj, dict):
                        return {k: units.add_units(v, u, dtype=data2dtype(v))
                                for (k, v), u in zip(obj.items(), field_units)}
                    elif isinstance(obj, (list, tuple)):
                        return [units.add_units(x, u, dtype=data2dtype(x))
                                for x, u in zip(obj, field_units)]
            return obj
        return wrapped_map_sent2recv


@pytest.mark.usefixtures("unyts_equality_patch")
class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    @pytest.fixture(scope="class", autouse=True)
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {'array_columns': True}


class TestAsciiTableComm_single(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class with field names sent."""

    @pytest.fixture(scope="class")
    def testing_options(self):
        r"""Testing options."""
        nele = 5
        dtype = np.dtype(dict(formats=['float'], names=['f0']))
        arr1 = np.zeros((nele, ), dtype)
        arr2 = np.ones((nele, ), dtype)
        out = {'kwargs': {'as_array': True, 'field_names': ['f0']},
               'contents': (
                   b'# f0\n# %g\n'
                   + nele * b'0\n' + nele * b'1\n'),
               'send': [[arr1['f0']], [arr2['f0']]],
               'recv': [[np.hstack([arr1, arr2])['f0']]],
               'recv_partial': [[[arr1['f0']]], [[arr2['f0']]]],
               'dict': {'f0': arr1['f0']},
               'objects': [[arr1['f0']], [arr2['f0']]]}
        out['msg'] = out['send'][0]
        out['msg_array'] = arr1
        return out

    def test_send_dict_default(self, send_comm, recv_comm, do_send_recv,
                               testing_options):
        r"""Test automated conversion of dictionary to pandas data frame."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'message': testing_options['dict']},
                     recv_params={'message': testing_options['msg']})
