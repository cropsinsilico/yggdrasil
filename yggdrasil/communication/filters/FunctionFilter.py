import numpy as np
from yggdrasil import units
from yggdrasil.communication.filters.FilterBase import FilterBase


class FunctionFilter(FilterBase):
    r"""Class for filtering messages based on a provided function using Python syntax.

    Args:
        function (func): The handle for a callable Python object (e.g. function)
            that should be used to determine if a message should be filtered or
            a string of the form "<function file>:<function name>" identifying
            a function where "<function file>" is the module or Python file
            containing the function and "<function name>" is the name of the function.
            The function should take the message as input and return a boolean, True
            if the message should pass through the filter, False if it should not.

    """
    _filtertype = 'function'
    _schema_required = ['function']
    _schema_properties = {'function': {'type': 'function'}}

    def evaluate_filter(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        return self.function(x)
    
    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the filter class.

        Returns:
            list: Mutiple dictionaries of keywords and messages that will
                pass/fail for those keywords.
        
        """

        def fcond(x):
            return (units.get_data(x) != 3)
        
        return [{'kwargs': {'function': fcond},
                 'pass': [1, 2, units.add_units(1, 'cm'),
                          np.ones(3, int),
                          units.add_units(np.ones(3, int), 'cm')],
                 'fail': [3, units.add_units(3, 'cm'),
                          3 * np.ones(3, int),
                          units.add_units(3 * np.ones(3, int), 'cm')]}]
