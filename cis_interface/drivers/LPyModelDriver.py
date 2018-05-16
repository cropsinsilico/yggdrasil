#
# This should not be used directly by modelers
#
import os
import sys
from logging import warning
from cis_interface.drivers.ModelDriver import ModelDriver
try:  # pragma: lpy
    from openalea import lpy
    _lpy_installed = True
except ImportError:  # pragma: no lpy
    warning("Could not import openalea.lpy. " +
            "LPy support will be disabled.")
    _lpy_installed = False


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


class LPyModelDriver(ModelDriver):  # pragma: lpy
    r"""Class for running LPy models.

    Args:
        name (str): Driver name.
        args (str): The LPy l-system file.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """

    def __init__(self, name, args, **kwargs):
        if not _lpy_installed:  # pragma: no lpy
            raise RuntimeError("LPy is not installed.")
        super(LPyModelDriver, self).__init__(name, args, **kwargs)
        self.debug(args)
        self.args = [sys.executable, _model_script] + self.args
