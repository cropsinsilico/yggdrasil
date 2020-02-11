import os
from yggdrasil.languages import get_language_dir
from yggdrasil.drivers import CModelDriver
from yggdrasil.drivers.CompiledModelDriver import (
    CompilerBase, CompiledModelDriver)


class FortranCompilerBase(CompilerBase):
    r"""Base class for Fortran compilers."""
    languages = ['fortran']
    default_executable_env = 'FF'
    default_flags_env = 'FFLAGS'
    default_flags = ['-g', '-Wall']
    linker_attributes = {'default_flags_env': 'LFLAGS',
                         'search_path_env': ['LIBRARY_PATH', 'LD_LIBRARY_PATH']}
    search_path_env = []
    default_linker = None
    default_executable = None
    

class GFortranCompiler(FortranCompilerBase):
    r"""Interface class for G++ compiler/linker."""
    toolname = 'gfortran'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_archiver = 'ar'

    @classmethod
    def set_env(cls, **kwargs):
        r"""Set environment variables required for compilation.

        Args:
            **kwargs: Keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(GFortranCompiler, cls).set_env(**kwargs)
        conda_prefix = cls.get_conda_prefix()
        if conda_prefix:
            out.setdefault('DYLD_FALLBACK_LIBRARY_PATH', conda_prefix)
        return out


_top_lang_dir = get_language_dir('fortran')
_incl_interface = _top_lang_dir
    

class FortranModelDriver(CompiledModelDriver):
    r"""Class for running Fortran models."""
                
    _schema_subtype_description = ('Model is written in Fortran.')
    language = 'fortran'
    language_ext = ['.f77', '.f90', '.f', '.h']
    base_languages = ['c']
    interface_library = 'ygg'
    # To prevent inheritance
    default_compiler = 'gfortran'
    default_linker = None
    internal_libraries = {
        'ygg': {'source': os.path.join(_incl_interface,
                                       'YggInterface.f90'),
                'internal_dependencies': ['ygg_c'],
                'libtype': 'static'},
        'ygg_c': {'source': 'ygg', 'language': 'c',
                  'libtype': 'object'}}
    type_map = {
        'int': 'integer(kind = X)',
        'float': 'real',
        'string': 'character',
        'array': None,
        'object': None,
        'boolean': 'logical',
        'null': None,
        'uint': None,
        'complex': 'complex(kind = X)',
        'bytes': 'character',
        'unicode': None,
        
    }
    function_param = {
        'import_nofile': 'use {function}',
        'index': '{variable}({index})',
        'interface': 'use {interface_library}',
        'input': None,
        'output': None,
        'declare': '{type_name} :: {variable}',
        'assign': '{name} = {value}',
        'comment': '!',
        'true': '.true.',
        'false': '.false.',
        'not': '.not.',
        'and': '.and.',
        'or': '.or.',
        'indent': 3 * ' ',
        'quote': "'",
        'print': "print *, '{message}'",
        'fprintf': "Print \"{message}\", {variables}",
        'error': "print *, '{message}'\n return",
        # 'block_end': 'END {block_type}',
        'if_begin': 'IF ({cond}) THEN',
        'if_elif': 'ELSE IF ({cond}) THEN',
        'if_else': 'ELSE',
        'if_end': 'END IF',
        'for_begin': 'DO {iter_var} = {iter_begin}, {iter_end}',
        'for_end': 'END DO',
        'while_begin': 'DO WHILE ({cond})',
        'while_end': 'END DO',
        'break': 'EXIT',
        'exec_begin': ['PROGRAM main', '   implicit none'],
        'exec_end': 'END PROGRAM main',
        'free': 'DEALLOCATE({variable})',
        'function_def_begin': [
            'SUBROUTINE {function_name}({input_var}, {output_var})',
            '   {input_type} :: {input_var}',
            '   {output_type} :: {output_var}'],
        'return': 'return',
        'function_def_regex': (
            r'(?P<procedure_type>(?i:(?:subroutine)|(?:function)))\s+'
            r'{function_name}\s*\((?P<inputs>(?:[^\(]*?))\)\s*'
            r'(?:result\s*\({outputs}\))?\s*\n'
            r'(?P<body>(?:.*?\n?)*?)'
            r'(?i:end\s+(?P=procedure_type))\s+{function_name}')
    }
    outputs_in_inputs = True
    include_arg_count = True
    include_channel_obj = True
    is_typed = True
    
    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(FortranModelDriver, self).set_env(**kwargs)
        out = CModelDriver.CModelDriver.update_ld_library_path(out)
        return out
