from yggdrasil.tools import pprint_encoded
from yggdrasil.examples.tests.test_transforms import TestExampleTransforms


def src():
    test_data = TestExampleTransforms.get_test_data()
    print('SENDING')
    pprint_encoded(test_data)
    return test_data
