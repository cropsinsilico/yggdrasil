from yggdrasil.tests import (
    generate_component_tests, generate_component_subtests)
from yggdrasil.communication.tests.test_FileComm import TestFileComm


generate_component_tests('file', TestFileComm, globals(), __file__,
                         class_attr='comm')
generate_component_subtests('comm', 'Async', globals(),
                            'yggdrasil.communication.tests',
                            new_attr={'use_async': True},
                            skip_subtypes=['default'])

__all__ = []
