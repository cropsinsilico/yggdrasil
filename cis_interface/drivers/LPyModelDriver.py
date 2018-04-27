#
# This should not be used directly by modelers
#
import os
import sys
from cis_interface.drivers.ModelDriver import ModelDriver


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


class LPyModelDriver(ModelDriver):
    r"""Class for running LPy models.

    Args:
        name (str): Driver name.
        args (str): The LPy l-system file.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """

    def __init__(self, name, args, **kwargs):
        super(LPyModelDriver, self).__init__(name, args, **kwargs)
        self.debug(args)
        self.args = [sys.executable, _model_script, self.args[0]]
