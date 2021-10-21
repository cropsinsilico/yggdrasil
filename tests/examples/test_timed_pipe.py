import pytest
import os
from tests.examples import TestExample as base_class


class TestTimedPipeBase(base_class):
    r"""Base class for testing TimedPipe example with various comm types."""

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "timed_pipe"

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

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self, request, check_required_comms, change_default_comm,
                 language, running_service):
        r"""str: Comm used by the current test."""
        out = request.param
        if out in ['value', 'buffer', 'rmq_async']:
            pytest.skip("invalid commtype for integration")
        check_required_comms([out], language=language)
        with change_default_comm(out):
            if out == 'ipc':
                from yggdrasil.communication.IPCComm import (
                    ipcrm_queues, ipc_queues)
                qlist = ipc_queues()
                if qlist:  # pragma: debug
                    print('Existing queues:', qlist)
                    ipcrm_queues()
            if out == 'rest':
                with running_service('flask', partial_commtype='rest'):
                    yield out
            else:
                yield out
