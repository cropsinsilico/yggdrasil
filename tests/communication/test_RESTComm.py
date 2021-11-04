import pytest
from tests.communication.test_CommBase import TestComm as base_class


class TestRESTComm(base_class):
    r"""Test for RESTComm communication class."""

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "rest"

    @pytest.fixture(scope="class", autouse=True)
    def running_service(self, running_service):
        with running_service('flask', partial_commtype='rest') as cli:
            yield cli
