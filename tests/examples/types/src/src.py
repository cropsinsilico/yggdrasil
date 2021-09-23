import os
import pprint
from tests.examples.types import get_test_data


def src():
    typename = os.environ.get('TEST_TYPENAME', None)
    assert(typename is not None)
    test_data = get_test_data(typename)
    print('SENDING: %s' % typename)
    pprint.pprint(test_data)
    return test_data
