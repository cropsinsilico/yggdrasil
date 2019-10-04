import os
import pprint
from yggdrasil.tests import assert_equal
from yggdrasil.examples.tests.test_types import TestExampleTypes


def dst(received_data):
    typename = os.environ.get('TEST_TYPENAME', None)
    assert(typename is not None)
    expected_data = TestExampleTypes.get_test_data(typename)
    print('RECEIVED:')
    pprint.pprint(received_data)
    print('EXPECTED:')
    pprint.pprint(expected_data)
    assert_equal(received_data, expected_data)
    print('CONFIRMED: %s' % typename)
    return
