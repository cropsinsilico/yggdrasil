import os
import signal
import nose.tools as nt
from threading import Timer
from cis_interface import PsiRun


# TODO: Test Ctrl-C interruption


class TestDriver(object):
    r"""Test runner for basic Driver class.

    Attributes:
        driver (str): The driver class.
        args (object): Driver arguments.
        namespace (str): PSI namespace to run drivers in.
        attr_list (list): List of attributes that should be checked for after
            initialization.

    """

    def __init__(self):
        self.driver = 'Driver'
        self.args = None
        self.namespace = 'TESTING'
        self.attr_list = ['name', 'sleeptime', 'longsleep', 'yml', 'namespace',
                          'rank', 'workingDir']
        self.inst_kwargs = {}

    def setup(self):
        r"""Create a driver instance and start the driver."""
        os.environ['PSI_DEBUG'] = 'DEBUG'
        os.environ['RMQ_DEBUG'] = 'DEBUG'
        # os.environ['PSI_DEBUG'] = 'INFO'
        os.environ['PSI_NAMESPACE'] = self.namespace
        PsiRun.setup_psi_logging(self.__module__)
        PsiRun.setup_rmq_logging()
        self._instance = self.create_instance()
        self.instance.start()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        if hasattr(self, '_instance'):
            self.remove_instance(self._instance)
            delattr(self, '_instance')

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
        inst = PsiRun.create_driver(self.driver, self.name, self.args,
                                    namespace=self.namespace,
                                    workingDir=self.workingDir,
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

    def test_attributes(self):
        r"""Assert that the driver has all of the required attributes."""
        for a in self.attr_list:
            if not hasattr(self.instance, a):  # pragma: debug
                raise AttributeError("Driver does not have attribute %s" % a)

    def test_init_del(self):
        r"""Test driver creation and deletion."""
        pass  # calls creation/destruction

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

    # This only works for some drivers
    # def test_wait(self):
    #     r"""Test mechanism to wait on driver to finish."""
    #     t = Timer(1, self.instance.stop)
    #     self.instance.wait()
    #     assert(not self.instance.isAlive())
