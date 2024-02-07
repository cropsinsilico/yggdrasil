import os
from yggdrasil.dev.pytest_plugin import check_received_data


def dst(received_data):
    typename = os.environ.get('TEST_TYPENAME', None)
    assert typename is not None
    check_received_data(typename, received_data)
    print('CONFIRMED: %s' % typename)
    return
