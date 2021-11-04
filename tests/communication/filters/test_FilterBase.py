import pytest
from tests import TestComponentBase as base_class


class TestFilterBase(base_class):
    r"""Test for FilterBase communication flass."""

    _component_type = 'filter'

    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, filter):
        r"""Subtype of component being tested."""
        return filter

    @pytest.fixture(scope="class", autouse=True)
    def filter(self, request):
        r"""str: Filter being tested."""
        return request.param

    @pytest.fixture
    def instance_kwargs(self, testing_options):
        r"""Keyword arguments for a new instance of the tested class."""
        out = {}
        if testing_options:
            out = dict(testing_options[0].get('kwargs', {}))
        return out

    def test_filter(self, python_class, testing_options):
        r"""Test filter."""
        for x in testing_options:
            inst = python_class(**x.get('kwargs', {}))
            for msg in x.get('pass', []):
                assert(inst(msg) is True)
            for msg in x.get('fail', []):
                assert(inst(msg) is False)
            for msg, err in x.get('error', []):
                with pytest.raises(err):
                    inst(msg)
