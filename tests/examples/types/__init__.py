import pprint
import numpy as np
from yggdrasil.metaschema.datatypes import get_type_class


def get_test_data(typename):
    r"""Determine a test data set for the specified type.

    Args:
        typename (str): Name of datatype.

    Returns:
        object: Example of specified datatype.

    """
    typeclass = get_type_class(typename)
    return typeclass.get_test_data()


def check_received_data(typename, x_recv):
    r"""Check that the received message is equivalent to the
    test data for the specified type.

    Args:
        typename (str): Name of datatype.
        x_recv (object): Received object.

    Raises:
        AssertionError: If the received message is not equivalent
            to the received message.

    """
    x_sent = get_test_data(typename)
    print('RECEIVED:')
    pprint.pprint(x_recv)
    print('EXPECTED:')
    pprint.pprint(x_sent)
    if isinstance(x_sent, np.ndarray):
        np.testing.assert_array_equal(x_recv, x_sent)
    else:
        assert(x_recv == x_sent)
