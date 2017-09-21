import os
import uuid
import nose.tools as nt
import unittest
from cis_interface import runner, tools
from cis_interface.config import cis_cfg

# TODO: Test Ctrl-C interruption


class TestParam(unittest.TestCase):
    r"""Test parameters for basic Driver test class.

    Attributes:
        driver (str): The driver class.
        args (object): Driver arguments.
        uuid (str): Random unique identifier.
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
        self.uuid = str(uuid.uuid4())
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list = ['name', 'sleeptime', 'longsleep', 'timeout',
                          'yml', 'env', 'namespace', 'rank', 'workingDir',
                          'lock']
        self.inst_kwargs = {'yml': {'workingDir': self.workingDir}}
        self.nprev_queues = 0
        self.timeout = 1.0
        self.sleeptime = 0.01
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
        cis_cfg.set('debug', 'psi', 'INFO')
        cis_cfg.set('debug', 'rmq', 'INFO')
        cis_cfg.set('debug', 'client', 'INFO')
        cis_cfg.set('rmq', 'namespace', self.namespace)
        runner.setup_cis_logging(self.__module__)
        runner.setup_rmq_logging()
        self.nprev_queues = len(tools._registered_queues.keys())
        self._instance = self.create_instance()
        if not skip_start:
            self.instance.start()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        if hasattr(self, '_instance'):
            inst = self._instance
            self._instance = None
            self.remove_instance(inst)
            delattr(self, '_instance')
        nt.assert_equal(len(tools._registered_queues.keys()), self.nprev_queues)

    @property
    def name(self):
        r"""str: Name of the test driver."""
        return 'Test%s_%s' % (self.driver, self.uuid)

    @property
    def instance(self):
        r"""object: Instance of the test driver."""
        if not hasattr(self, '_instance'):  # pragma: debug
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
                                    timeout=self.timeout,
                                    sleeptime=self.sleeptime,
                                    **self.inst_kwargs)
        os.chdir(curpath)
        # print("created instance")
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance."""
        if not inst._terminated:
            inst.terminate()
        if inst.is_alive():  # pragma: debug
            inst.join()
        inst.cleanup()
        assert(not inst.is_alive())
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
        self.assert_after_stop()

    def test_run_terminate(self):
        r"""Start the thread, then terminate it."""
        self.assert_before_stop()
        self.run_before_terminate()
        self.instance.terminate()
        # Second time to ensure it is escaped
        self.instance.terminate()
        if self.instance.is_alive():  # pragma: debug
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

    def test_prints(self):
        r"""Test logging at various levels."""
        self.instance.display(1)
        self.instance.info(1)
        self.instance.debug(1)
        self.instance.critical(1)
        self.instance.warn(1)
        self.instance.error(1)
        self.instance.exception(1)
        self.instance.printStatus()

    def test_timeout(self):
        r"""Test functionality of timeout."""
        # Test w/o timeout
        self.instance.start_timeout(10, key='fake_key')
        assert(not self.instance.check_timeout(key='fake_key'))
        # Test errors
        nt.assert_raises(KeyError, self.instance.start_timeout,
                         0.1, key='fake_key')
        self.instance.stop_timeout(key='fake_key')
        nt.assert_raises(KeyError, self.instance.check_timeout)
        nt.assert_raises(KeyError, self.instance.check_timeout, key='fake_key')
        nt.assert_raises(KeyError, self.instance.stop_timeout, key='fake_key')
        # Test w/ timeout
        T = self.instance.start_timeout(0.001)  # self.instance.sleeptime)
        while not T.is_out:
            self.instance.sleep()
        assert(self.instance.check_timeout())
        self.instance.stop_timeout()

    def test_raise_error(self):
        r"""Test error raise with log."""
        nt.assert_raises(KeyError, self.instance.raise_error, KeyError("fake"))
