import os
import pprint
from yggdrasil.examples.tests.test_types import TestExampleTypes


def src():
    typename = os.environ.get('TEST_TYPENAME', None)
    assert(typename is not None)
    test_data = TestExampleTypes.get_test_data(typename)
    print('SENDING: %s' % typename)
    pprint.pprint(test_data)
    return test_data
