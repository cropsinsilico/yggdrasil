import os
import nose.tools as nt
from cis_interface.tests import CisTestClassInfo
from cis_interface import drivers


def test_import_driver():
    r"""Test creation of default driver."""
    drivers.import_driver()


class TestParam(CisTestClassInfo):
    r"""Test parameters for basic Driver test class.

    Attributes:
        driver (str): Name of driver class.
        args (object): Driver arguments.
        namespace (str): PSI namespace to run drivers in.

    """

    def __init__(self, *args, **kwargs):
        super(TestParam, self).__init__(*args, **kwargs)
        self.driver = 'Driver'
        self.args = None
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list += ['name', 'sleeptime', 'longsleep', 'timeout',
                           'yml', 'env', 'namespace', 'rank', 'working_dir',
                           'lock']
        self._inst_kwargs = {'yml': {'working_dir': self.working_dir},
                             'timeout': self.timeout,
                             'sleeptime': self.sleeptime,
                             # 'working_dir': self.working_dir,
                             'namespace': self.namespace}
        self.debug_flag = False

    @property
    def working_dir(self):
        r"""str: Working directory."""
        return os.path.dirname(__file__)

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

    def setup(self, *args, **kwargs):
        r"""Create a driver instance and start the driver."""
        super(TestParam, self).setup(*args, **kwargs)
        if not self.skip_start:
            self.instance.start()

    @property
    def name(self):
        r"""str: Name of the test driver."""
        return 'Test%s_%s' % (self.cls, self.uuid)

    def create_instance(self):
        r"""Create a new instance object."""
        curpath = os.getcwd()
        os.chdir(self.working_dir)
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
        self.instance.warning(1)
        self.instance.error(1)
        self.instance.exception(1)
        try:
            raise Exception("Test exception")
        except Exception:
            self.instance.exception(1)
        self.instance.printStatus()
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = True
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = False

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
        self.instance.stop_timeout(quiet=True)
