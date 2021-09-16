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
    def running_service(self, request):
        manager = request.config.pluginmanager
        plugin_class = manager.get_plugin('pytest_cov').CovPlugin
        plugin = None
        for x in manager.get_plugins():
            if isinstance(x, plugin_class):
                plugin = x
                break
        with running_service('flask', partial_commtype='rest',
                             with_coverage=(plugin is not None)) as cli:
            yield cli
