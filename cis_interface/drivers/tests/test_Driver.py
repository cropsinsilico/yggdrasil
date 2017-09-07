import os
import nose.tools as nt
import unittest
from cis_interface import runner
from cis_interface.tools import ipc_queues
from cis_interface.config import cis_cfg

# TODO: Test Ctrl-C interruption


class TestParam(unittest.TestCase):
    r"""Test parameters for basic Driver test class.

    Attributes:
        driver (str): The driver class.
        args (object): Driver arguments.
        namespace (str): PSI namespace to run drivers in.
        attr_list (list): List of attributes that should be checked for after
            initialization.
        inst_kwargs (dict): Keyword arguments for the driver.
        nprev_queues (int): The number of IPC queues that exist before the
            driver instance is created.

    """

    def __init__(self, *args, **kwargs):
        self.driver = 'Driver'
        self.args = None
        self.namespace = 'TESTING'
        self.attr_list = ['name', 'sleeptime', 'longsleep', 'yml', 'namespace',
                          'rank', 'workingDir']
        self.inst_kwargs = {'yml': {'workingDir': self.workingDir}}
        self.nprev_queues = 0
        super(TestParam, self).__init__(*args, **kwargs)

    def shortDescription(self):
        r"""Prefix first line of doc string with driver."""
        out = super(TestParam, self).shortDescription()
        return '%s: %s' % (self.driver, out)

    def setUp(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def tearDown(self, *args, **kwargs):
        self.teardown(*args, **kwargs)

    # def set_param_attr(self, param_class):
    #     r"""Copy all attributes from param_class."""
    #     for k, v in param_class.__dict__.items():
    #         setattr(self, k, v)
            
    def setup(self, skip_start=False):
        r"""Create a driver instance and start the driver."""
        # cis_cfg.set('debug', 'psi', 'INFO')
        cis_cfg.set('debug', 'psi', 'DEBUG')
        cis_cfg.set('debug', 'rmq', 'INFO')
        cis_cfg.set('debug', 'client', 'INFO')
        cis_cfg.set('rmq', 'namespace', self.namespace)
        runner.setup_cis_logging(self.__module__)
        runner.setup_rmq_logging()
        self.nprev_queues = len(ipc_queues())
        self._instance = self.create_instance()
        if not skip_start:
            self.instance.start()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        if hasattr(self, '_instance'):
            self.remove_instance(self._instance)
            delattr(self, '_instance')
        nt.assert_equal(len(ipc_queues()), self.nprev_queues)

    @property
    def name(self):
        r"""str: Name of the test driver."""
        return 'Test' + self.driver

    @property
    def instance(self):
        r"""object: Instance of the test driver."""
        if not hasattr(self, '_instance'):
            self._instance = self.create_instance()
        return self._instance

    @property
    def workingDir(self):
        r"""str: Working directory."""
        return os.path.dirname(__file__)

    def create_instance(self):
        r"""Create a new instance object."""
        curpath = os.getcwd()
        os.chdir(self.workingDir)
        inst = runner.create_driver(self.driver, self.name, self.args,
                                    namespace=self.namespace,
                                    # workingDir=self.workingDir,
                                    **self.inst_kwargs)
        os.chdir(curpath)
        # print("created instance")
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.terminate()
        if inst.is_alive():
            inst.join()  # pragma: debug
        del inst
        # print("removed instance")


class TestDriver(TestParam):
    r"""Test runner for basic Driver class.

    Attributes (in addition to parameter class):
        -

    """

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        pass

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        pass

    def run_before_stop(self):
        r"""Commands to run while the instance is running."""
        pass

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        assert(not self.instance.is_alive())

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        self.assert_after_terminate()

    def test_init_del(self):
        r"""Test driver creation and deletion."""
        self.instance.printStatus()

    def test_run_stop(self):
        r"""Start the thread, then stop it."""
        self.assert_before_stop()
        self.run_before_stop()
        self.instance.stop()
        if self.instance.is_alive():
            self.instance.join()
        self.assert_after_stop()

    def test_run_terminate(self):
        r"""Start the thread, then terminate it."""
        self.assert_before_stop()
        self.run_before_terminate()
        self.instance.terminate()
        if self.instance.is_alive():
            self.instance.join()
        self.assert_after_terminate()

        
class TestDriverNoStart(TestParam):
    r"""Test runner for basic Driver class without starting driver.

    Attributes (in addition to parent class):
        -

    """

    def setup(self):
        r"""Create a driver instance without starting the driver."""
        super(TestDriverNoStart, self).setup(skip_start=True)
        assert(not self.instance.is_alive())

    def test_attributes(self):
        r"""Assert that the driver has all of the required attributes."""
        for a in self.attr_list:
            if not hasattr(self.instance, a):  # pragma: debug
                raise AttributeError("Driver does not have attribute %s" % a)

    def test_info(self):
        r"""Test print of info statement."""
        self.instance.info(1)

    def test_debug(self):
        r"""Test print of debug statement."""
        self.instance.debug(1)

    def test_critical(self):
        r"""Test print of critical statement."""
        self.instance.critical(1)

    def test_warn(self):
        r"""Test print of warning statement."""
        self.instance.warn(1)
        
    def test_error(self):
        r"""Test print of error statement."""
        self.instance.error(1)

    def test_exception(self):
        r"""Test print of exception."""
        self.instance.exception(1)
        
    def test_printStatus(self):
        r"""Test mechanism to print the status of the driver."""
        self.instance.printStatus()
