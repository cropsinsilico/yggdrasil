from yggdrasil.tests import generate_component_tests
from yggdrasil.communication.filters.tests.test_FilterBase import TestFilterBase


generate_component_tests('filter', TestFilterBase,
                         globals(), __file__, class_attr='filter')


__all__ = []
