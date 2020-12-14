import pprint
from yggdrasil.tools import print_encoded
from yggdrasil.examples.tests.test_transforms import TestExampleTransforms


def src():
    test_data = TestExampleTransforms.get_test_data()
    print('SENDING')
    print_encoded(pprint.pformat(test_data))
    return test_data
