#
# This should not be used directly by modelers
#
import os
from cis_interface.drivers.ModelDriver import ModelDriver


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


class PythonModelDriver(ModelDriver):
    r"""Class for running Python models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            after the call to python.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):
        -

    """

    def __init__(self, name, args, **kwargs):
        super(PythonModelDriver, self).__init__(name, args, **kwargs)
        self.debug(args)
        
        if 'python' not in self.args[0] or self.args[0].endswith('.py'):
            self.args = ['python'] + self.args
