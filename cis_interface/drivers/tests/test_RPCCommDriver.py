import nose.tools as nt
from cis_interface.tests import MagicTestError
from cis_interface.drivers import import_driver
from cis_interface.drivers.tests import test_CommDriver as parent


class TestRPCCommParam(parent.TestCommParam):
    r"""Test parameters for the RPCCommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestRPCCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RPCCommDriver'
        self.comm_name = 'RPCComm'
    

class TestRPCCommDriverNoStart(TestRPCCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the RPCCommDriver class without start."""
    
    def get_fresh_error_instance(self, comm, error_on_init=False):
        r"""Get CommDriver instance with an ErrorComm parent class."""
        args = [self.get_fresh_name()]
        if self.args is not None:  # pragma: debug
            args.append(self.args)
        # args = self.inst_args
        kwargs = self.inst_kwargs
        kwargs.setdefault('icomm_kwargs', {})
        kwargs.setdefault('ocomm_kwargs', {})
        if 'address' in kwargs:
            del kwargs['address']
        if comm in ['ocomm', 'both']:
            kwargs['ocomm_kwargs'].update(
                base_comm=None, new_comm_class='ErrorComm',
                error_on_init=error_on_init)
        if comm in ['icomm', 'both']:
            kwargs['icomm_kwargs'].update(
                base_comm=None, new_comm_class='ErrorComm',
                error_on_init=error_on_init)
        driver_class = import_driver(self.driver)
        if error_on_init:
            nt.assert_raises(MagicTestError, driver_class, *args, **kwargs)
        else:
            inst = driver_class(*args, **kwargs)
            self._extra_instances.append(inst)
            return inst

    def test_error_init_ocomm(self):
        r"""Test forwarding of error from init of ocomm."""
        self.get_fresh_error_instance('ocomm', error_on_init=True)
    
    def test_error_open_fails(self):
        r"""Test error raised when comm fails to open."""
        inst = self.get_fresh_error_instance('icomm')
        inst.comm.icomm.error_replace('open')
        nt.assert_raises(MagicTestError, inst.open_comm)
        assert(inst.comm.icomm.is_closed)
        inst.comm.icomm.restore_all()

    def test_error_on_graceful_stop(self):
        r"""Test forwarding of error from close of icomm."""
        inst = self.get_fresh_error_instance('icomm')
        inst.open_comm()
        inst.comm.icomm.error_replace('close')
        nt.assert_raises(MagicTestError, inst.close_comm)
        assert(inst.comm.ocomm.is_closed)
        inst.comm.icomm.restore_all()
        inst.comm.icomm.close()
        assert(inst.comm.icomm.is_closed)

    def test_error_close_ocomm(self):
        r"""Test forwarding of error from close of ocomm."""
        inst = self.get_fresh_error_instance('ocomm')
        inst.open_comm()
        inst.comm.ocomm.error_replace('close')
        nt.assert_raises(MagicTestError, inst.close_comm)
        assert(inst.comm.icomm.is_closed)
        inst.comm.ocomm.restore_all()
        inst.comm.ocomm.close()
        assert(inst.comm.ocomm.is_closed)


class TestRPCCommDriver(TestRPCCommParam, parent.TestCommDriver):
    r"""Test class for the RPCCommDriver class."""
    pass
