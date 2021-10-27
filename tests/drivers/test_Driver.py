import pytest
import copy
from tests import TestComponentBase as base_class
import os


class TestDriver(base_class):
    r"""Test parameters for basic Driver test class."""

    @pytest.fixture(scope="class")
    def working_dir(self):
        r"""Working director."""
        return os.path.dirname(__file__)

    @pytest.fixture
    def namespace(self, uuid):
        r"""Unique name for the test communicators."""
        return f"TESTING_{uuid}"

    @pytest.fixture
    def name(self, class_name, uuid):
        r"""str: Name of the test driver."""
        return f'Test{class_name}_{uuid}'

    @pytest.fixture
    def instance_args(self, name):
        r"""Arguments for a new instance of the tested class."""
        return tuple([name])

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace):
        r"""Keyword arguments for a new instance of the tested class."""
        yml = {}
        if working_dir:
            yml['working_dir'] = working_dir
        return dict(copy.deepcopy(testing_options.get('kwargs', {})), yml=yml,
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace)

    @pytest.fixture
    def instance(self, python_class, instance_args, instance_kwargs,
                 verify_count_threads, verify_count_comms, verify_count_fds,
                 working_dir, is_installed):
        r"""New instance of the python class for testing."""
        curpath = os.getcwd()
        if working_dir:
            os.chdir(working_dir)
        out = python_class(*instance_args, **instance_kwargs)
        try:
            yield out
        finally:
            if not out.was_started:
                out.cleanup()
            out.disconnect()
            del out
            os.chdir(curpath)

    @pytest.fixture(scope="class")
    def before_instance_started(self):
        r"""Actions performed after teh instance is created, but before it
        is started."""
        def before_instance_started_w(x):
            pass
        return before_instance_started_w

    @pytest.fixture(scope="class")
    def after_instance_started(self):
        r"""Action taken after the instance is started, but before tests
        begin."""
        def after_instance_started_w(x):
            pass
        return after_instance_started_w
        
    @pytest.fixture
    def started_instance(self, instance, before_instance_started,
                         after_instance_started):
        r"""Started version of the instance."""
        before_instance_started(instance)
        instance.start()
        try:
            after_instance_started(instance)
            yield instance
        finally:
            if not instance.was_terminated:
                instance.terminate()
            if instance.is_alive():
                instance.join()
            instance.cleanup()
            assert(not instance.is_alive())

    @pytest.fixture(scope="class")
    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        def assert_before_stop_w():
            pass
        return assert_before_stop_w

    @pytest.fixture(scope="class")
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        def run_before_terminate_w():
            pass
        return run_before_terminate_w

    @pytest.fixture(scope="class")
    def run_before_stop(self):
        r"""Commands to run while the instance is running."""
        def run_before_stop_w():
            pass
        return run_before_stop_w

    @pytest.fixture
    def assert_after_terminate(self, started_instance):
        r"""Assertions to make after terminating the driver instance."""
        def assert_after_terminate_w():
            assert(not started_instance.is_alive())
        return assert_after_terminate_w

    @pytest.fixture
    def assert_after_stop(self, assert_after_terminate):
        r"""Assertions to make after stopping the driver instance."""
        def assert_after_stop_w():
            assert_after_terminate()
        return assert_after_stop_w

    def test_init_del(self, started_instance):
        r"""Test driver creation and deletion."""
        started_instance.printStatus()
        started_instance.printStatus(return_str=True)

    def test_run_stop(self, started_instance, assert_before_stop,
                      run_before_stop, assert_after_stop, polling_interval):
        r"""Start the thread, then stop it."""
        assert_before_stop()
        run_before_stop()
        started_instance.wait(polling_interval)
        started_instance.stop()
        started_instance.stop()
        assert_after_stop()

    def test_run_terminate(self, started_instance, assert_before_stop,
                           run_before_terminate, assert_after_terminate):
        r"""Start the thread, then terminate it."""
        assert_before_stop()
        run_before_terminate()
        started_instance.terminate()
        # Second time to ensure it is escaped
        started_instance.terminate()
        if started_instance.is_alive():  # pragma: debug
            started_instance.join()
        assert_after_terminate()
