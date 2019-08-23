import numpy as np
import pandas as pd
import logging
from collections import OrderedDict
from yggdrasil import serialize, backwards, platform
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver
from yggdrasil.drivers.CModelDriver import CModelDriver
from yggdrasil.languages.R import install


logger = logging.getLogger(__name__)


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
    # Dynamically setting the interface library causes circular a import so
    # it is defined here statically. For dynamic import, use the following:
    #     interface_library = PythonModelDriver.interface_library
    interface_library = 'yggdrasil'
    interface_dependencies = install.requirements_from_description()
    # The Batch version causes output to saved to a file rather than directed to
    # stdout so use Rscript instead. For the batch version, use the following:
    #     default_interpreter_flags = ['CMD', 'BATCH' '--vanilla', '--silent']
    default_interpreter_flags = ['--default-packages=methods,utils']
    send_converters = {'table': serialize.consolidate_array}
    type_map = {
        'int': 'integer, bit64::integer64',
        'float': 'double',
        'string': 'character',
        'array': 'list',
        'object': 'list',
        'boolean': 'logical',
        'null': 'NULL',
        'uint': 'integer',
        'complex': 'complex',
        'bytes': 'char (utf-8)',
        'unicode': 'char',
        '1darray': 'list',
        'ndarray': 'list',
        'ply': 'PlyDict',
        'obj': 'ObjDict',
        'schema': 'list'}
    function_param = {
        'import': 'source(\"{filename}\")',
        'interface': 'library(yggdrasil)',
        'input': '{channel} <- YggInterface(\"YggInput\", \"{channel_name}\")',
        'output': '{channel} <- YggInterface(\"YggOutput\", \"{channel_name}\")',
        'table_input': ('{channel} <- YggInterface(\"YggAsciiTableInput\", '
                        '\"{channel_name}\")'),
        'table_output': ('{channel} <- YggInterface(\"YggAsciiTableOutput\", '
                         '\"{channel_name}\", \"{format_str}\")'),
        'recv': 'c({flag_var}, {recv_var}) %<-% {channel}$recv()',
        'send': '{flag_var} <- {channel}$send({send_var})',
        'function_call': '{output_var} <- {function_name}({input_var})',
        'define': '{variable} <- {value}',
        'true': 'TRUE',
        'not': '!',
        'comment': '#',
        'indent': 2 * ' ',
        'quote': '\"',
        'print': 'print(\"{message}\")',
        'fprintf': 'print(sprintf(\"{message}\", {variables}))',
        'error': 'stop(\"{error_msg}\")',
        'block_end': '}',
        'if_begin': 'if({cond}) {{',
        'for_begin': 'for ({iter_var} in {iter_begin}:{iter_end}) {{',
        'while_begin': 'while ({cond}) {{',
        'try_begin': 'tryCatch({',
        'try_except': '}}, error = function({error_var}) {{',
        'try_end': '})',
        'assign': '{name} <- {value}'}

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        if lib not in cls._library_cache:
            try:
                cls.run_executable(['-e', 'library(%s)' % lib])
                cls._library_cache[lib] = True
            except RuntimeError:
                cls._library_cache[lib] = False
        return cls._library_cache[lib]
        
    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's
                method.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        kwargs.setdefault('skip_interpreter_flags', True)
        return super(RModelDriver, cls).language_version(**kwargs)

    # @property
    # def debug_flags(self):
    #     r"""list: Flags that should be prepended to an executable command to
    #     enable debugging."""
    #     if self.with_valgrind:
    #         interp = 'R'.join(self.get_interpreter().rsplit('Rscript', 1))
    #         return [interp, '-d', '"valgrind %s"'
    #                 % ' '.join(self.valgrind_flags), '--vanilla', '-f']
    #     return super(RModelDriver, self).debug_flags
        
    def set_env(self):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(RModelDriver, self).set_env()
        out['RETICULATE_PYTHON'] = PythonModelDriver.get_interpreter()
        c_linker = CModelDriver.get_tool('linker')
        search_dirs = c_linker.get_search_path(conda_only=True)
        out = CModelDriver.update_ld_library_path(out, paths_to_add=search_dirs,
                                                  add_to_front=True)
        return out
        
    @classmethod
    def comm_atexit(cls, comm):  # pragma: no cover
        r"""Operations performed on comm at exit including draining receive.
        
        Args:
            comm (CommBase): Communication object.

        """
        if comm.direction == 'recv':
            while comm.recv(timeout=0)[0]:
                comm.sleep()
        else:
            comm.send_eof()
        if not getattr(comm, 'dont_backlog', True):
            comm.linger_close()

    @classmethod
    def language2python(cls, robj):
        r"""Prepare an R object for serialization in Python.

        Args:
           robj (object): Python object prepared in R.

        Returns:
            object: Python object in a form that is serialization friendly.

        """
        logger.debug("language2python: %s, %s" % (robj, type(robj)))
        if isinstance(robj, tuple):
            return tuple([cls.language2python(x) for x in robj])
        elif isinstance(robj, list):
            return [cls.language2python(x) for x in robj]
        elif isinstance(robj, dict):
            return {k: cls.language2python(v) for k, v in robj.items()}
        elif isinstance(robj, backwards.string_types):
            return backwards.as_bytes(robj)
        return robj

    @classmethod
    def python2language(cls, pyobj):
        r"""Prepare a python object for transformation in R.

        Args:
            pyobj (object): Python object.

        Returns:
            object: Python object in a form that is R friendly.

        """
        logger.debug("python2language: %s, %s" % (pyobj, type(pyobj)))
        if isinstance(pyobj, tuple):
            return tuple([cls.python2language(x) for x in pyobj])
        elif isinstance(pyobj, list):
            return [cls.python2language(x) for x in pyobj]
        elif isinstance(pyobj, OrderedDict):
            return OrderedDict([(backwards.as_str(k), cls.python2language(v))
                                for k, v in pyobj.items()])
        elif isinstance(pyobj, dict):
            return {backwards.as_str(k): cls.python2language(v)
                    for k, v in pyobj.items()}
        elif isinstance(pyobj, tuple(list(backwards.string_types)
                                     + [np.string_])):
            return backwards.as_str(pyobj)
        elif isinstance(pyobj, pd.DataFrame):
            # R dosn't have int64 and will cast 64bit ints as floats if passed
            # without casting them to int32 first
            for n in pyobj.columns:
                if pyobj[n].dtype == np.dtype('int64'):
                    pyobj[n] = pyobj[n].astype('int32')
                elif ((not backwards.PY2)
                      and (pyobj[n].dtype == np.dtype('object'))
                      and isinstance(pyobj[n][0], backwards.bytes_type)):
                    pyobj[n] = pyobj[n].apply(backwards.as_str)
        return pyobj
    
    @classmethod
    def write_model_wrapper(cls, model_file, model_function, **kwargs):
        r"""Return the lines required to wrap a model function as an integrated
        model.

        Args:
            model_file (str): Full path to the file containing the model
                function's declaration.
            model_function (str): Name of the model function.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Lines of code wrapping the provided model with the necessary
                code to run it as part of an integration.

        """
        if platform._is_win:  # pragma: windows
            model_file = model_file.replace('\\', '/')
        return super(RModelDriver, cls).write_model_wrapper(
            model_file, model_function, **kwargs)
