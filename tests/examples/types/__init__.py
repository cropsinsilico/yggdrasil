import pprint
import numpy as np
from yggdrasil import rapidjson


class ExampleClass(object):

    def __init__(self, *args, **kwargs):
        self._input_args = args
        self._input_kwargs = kwargs

    def __str__(self):
        return str((self._input_args, self._input_kwargs))

    def __eq__(self, solf):
        if not isinstance(solf, ExampleClass):
            return False
        if not self._input_kwargs == solf._input_kwargs:
            return False
        return self._input_args == solf._input_args


def get_test_data(typename):
    r"""Determine a test data set for the specified type.

    Args:
        typename (str): Name of datatype.

    Returns:
        object: Example of specified datatype.

    """
    x = {'type': typename}
    prop_names = 'abcdefghijklmnopqrstuvwxyg'
    prop_types = [{'type': 'number'}, {'type': 'string'}]
    if typename == 'array':
        x['items'] = prop_types
    elif typename == 'object':
        x['properties'] = {
            k: xx for k, xx in zip(prop_names, prop_types)}
    elif typename == 'class':
        return ExampleClass
    elif typename == 'instance':
        return ExampleClass(1, 'b', c=2, d='d')
    return rapidjson.generate_data(x)


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
        assert x_recv == x_sent
