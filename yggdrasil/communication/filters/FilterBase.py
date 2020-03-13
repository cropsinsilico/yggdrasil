import numpy as np
from yggdrasil.components import ComponentBase


class FilterBase(ComponentBase):
    r"""Base class for message filters.

    Args:
        initial_state (dict, optional): Dictionary of initial state variables
            that should be set when the filter is created.

    """

    _filtertype = None
    _schema_type = 'filter'
    _schema_subtype_key = 'filtertype'
    _schema_properties = {'initial_state': {'type': 'object'}}

    def __init__(self, *args, **kwargs):
        self._state = {}
        super(FilterBase, self).__init__(*args, **kwargs)
        if self.initial_state:
            self._state = self.initial_state

    def evaluate_filter(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        raise NotImplementedError

    def __call__(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        out = self.evaluate_filter(x)
        if isinstance(out, np.ndarray):
            assert(out.dtype == bool)
            out = bool(out.all())
        elif isinstance(out, np.bool_):
            out = bool(out)
        try:
            assert(isinstance(out, bool))
        except AssertionError:  # pragma: debug
            print(out, type(out))
            raise
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the filter class.

        Returns:
            list: Mutiple dictionaries of keywords and messages that will
                pass/fail for those keywords.
        
        """
        return [{'error': [(1, NotImplementedError)],
                 'kwargs': {'initial_state': {'a': int(1)}}}]
