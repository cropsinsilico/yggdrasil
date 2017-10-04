import os
import nose.tools as nt
from cis_interface import runner, tools
from cis_interface.config import cis_cfg
from cis_interface.tests import CisTest

# TODO: Test Ctrl-C interruption


class TestParam(CisTest):
    r"""Test parameters for basic Driver test class.

    Attributes:
        driver (str): Name of driver class.
        args (object): Driver arguments.
        namespace (str): PSI namespace to run drivers in.
        nprev_queues (int): The number of IPC queues that exist before the
            driver instance is created.

    """

    def __init__(self, *args, **kwargs):
        super(TestParam, self).__init__(*args, **kwargs)
        self.driver = 'Driver'
        self.args = None
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list += ['name', 'sleeptime', 'longsleep', 'timeout',
                           'yml', 'env', 'namespace', 'rank', 'workingDir',
                           'lock']
        self._inst_kwargs = {'yml': {'workingDir': self.workingDir},
                             'timeout': self.timeout,
                             'sleeptime': self.sleeptime,
                             # 'workingDir': self.workingDir,
                             'namespace': self.namespace}
        self.nprev_queues = 0

    @property
    def cls(self):
        r"""str: Driver class."""
        return self.driver

    @property
    def mod(self):
        r"""str: Absolute path to module containing driver."""
        return 'cis_interface.drivers.%s' % self.cls

    @property
    def inst_args(self):
        r"""tuple: Driver arguments."""
        out = [self.name]
        if self.args is not None:
            out.append(self.args)
        return out

    def setup(self, skip_start=False, nprev_queues=None):
        r"""Create a driver instance and start the driver.

        Args:
            skip_start (bool, optional): If True, the driver will not be
                started. Defaults to False.
            nprev_queues (int, optional): Number of previous IPC queues.
                If not provided, it is determined to be the present number of
                queues.

        """
        cis_cfg.set('debug', 'psi', 'INFO')
        cis_cfg.set('debug', 'rmq', 'INFO')
        cis_cfg.set('debug', 'client', 'INFO')
        cis_cfg.set('rmq', 'namespace', self.namespace)
        runner.setup_cis_logging(self.__module__)
        runner.setup_rmq_logging()
        if nprev_queues is None:
            nprev_queues = len(tools._registered_queues.keys())
        self.nprev_queues = nprev_queues
        super(TestParam, self).setup()
        if not skip_start:
            self.instance.start()

    def teardown(self, ncurr_queues=None):
        r"""Remove the instance, stoppping it.

        Args:
            ncurr_queues (int, optional): Number of current queues. If not
                provided, it is determined to be the present number of queues.

        """
        super(TestParam, self).teardown()
        if ncurr_queues is None:
            ncurr_queues = len(tools._registered_queues.keys())
        nt.assert_equal(ncurr_queues, self.nprev_queues)

    @property
    def name(self):
        r"""str: Name of the test driver."""
        return 'Test%s_%s' % (self.cls, self.uuid)

    def create_instance(self):
        r"""Create a new instance object."""
        curpath = os.getcwd()
        os.chdir(self.workingDir)
        inst = super(TestParam, self).create_instance()
        os.chdir(curpath)
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance."""
        if not inst._terminated:
            inst.terminate()
        if inst.is_alive():  # pragma: debug
            inst.join()
        inst.cleanup()
        assert(not inst.is_alive())
        super(TestParam, self).remove_instance(inst)


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

    def setup(self, *args, **kwargs):
        r"""Create a driver instance without starting the driver."""
        kwargs['skip_start'] = True
        super(TestDriverNoStart, self).setup(*args, **kwargs)
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
        try:
            raise Exception("Test exception")
        except:
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
