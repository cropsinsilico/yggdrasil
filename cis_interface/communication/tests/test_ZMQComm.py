from cis_interface.communication.tests import test_CommBase as parent


class TestZMQComm(parent.TestCommBase):
    r"""Test for ZMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestZMQComm, self).__init__(*args, **kwargs)
        self.comm = 'ZMQComm'
        self.attr_list += ['context', 'socket', 'socket_type_name',
                           'socket_type']

    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm, self).send_inst_kwargs
        out['protocol'] = 'inproc'
        return out


class TestZMQCommTCP(TestZMQComm):
    r"""Test for ZMQComm communication class with TCP socket."""

    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm, self).send_inst_kwargs
        out['protocol'] = 'tcp'
        return out
