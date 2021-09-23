import pytest
from tests.communication import TestComm as base_class


class TestRESTComm(base_class):
    r"""Test for RESTComm communication class."""

    @pytest.fixture(scope="class", autouse=True, params=["rest"])
    def component_subtype(self, request):
        r"""Subtype of component being tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True, params=[False, True])
    def use_async(self, request):
        r"""Whether communicator should be asynchronous or not."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def running_service(self, running_service):
        with running_service('flask', partial_commtype='rest') as cli:
            yield cli
