import subprocess
import numpy as np
import pandas as pd
from yggdrasil import serialize, backwards
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver
from yggdrasil.drivers.CModelDriver import CModelDriver


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
    interface_library = 'yggdrasil'
    interface_dependencies = ['reticulate', 'zeallot', 'bit64']
    # interface_library = PythonModelDriver.interface_library
    # The Batch version causes output to saved to a file rather than directed to
    # stdout
    default_interpreter_flags = ['--default-packages=methods,utils']
    # default_interpreter_flags = ['CMD', 'BATCH' '--vanilla', '--silent']
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
        'interface': 'library(yggdrasil)',
        'input': '{channel} <- YggInterface(\"YggInput\", \"{channel_name}\")',
        'output': '{channel} <- YggInterface(\"YggOutput\", \"{channel_name}\")',
        'table_input': ('{channel} <- YggInterface(\"YggAsciiTableInput\", '
                        '\"{channel_name}\")'),
        'table_output': ('{channel} <- YggInterface(\"YggAsciiTableOutput\", '
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
                cls.run_executable(['-e', '\"library(%s)\"' % lib])
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

    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        out = super(RModelDriver, cls).configure(cfg)
        if cls.are_dependencies_installed() and (not cls.is_interface_installed()):
            subprocess.check_output(['ygginstall', 'R', '--skip-requirements'])
        return out
        
    def add_debug_flags(self, command):
        r"""Add valgrind flags with the command.

        Args:
            command (list): Command that debug commands should be added to.

        Returns:
            list: Command updated with debug commands.

        """
        if self.with_valgrind:
            interp = 'R'.join(self.get_interpreter().rsplit('Rscript', 1))
            return [interp, '-d', '"valgrind %s"'
                    % ' '.join(self.valgrind_flags), '--vanilla', '-f'] + command
        return super(RModelDriver, self).add_debug_flags(command)
        
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
    def comm_atexit(cls, comm):
        r"""Operations performed on comm at exit including draining receive.
        
        Args:
            comm (CommBase): Communication object.

        """
        if comm.direction == 'recv':
            while comm.recv(timeout=0)[0]:
                comm.sleep()
        else:
            comm.send_eof()
        comm.linger_close()

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
            return {k: cls.language2python(v) for k, v in robj.items()}
        elif isinstance(robj, backwards.string_types):
            # print("language2python", type(robj), len(robj))
            return backwards.as_bytes(robj)
        elif isinstance(robj, pd.DataFrame):
            # R dosn't have int64 and will cast as float if passed
            for n in robj.columns:
                print("language2python", n, robj[n].dtype)
        return robj

    @classmethod
    def python2language(cls, pyobj):
        r"""Prepare a python object for transformation in R.

        Args:
            pyobj (object): Python object.

        Returns:
            object: Python object in a form that is R friendly.

        """
        # print("python2language", pyobj, type(pyobj))
        if isinstance(pyobj, tuple):
            return tuple([cls.python2language(x) for x in pyobj])
        elif isinstance(pyobj, list):
            return [cls.python2language(x) for x in pyobj]
        elif isinstance(pyobj, dict):
            return {backwards.as_str(k): cls.python2language(v)
                    for k, v in pyobj.items()}
        elif isinstance(pyobj, backwards.string_types):
            # print("python2language", type(pyobj), len(pyobj))
            return backwards.as_str(pyobj)
        elif isinstance(pyobj, np.string_):
            return backwards.as_str(pyobj)
        elif isinstance(pyobj, pd.DataFrame):
            # R dosn't have int64 and will cast as float if passed
            for n in pyobj.columns:
                print("python2language", n, pyobj[n].dtype)
                if pyobj[n].dtype == np.dtype('int64'):
                    pyobj[n] = pyobj[n].astype('int32')
                elif ((not backwards.PY2)
                      and (pyobj[n].dtype == np.dtype('object'))
                      and isinstance(pyobj[n][0], backwards.bytes_type)):
                    pyobj[n] = pyobj[n].apply(backwards.as_str)
        return pyobj
