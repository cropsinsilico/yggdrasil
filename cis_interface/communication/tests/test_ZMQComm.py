from cis_interface.communication.tests import test_CommBase as parent


class TestZMQComm(parent.TestCommBase):
    r"""Test for ZMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestZMQComm, self).__init__(*args, **kwargs)
        self.comm = 'ZMQComm'
        self.attr_list += ['context', 'socket', 'socket_type_name',
                           'socket_type']
        self.send_inst_kwargs = {'protocol': 'inproc'}
