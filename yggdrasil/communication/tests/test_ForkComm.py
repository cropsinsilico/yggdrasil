import uuid
import copy
from yggdrasil.communication.tests import test_CommBase as parent


class TestForkComm(parent.TestCommBase):
    r"""Tests for ForkComm communication class."""

    comm = 'ForkComm'
    attr_list = (copy.deepcopy(parent.TestCommBase.attr_list)
                 + ['comm_list', 'curr_comm_index'])
    ncomm = 2

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return set([self.comm] + [None])

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestForkComm, self).send_inst_kwargs
        out['ncomm'] = self.ncomm
        return out

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

    def do_send_recv(self, *args, **kwargs):
        r"""Generic send/recv of a message."""
        if ((('eof' not in kwargs.get('send_meth', 'None'))
             and (not kwargs.get('no_recv', False)))):
            kwargs.setdefault('n_recv', self.ncomm)
        super(TestForkComm, self).do_send_recv(*args, **kwargs)

    def add_filter(self, comm, filter=None):
        r"""Add a filter to a comm.

        Args:
            comm (CommBase): Communication instance to add a filter to.
            filter (FilterBase, optional): Filter class. Defaults to None and is ignored.

        """
        for x in comm.comm_list:
            super(TestForkComm, self).add_filter(x, filter=filter)
            
    def test_send_recv_filter_recv_filter(self, **kwargs):
        r"""Test send/recv with filter that blocks recv."""
        kwargs.setdefault('n_recv', 1)
        super(TestForkComm, self).test_send_recv_filter_recv_filter(**kwargs)
        
    def test_purge(self, **kwargs):
        r"""Test purging messages from the comm."""
        kwargs['nrecv'] = self.ncomm
        super(TestForkComm, self).test_purge(**kwargs)


class TestForkCommList(TestForkComm):
    r"""Tests for ForkComm communication class with construction from address."""
    @property
    def inst_kwargs(self):
        r"""list: Keyword arguments for tested class."""
        out = super(TestForkComm, self).inst_kwargs
        out['comm'] = 'ForkComm'  # To force test of construction from addresses
        return out
