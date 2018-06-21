#
# This should not be used directly by modelers
#
import os
import sys
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.schema import register_component


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


@register_component
class PythonModelDriver(ModelDriver):
    r"""Class for running Python models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            after the call to python.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """

    _language = 'python'

    def __init__(self, name, args, **kwargs):
        super(PythonModelDriver, self).__init__(name, args, **kwargs)
        self.debug(args)
        
        if 'python' not in self.args[0] or self.args[0].endswith('.py'):
            python_exec = sys.executable
            self.args = [python_exec] + self.args
