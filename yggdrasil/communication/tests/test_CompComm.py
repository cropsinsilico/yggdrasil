import uuid
import copy
from yggdrasil import units
from yggdrasil.communication.tests import test_CommBase as parent


class TestCompComm(parent.TestCommBase):
    r"""Tests for CompComm communication class."""

    comm = 'CompComm'
    attr_list = (copy.deepcopy(parent.TestCommBase.attr_list)
                 + ['comm_list'])

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return set([self.comm] + [None])

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        if not self.instance.is_eof(obj):
            field_units = self.testing_options.get('field_units', None)
            if field_units:
                if isinstance(obj, dict):
                    return {k: units.add_units(v, u) for (k, v), u
                            in zip(obj.items(), field_units)}
                elif isinstance(obj, (list, tuple)):
                    return [units.add_units(x, u) for x, u
                            in zip(obj, field_units)]
        return obj
    
    def test_error_name(self):
        r"""Test error on missing address."""
        self.assert_raises(RuntimeError, self.import_cls, 'test%s' % uuid.uuid4())

    def test_error_send(self):
        r"""Disabled: Test error on send."""
        pass

    def test_error_recv(self):
        r"""Disabled: Test error on recv."""
        pass

    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass


class TestCompCommList(TestCompComm):
    r"""Tests for CompComm communication class with construction from address."""
    @property
    def inst_kwargs(self):
        r"""list: Keyword arguments for tested class."""
        out = super(TestCompComm, self).inst_kwargs
        out['comm'] = 'CompComm'  # To force test of construction from addresses
        return out
