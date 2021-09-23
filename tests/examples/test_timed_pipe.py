import pytest
import os
from tests.examples import TestExample as base_class
from yggdrasil.tools import get_supported_comm


_commtypes = sorted([x for x in get_supported_comm(dont_include_value=True)
                     if x not in ['value', 'buffer', 'rmq_async']])


@pytest.mark.parametrize("commtype", _commtypes, indirect=True)
class TestTimedPipeBase(base_class):
    r"""Base class for testing TimedPipe example with various comm types."""

    examples = ['timed_pipe']

    @pytest.fixture(scope="class")
    def env(self):
        r"""dict: Environment variables set for the test."""
        return {'PIPE_MSG_COUNT': '10',
                'PIPE_MSG_SIZE': '1024'}
        
    @pytest.fixture
    def results(self, env):
        r"""Result that should be found in output files."""
        siz = int(env['PIPE_MSG_COUNT']) * int(env['PIPE_MSG_SIZE'])
        res = '0' * siz
        return [res]

    @pytest.fixture
    def output_files(self, tempdir):
        r"""Output file."""
        return [os.path.join(tempdir, 'output_timed_pipe.txt')]
