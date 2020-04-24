from yggdrasil.tests import generate_component_tests
from yggdrasil.communication.transforms.tests.test_TransformBase import TestTransformBase


generate_component_tests('transform', TestTransformBase,
                         globals(), __file__, class_attr='transform')


__all__ = []
