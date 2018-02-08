import os
import threading
# import psutil
import nose.tools as nt
from cis_interface.tools import CisClass
from cis_interface.tests import CisTest
from cis_interface.communication import get_comm_class


class TestParam(CisTest):
    r"""Test parameters for basic Driver test class.

    Attributes:
        driver (str): Name of driver class.
        args (object): Driver arguments.
        namespace (str): PSI namespace to run drivers in.
        nprev_comm (int): The number of communication queues, sockets, and
            channel that exist when the driver instance is created.

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
        self.nprev_comm = 0
        self.debug_flag = False

    @property
    def skip_start(self):
        r"""bool: True if driver shouldn't be started. False otherwise."""
        return ('NoStart' in str(self.__class__))

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

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestParam, self).inst_kwargs
        out['timeout'] = self.timeout
        out['sleeptime'] = self.sleeptime
        return out

    @property
    def comm_count(self):
        r"""int: Return the number of comms."""
        return get_comm_class().comm_count()

    @property
    def thread_count(self):
        r"""int: Return the number of active threads."""
        return threading.active_count()

    def setup(self, nprev_comm=None, nprev_thread=None):
        r"""Create a driver instance and start the driver.

        Args:
            nprev_comm (int, optional): Number of previous comm channels.
                If not provided, it is determined to be the present number of
                default comms.
            nprev_thread (int, optional): Number of previous threads.
                If not provided, it is determined to be the present number of
                threads.

        """
        if nprev_comm is None:
            nprev_comm = self.comm_count
        if nprev_thread is None:
            nprev_thread = self.thread_count
        self.nprev_comm = nprev_comm
        self.nprev_thread = self.thread_count
        super(TestParam, self).setup()
        if not self.skip_start:
            self.instance.start()

    def teardown(self, ncurr_comm=None, ncurr_thread=None):
        r"""Remove the instance, stoppping it.

        Args:
            ncurr_comm (int, optional): Number of current comms. If not
                provided, it is determined to be the present number of comms.
            ncurr_thread (int, optional): Number of current threads. If not
                provided, it is determined to be the present number of threads.

        """
        super(TestParam, self).teardown()
        # Give comms time to close
        if ncurr_comm is None:
            x = CisClass(self.name, timeout=self.timeout,
                         sleeptime=self.sleeptime)
            Tout = x.start_timeout()
            while ((not Tout.is_out) and
                   (self.comm_count > self.nprev_comm)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_comm = self.comm_count
        # Give threads time to close
        if ncurr_thread is None:
            x = CisClass(self.name, timeout=self.timeout,
                         sleeptime=self.sleeptime)
            Tout = x.start_timeout()
            while ((not Tout.is_out) and
                   (self.thread_count > self.nprev_thread)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_thread = self.thread_count
        # Check counts
        nt.assert_less_equal(ncurr_comm, self.nprev_comm)
        nt.assert_less_equal(ncurr_thread, self.nprev_thread)
        # nt.assert_equal(len(psutil.Process().children(recursive=True)), 0)

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
        if not inst.was_terminated:
            inst.terminate()
        if inst.is_alive():  # pragma: debug
            inst.join()
        inst.cleanup()
        assert(not inst.is_alive())
        super(TestParam, self).remove_instance(inst)


class TestDriver(TestParam):
    r"""Test runner for basic Driver class."""

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
        self.instance.wait(self.sleeptime)
        self.instance.stop()
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
    r"""Test runner for basic Driver class without starting driver."""

    def setup(self, *args, **kwargs):
        r"""Create a driver instance without starting the driver."""
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
        self.instance.verbose_debug(1)
        self.instance.critical(1)
        self.instance.warn(1)
        self.instance.error(1)
        self.instance.exception(1)
        try:
            raise Exception("Test exception")
        except Exception:
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
