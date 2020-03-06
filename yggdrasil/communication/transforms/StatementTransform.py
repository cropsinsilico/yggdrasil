import numpy as np
from yggdrasil import units
from yggdrasil.tools import safe_eval
from yggdrasil.communication.transforms.TransformBase import TransformBase


class StatementTransform(TransformBase):
    r"""Class for transforming messages based on a provided statement using Python syntax.

    Args:
        statement (str): Python statement in terms of the message as represented by
            the string "%x%" that should evaluate to the transformed message.
            The statement should only use a limited set of builtins and the math
            library (See yggdrasil.tools.safe_eval). If more complex relationships
            are required, use the FunctionTransform class.

    Attributes:
        statement (str): Python statement that will be evaluated to transform
            messages.

    """
    _transformtype = 'statement'
    _schema_required = ['statement']
    _schema_properties = {'statement': {'type': 'string'}}

    def __init__(self, *args, **kwargs):
        super(StatementTransform, self).__init__(*args, **kwargs)
        self.statement = self.statement.replace('%x%', 'x')

    def evaluate_transform(self, x, no_copy=False):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_copy (bool, optional): If True, the transformation occurs in
                place. Otherwise a copy is created and transformed. Defaults
                to False.

        Returns:
            bool: True if the message will pass through the transform, False otherwise.

        """
        return safe_eval(self.statement, x=x)

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        out = [{'kwargs': {'statement': '%x%**3'},
                'in/out': [(1, 1), (2, 8)]},
               {'kwargs': {'statement': '%x% * array([1, 1, 1])'},
                'in/out': [(1, np.ones(3, int)), (2, 2 * np.ones(3, int))]},
               {'kwargs': {'statement': '%x% * '
                           + repr(units.add_units(1, 'cm'))},
                'in/out': [(1, units.add_units(1, 'cm')),
                           (2, units.add_units(2, 'cm'))]}]
        return out
