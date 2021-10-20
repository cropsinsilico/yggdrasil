import os
import numpy as np
import pandas as pd
from yggdrasil import units, tools
from yggdrasil.components import ComponentError, create_component


def get_test_data(transform=None):
    r"""Determine a test data set for the specified type.

    Returns:
        object: Example of specified datatype.

    """
    if transform is None:
        transform = os.environ['TEST_TRANSFORM']
    umol = b'\xce\xbcmol'.decode('utf-8')
    field_names = ['name', 'count', 'size']
    field_units = ['n/a', umol, 'cm']
    dtype = np.dtype(
        {'names': field_names,
         'formats': ['S5', 'i4', 'f8']})
    rows = [(b'one', np.int32(1), 1.0),
            (b'two', np.int32(2), 2.0),
            (b'three', np.int32(3), 3.0)]
    arr = np.array(rows, dtype=dtype)
    lst = [units.add_units(arr[n], u) for n, u
           in zip(field_names, field_units)]
    if transform == 'table':
        return list(rows[0])
    return lst


def check_received_data(transform, x_recv):
    r"""Check that the received message is equivalent to the
    test data for the specified type.

    Args:
        transform (str): Name of transform being tested.
        x_recv (object): Received object.

    Raises:
        AssertionError: If the received message is not equivalent
            to the received message.

    """
    try:
        t = create_component('transform', subtype=transform)
    except ComponentError:
        def t(x):
            return x
    x_sent = t(get_test_data(transform))
    print('RECEIVED:')
    tools.pprint_encoded(x_recv)
    print('EXPECTED:')
    tools.pprint_encoded(x_sent)
    if isinstance(x_sent, np.ndarray):
        np.testing.assert_array_equal(x_recv, x_sent)
    elif isinstance(x_sent, pd.DataFrame):
        pd.testing.assert_frame_equal(x_recv, x_sent)
    else:
        assert(x_recv == x_sent)
