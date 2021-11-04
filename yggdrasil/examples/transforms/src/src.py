from yggdrasil.tools import pprint_encoded
from yggdrasil.examples.transforms import get_test_data


def src():
    test_data = get_test_data()
    print('SENDING')
    pprint_encoded(test_data)
    return test_data
