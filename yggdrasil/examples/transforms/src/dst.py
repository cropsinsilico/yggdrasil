import os
from yggdrasil.examples.tests.test_transforms import TestExampleTransforms


def dst(received_data):
    transform = os.environ['TEST_TRANSFORM']
    TestExampleTransforms.check_received_data(transform, received_data)
    print('CONFIRMED')
    return
