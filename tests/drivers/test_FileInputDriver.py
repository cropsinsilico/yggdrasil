import pytest
import os
import tempfile
from yggdrasil import constants
from tests.drivers.test_ConnectionDriver import TestInputDriver as base_class


_filetypes = sorted(
    [x for x in constants.COMPONENT_REGISTRY['file']['subtypes'].keys()
     if x not in ['pandas']])


class TestFileInputDriver(base_class):
    r"""Test class for FileInputDriver."""

    parametrize_filetype = _filetypes

    test_send_recv = None
    test_send_recv_nolimit = None
    
    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'file_input'

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

    @pytest.fixture
    def send_comm_kwargs(self, instance, icomm_name):
        r"""dict: Keyword arguments for send comm."""
        out = instance.icomm.opp_comm_kwargs()
        out['append'] = True
        return out

    @pytest.fixture
    def filepath(self, name, icomm_python_class, contents_to_write):
        r"""str: Path to the test file."""
        out = os.path.join(
            tempfile.gettempdir(),
            f'{name}_input{icomm_python_class._default_extension}')
        with open(out, 'wb') as fd:
            fd.write(contents_to_write)
        try:
            yield out
        finally:
            if os.path.isfile(out):
                os.remove(out)
    
    @pytest.fixture(scope="class")
    def contents_to_write(self, testing_options):
        r"""str: Contents that should be written to the file."""
        return testing_options['contents']

    @pytest.fixture
    def assert_before_stop(self, instance, recv_message_list,
                           recv_comm, testing_options, unyts_equality_patch,
                           pandas_equality_patch):
        r"""Assertions to make before stopping the driver instance."""
        def assert_before_stop_w():
            instance.sleep()
            recv_message_list(recv_comm, testing_options['recv'])
        return assert_before_stop_w
    
    # These are disabled to prevent writting extraneous data
    @pytest.fixture(scope="class")
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        def run_before_terminate_w():
            pass
        return run_before_terminate_w


class TestPandasInputDriver(TestFileInputDriver):
    r"""Test class for FileInputDriver reading from a pandas table."""
    
    @pytest.fixture(scope="class")
    def filetype(self):
        r"""str: Name of the file type being tested."""
        return 'pandas'

    @pytest.fixture(scope="class")
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {'not_as_frames': True}


class TestAsciiTableArrayInputDriver(TestFileInputDriver):
    r"""Test class for FileInputDriver reading from a table as an array."""

    @pytest.fixture(scope="class")
    def filetype(self):
        r"""str: Name of the file type being tested."""
        return 'table'

    @pytest.fixture(scope="class")
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {'array_columns': True}
