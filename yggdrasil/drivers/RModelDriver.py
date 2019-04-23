import numpy as np
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


class RModelDriver(InterpretedModelDriver):  # pragma: R
    r"""Base class for running R models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """
    _schema_subtype_description = ('Model is written in R.')
    language = 'R'
    language_aliases = ['r']
    language_ext = '.R'
    base_languages = ['python']
    default_interpreter = 'Rscript'
    # Dynamically setting the interface library cause circular logic
    interface_library = 'yggdrasil.interface.YggInterface'
    # interface_library = PythonModelDriver.interface_library
    # The Batch version causes output to saved to a file rather than directed to
    # stdout
    # default_interpreter_flags = ['CMD', 'BATCH' '--vanilla', '--silent']
    function_param = {
        'interface': ['library(reticulate)',
                      'library(zeallot)',
                      'ygg <- import(\"{interface_library}\")'],
        'input': '{channel} <- ygg$YggInput(\"{channel_name}\")',
        'output': '{channel} <- ygg$YggOutput(\"{channel_name}\")',
        'table_input': '{channel} <- ygg$YggAsciiTableInput(\"{channel_name}\")',
        'table_output': ('{channel} <- ygg$YggAsciiTableOutput('
                         '\"{channel_name}\", \"{format_str}\")'),
        'recv': 'c({flag_var}, {recv_var}) %<-% {channel}$recv()',
        'send': '{flag_var} <- {channel}$send({send_var})',
        'true': 'TRUE',
        'not': '!',
        'comment': '#',
        'indent': 2 * ' ',
        'quote': '\"',
        'print': 'print(\"{message}\")',
        'fprintf': 'print(sprintf(\"{message}\", {variables}))',
        'block_end': '}',
        'if_begin': 'if({cond}) {',
        'for_begin': 'for ({iter_var} in {iter_begin}:{iter_end}) {',
        'while_begin': 'while ({cond}) {',
        'try_begin': 'tryCatch({',
        'try_except': '}, error = function({error_var}) {',
        'try_end': '})'}

    @classmethod
    def language2python(cls, robj):
        r"""Prepare an R object for serialization in Python.

        Args:
           robj (object): Python object prepared in R.

        Returns:
            object: Python object in a form that is serialization friendly.

        """
        # print("language2python", robj, type(robj))
        if isinstance(robj, tuple):
            return tuple([cls.language2python(x) for x in robj])
        elif isinstance(robj, list):
            return [cls.language2python(x) for x in robj]
        elif isinstance(robj, dict):
            return {k: cls.language2python(v) for k,v in robj.items()}
        elif isinstance(robj, int):
            # R integers are 32bit
            return np.int32(robj)
        return robj

    # @classmethod
    # def python2language(cls, pyobj):
    #     r"""Prepare a python object for transformation in R.

    #     Args:
    #         pyobj (object): Python object.

    #     Returns:
    #         object: Python object in a form that is R friendly.

    #     """
    #     print("python2language", pyobj, type(pyobj))
    #     if isinstance(pyobj, tuple):
    #         return tuple([cls.python2language(x) for x in pyobj])
    #     elif isinstance(pyobj, list):
    #         return [cls.python2language(x) for x in pyobj]
    #     elif isinstance(pyobj, dict):
    #         return {k: cls.python2language(v) for k, v in pyobj.items()}
    #     return pyobj
