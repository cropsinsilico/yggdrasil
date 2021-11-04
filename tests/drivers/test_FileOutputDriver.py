import pytest
import os
from yggdrasil import constants
from tests.drivers.test_ConnectionDriver import (
    TestOutputDriver as base_class)


_filetypes = sorted(constants.COMPONENT_REGISTRY['file']['subtypes'].keys())


class TestFileOutputDriver(base_class):
    r"""Test class for FileOutputDriver."""

    parametrize_filetype = _filetypes
    
    test_send_recv = None
    test_send_recv_nolimit = None
    test_send_recv_closed = None
    
    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'file_output'

    @pytest.fixture(scope="class")
    def filetype(self, request):
        r"""str: Name of the file type being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def commtype(self, filetype):
        r"""str: Name of the communicator being tested."""
        return filetype

    @pytest.fixture
    def instance_args(self, name, filepath):
        r"""Arguments for a new instance of the tested class."""
        return (name, filepath)

    @pytest.fixture(autouse=True)
    def filepath(self, name, ocomm_python_class):
        r"""str: Path to the test file."""
        out = os.path.abspath(
            f'{name}_input{ocomm_python_class._default_extension}')
        try:
            yield out
        finally:
            if os.path.isfile(out):
                os.remove(out)

    @pytest.fixture
    def recv_comm(self):
        r"""CommBase: communicator for receiving messages from the driver."""
        pytest.skip("recv_comm disabled for output files")

    @pytest.fixture
    def before_instance_started(self, send_comm):
        r"""Actions performed after teh instance is created, but before it
        is started."""
        def before_instance_started_w(x):
            pass
        return before_instance_started_w
    
    @pytest.fixture
    def after_instance_started(self, send_comm, testing_options):
        r"""Action taken after the instance is started, but before tests
        begin."""
        def after_instance_started_w(x):
            for x in testing_options['send']:
                flag = send_comm.send(x)
                assert(flag)
            flag = send_comm.send_eof()
            assert(flag)
        return after_instance_started_w

    @pytest.fixture
    def run_before_stop(self, instance):
        r"""Commands to run while the instance is running."""
        def run_before_stop_w():
            instance.wait(1.0)
        return run_before_stop_w
    
    @pytest.fixture
    def contents_to_read(self, testing_options):
        r"""str: Contents that should be read to the file."""
        return testing_options['contents']

    @pytest.fixture
    def assert_after_stop(self, assert_after_terminate, filepath,
                          testing_options, contents_to_read):
        r"""Assertions to make after stopping the driver instance."""
        def assert_after_stop_w():
            assert_after_terminate()
            assert(os.path.isfile(filepath))
            if testing_options.get('exact_contents', True):
                with open(filepath, 'rb') as fd:
                    data = fd.read()
                assert(data == contents_to_read)
        return assert_after_stop_w
    
    # These are disabled to prevent writting extraneous data
    @pytest.fixture(scope="class")
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        def run_before_terminate_w():
            pass
        return run_before_terminate_w


class TestAsciiTableArrayOutputDriver(TestFileOutputDriver):
    r"""Test class for FileOutputDriver reading to a table as an array."""

    @pytest.fixture(scope="class")
    def filetype(self):
        r"""str: Name of the file type being tested."""
        return 'table'

    @pytest.fixture(scope="class")
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {'array_columns': True}
