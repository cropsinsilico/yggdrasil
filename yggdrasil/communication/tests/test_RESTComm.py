import pytest
import unittest
from yggdrasil.communication import RESTComm
from yggdrasil.communication.tests import test_CommBase
from yggdrasil.tests.test_services import running_service


_rest_installed = RESTComm.RESTComm.is_installed(language='python')


@unittest.skipIf(not _rest_installed, "REST library not installed")
class TestRESTComm(test_CommBase.TestCommBase):
    r"""Test for RESTComm communication class."""

    comm = 'RESTComm'

    @pytest.fixture(scope="class", autouse=True)
    def running_service(self):
        with running_service('flask', partial_commtype='rest') as cli:
            yield cli
