import os
import numpy as np
import nose.tools as nt
from cis_interface import backwards, serialize
from cis_interface.communication import AsciiTableComm
from cis_interface.communication.tests import test_AsciiFileComm as parent


def test_AsciiTableComm_nofmt():
    r"""Test read of asciitable without format."""
    test_file = os.path.join(os.getcwd(), 'temp_file.txt')
    rows = [('one', 1, 1.0), ('two', 2, 2.0), ('three', 3, 3.0)]
    lines = [backwards.format_bytes('%5s\t%d\t%f\n', r) for r in rows]
    contents = backwards.unicode2bytes(''.join(lines))
    with open(test_file, 'wb') as fd:
        fd.write(contents)
    inst = AsciiTableComm.AsciiTableComm('test', test_file, direction='recv')
    inst.open()
    for ans in rows:
        flag, x = inst.recv_dict()
        assert(flag)
        irow = [e for e in ans]
        irow[0] = backwards.unicode2bytes(irow[0])
        idict = {'f%d' % i: irow[i] for i in range(len(irow))}
        # irow = tuple(irow)
        nt.assert_equal(x, idict)
    flag, x = inst.recv()
    assert(not flag)
    inst.close()
    os.remove(test_file)


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiTableComm'
        self.field_names = [backwards.bytes2unicode(x) for
                            x in self.send_inst_kwargs.get('field_names', [])]

    def test_send_recv_comment(self):
        r"""Disabled: Test send/recv with commented message."""
        pass


class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    @property
    def testing_options(self):
        r"""dict: Testing options."""
        out = self.import_cls.get_testing_options(as_array=True)
        return out
