import os
from yggdrasil.examples.tests.test_types import TestExampleTypes


def dst(received_data):
    typename = os.environ.get('TEST_TYPENAME', None)
    assert(typename is not None)
    TestExampleTypes.check_received_data(typename, received_data)
    print('CONFIRMED: %s' % typename)
    return
