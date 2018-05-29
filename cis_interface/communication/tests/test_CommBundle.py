from cis_interface.communication.tests.test_CommBase import TestCommBase


class TestCommBundle(TestCommBase):
    r"""Tests for CommBase communication class."""
    def __init__(self, *args, **kwargs):
        super(TestCommBase, self).__init__(*args, **kwargs)
        self.comm = 'CommBundle'
        self.attr_list += ['comm_list', 'curr_comm_index']
        self.comm_list = [None, 'FileComm']
        self.comm_kwargs = [{'comm': x} for x in self.comm_list]

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return set([self.comm, self.send_inst_kwargs['comm']] + self.comm_list)

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestCommBundle, self).send_inst_kwargs
        out['comm_kwargs'] = self.comm_kwargs
        return out

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
        if 'eof' not in kwargs.get('send_meth', 'None'):
            kwargs['n_recv'] = len(self.comm_kwargs)
        super(TestCommBundle, self).do_send_recv(*args, **kwargs)
