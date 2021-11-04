import os
from yggdrasil.examples.transforms import check_received_data


def dst(received_data):
    transform = os.environ['TEST_TRANSFORM']
    check_received_data(transform, received_data)
    print('CONFIRMED')
    return
