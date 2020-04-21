from yggdrasil.tests import generate_component_tests
from yggdrasil.communication.tests.test_FileComm import TestFileComm


generate_component_tests('file', TestFileComm, globals(), __file__,
                         class_attr='comm')

__all__ = []
