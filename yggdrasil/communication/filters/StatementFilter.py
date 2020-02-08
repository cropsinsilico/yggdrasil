import numpy as np
from yggdrasil import units
from yggdrasil.tools import safe_eval
from yggdrasil.communication.filters.FilterBase import FilterBase


class StatementFilter(FilterBase):
    r"""Class for filtering messages based on a provided statement using Python syntax.

    Args:
        statement (str): Python statement in terms of the message as represented by
            the string "%x%" that should evaluate to a boolean, True if the message
            should pass through the filter, False if it should not. The statement
            should only use a limited set of builtins and the math library (See
            yggdrasil.tools.safe_eval). If more complex relationships are required,
            use the FunctionFilter class.

    Attributes:
        statement (str): Python statement that will be evaluated to determine if
            messages should or should not pass the filter.

    """
    _filtertype = 'statement'
    _schema_required = ['statement']
    _schema_properties = {'statement': {'type': 'string'}}

    def __init__(self, *args, **kwargs):
        super(StatementFilter, self).__init__(*args, **kwargs)
        self.statement = self.statement.replace('%x%', 'x')

    def evaluate_filter(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        return safe_eval(self.statement, x=x)

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the filter class.

        Returns:
            list: Mutiple dictionaries of keywords and messages that will
                pass/fail for those keywords.
        
        """
        out = [{'kwargs': {'statement': '%x% != 2'},
                'pass': [1, 3], 'fail': [2]},
               {'kwargs': {'statement': '%x% != array([0, 0, 0])'},
                'pass': [np.ones(3, int)], 'fail': [np.zeros(3, int)]},
               {'kwargs': {'statement': '%x% != add_units(1, "cm")'},
                'pass': [units.add_units(2, 'cm')],
                'fail': [units.add_units(1, 'cm')]},
               {'kwargs': {'statement': '%x% != '
                           + repr(units.add_units(1, 'cm'))},
                'pass': [units.add_units(2, 'cm')],
                'fail': [units.add_units(1, 'cm')]}]
        return out
