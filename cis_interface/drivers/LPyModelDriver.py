#
# This should not be used directly by modelers
#
import os
import sys
from logging import warning
from cis_interface.drivers.ModelDriver import ModelDriver
try:  # pragma: lpy
    from openalea import lpy
except ImportError:  # pragma: no lpy
    warning("Could not import openalea.lpy. " +
            "LPy support will be disabled.")
    lpy = None
from cis_interface.schema import register_component
_lpy_installed = (lpy is not None)


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


@register_component
class LPyModelDriver(ModelDriver):  # pragma: lpy
    r"""Class for running LPy models.

    Args:
        name (str): Driver name.
        args (str): The LPy l-system file.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """

    _language = 'lpy'

    def __init__(self, name, args, **kwargs):
        if not _lpy_installed:  # pragma: no lpy
            raise RuntimeError("LPy is not installed.")
        super(LPyModelDriver, self).__init__(name, args, **kwargs)
        self.debug(args)
        self.args = [sys.executable, _model_script] + self.args
