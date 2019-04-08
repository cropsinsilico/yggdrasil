import os
import sys
import importlib
from yggdrasil import tools
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


class PythonModelDriver(InterpretedModelDriver):
    r"""Class for running Python models."""

    _schema_subtype_description = ('Model is written in Python.')
    language = 'python'
    language_ext = '.py'
    default_interpreter = sys.executable
    interface_library = 'yggdrasil.interface.YggInterface'
    supported_comms = tools.get_supported_comm()
    supported_comm_options = {
        'ipc': {'platforms': ['MacOS', 'Linux'],
                'libraries': ['sysv_ipc']},
        'zmq': {'libraries': ['zmq']},
        'rmq': {'libraries': ['pika']}}
    function_param = {
        'comment': '#',
        'indent': 4 * ' ',
        'block_end': '',
        'if_begin': 'if ({cond}):',
        'for_begin': 'for {iter_var} in range({iter_begin}, {iter_end}):',
        'while_begin': 'while ({cond}):',
        'try_begin': 'try:',
        'try_error_type': 'BaseException',
        'try_except': 'except {try_error} as {error_var}:'}

    @classmethod
    def is_language_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        # This is being run so python exists
        return True

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        try:
            importlib.import_module(lib)
        except ImportError:
            return False
        return True

    @classmethod
    def is_comm_installed(cls, **kwargs):
        r"""Determine if a comm is installed for the associated programming
        language.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            bool: True if a comm is installed for this language.

        """
        out = super(PythonModelDriver, cls).is_comm_installed(**kwargs)
        if not kwargs.get('skip_config'):
            return out
        if out and (kwargs.get('commtype', None) in ['rmq', 'rmq_async']):
            from yggdrasil.communication.RMQComm import check_rmq_server
            out = check_rmq_server()
        return out
