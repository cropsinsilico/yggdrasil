import os
import unittest
from yggdrasil import backwards, units
from yggdrasil.tests import assert_equal
from yggdrasil.communication import AsciiTableComm
from yggdrasil.communication.tests import test_AsciiFileComm as parent
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    data2dtype)


def test_AsciiTableComm_nofmt():
    r"""Test read of asciitable without format."""
    test_file = os.path.join(os.getcwd(), 'temp_file.txt')
    rows = [('one', 1, 1.0), ('two', 2, 2.0), ('three', 3, 3.0)]
    lines = [backwards.format_bytes('%5s\t%d\t%f\n', r) for r in rows]
    contents = backwards.as_bytes(''.join(lines))
    with open(test_file, 'wb') as fd:
        fd.write(contents)
    inst = AsciiTableComm.AsciiTableComm('test', test_file, direction='recv')
    inst.open()
    for ans in rows:
        flag, x = inst.recv_dict()
        assert(flag)
        irow = [e for e in ans]
        irow[0] = backwards.as_bytes(irow[0])
        idict = {'f%d' % i: irow[i] for i in range(len(irow))}
        # irow = tuple(irow)
        assert_equal(x, idict)
    flag, x = inst.recv()
    assert(not flag)
    inst.close()
    os.remove(test_file)


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""

    comm = 'AsciiTableComm'
    
    @unittest.skipIf(True, 'Table comm')
    def test_send_recv_comment(self):
        r"""Disabled: Test send/recv with commented message."""
        pass  # pragma: no cover

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        if not self.instance.is_eof(obj):
            field_units = self.testing_options.get('field_units', None)
            if field_units:
                if isinstance(obj, dict):
                    return {k: units.add_units(v, u, dtype=data2dtype(v))
                            for (k, v), u in zip(obj.items(), field_units)}
                elif isinstance(obj, (list, tuple)):
                    return [units.add_units(x, u, dtype=data2dtype(x))
                            for x, u in zip(obj, field_units)]
        return obj

    
class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    testing_option_kws = {'array_columns': True}
