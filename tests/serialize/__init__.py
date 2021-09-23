from yggdrasil.tests import generate_component_tests
from yggdrasil.serialize.tests.test_SerializeBase import TestSerializeBase


generate_component_tests('serializer', TestSerializeBase,
                         globals(), __file__)


__all__ = []
