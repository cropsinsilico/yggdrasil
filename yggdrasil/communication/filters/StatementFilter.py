import importlib
import numpy as np
from yggdrasil import units
from yggdrasil.communication.filters.FilterBase import FilterBase


class StatementFilter(FilterBase):
    r"""Class for filtering messages based on a provided statement using Python syntax.

    Args:
        statement (str): Python statement in terms of the message as represented by
            the string "%x%" that should evaluate to a boolean, True if the message
            should pass through the filter, False if it should not. The statement
            should only use a limited set of builtins and the math library (See
            safe_dict attribute). If more complex relationships are required, use
            the FunctionFilter class.

    Attributes:
        statement (str): Python statement that will be evaluated to determine if
            messages should or should not pass the filter.
        safe_dict (dict): Mapping of functions from the builtins and math modules
            that will be available to the statement.

    """
    _filtertype = 'statement'
    _schema_required = ['statement']
    _schema_properties = {'statement': {'type': 'string'}}
    _safe_lists = {'math': ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos',
                            'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod',
                            'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi',
                            'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'],
                   'builtins': ['abs', 'any', 'bool', 'bytes', 'float', 'int', 'len',
                                'list', 'map', 'max', 'min', 'repr', 'set', 'str',
                                'sum', 'tuple', 'type'],
                   'numpy': ['array', 'int8', 'int16', 'int32', 'int64',
                             'uint8', 'uint16', 'uint32', 'uint64',
                             'float16', 'float32', 'float64']}
    _no_eval_class = {}

    def __init__(self, *args, **kwargs):
        self.safe_dict = {}
        if units._use_unyt:
            self._safe_lists['unyt.array'] = ['unyt_quantity', 'unyt_array']
        else:
            self.safe_dict['Quantity'] = units._unit_quantity
            self._no_eval_class['Quantity'] = 'Quantity'
        for mod_name, func_list in self._safe_lists.items():
            mod = importlib.import_module(mod_name)
            for func in func_list:
                self.safe_dict[func] = getattr(mod, func)
        super(StatementFilter, self).__init__(*args, **kwargs)
        self.statement = self.format_statement(self.statement)

    def format_statement(self, statement):
        r"""Format the filter statement replacing the variable stand-in %x% and
        replacing classes that are not expressed in an eval friendly way but
        are safe listed in self._no_eval_class.

        Args:
            statement (str): Statement that should be modified.

        Returns:
            str: Statement with classes replaced with eval friendly expression.s

        """
        statement = statement.replace('%x%', 'x')
        # The following replaces <Class Name(a, b)> style reprs with calls to classes
        # identified in self._no_eval_class
        # regex = r'<([^<>]+)\(([^\(\)]+)\)>'
        # while True:
        #     match = re.search(regex, statement)
        #     if not match:
        #         break
        #     cls_repl = self._no_eval_class.get(match.group(1), False)
        #     if not cls_repl:
        #         raise ValueError("Expression '%s' in '%s' is not eval friendly."
        #                          % (match.group(0), statement))
        #     statement = statement.replace(match.group(0),
        #                                   '%s(%s)' % (cls_repl, match.group(2)), 1)
        return statement

    def evaluate_filter(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        safe_dict = dict(self.safe_dict, x=x)
        return eval(self.statement, {"__builtins__": None}, safe_dict)

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
                'pass': [np.ones(3, int)], 'fail': [np.zeros(3, int)]}]
        if units._use_unyt:
            out.append({'kwargs': {'statement': '%x% != '
                                   + repr(units.add_units(1, 'cm'))},
                        'pass': [units.add_units(2, 'cm')],
                        'fail': [units.add_units(1, 'cm')]})
        return out
