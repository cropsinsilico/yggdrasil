import os
import copy
from collections import OrderedDict
from yggdrasil import platform, tools
from yggdrasil.languages import get_language_dir
from yggdrasil.drivers import CModelDriver
from yggdrasil.drivers.CompiledModelDriver import (
    CompilerBase, CompiledModelDriver)


_top_lang_dir = get_language_dir('fortran')
_incl_interface = _top_lang_dir
_c_internal_libs = copy.deepcopy(CModelDriver.CModelDriver.internal_libraries)
    

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
    product_exts = ['mod']

    @classmethod
    def get_flags(cls, **kwargs):
        r"""Get a list of flags for the tool.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's
                method.

        Returns:
            list: Flags for the tool.

        """
        kwargs.setdefault('module-dir', _top_lang_dir)
        kwargs.setdefault('module-search-path', _top_lang_dir)
        return super(FortranCompilerBase, cls).get_flags(**kwargs)
        
    @classmethod
    def append_product(cls, products, src, new, new_dir=None,
                       dont_append_src=False):
        r"""Append a product to the specified list along with additional values
        indicated by cls.product_exts.

        Args:
            products (list): List of of existing products that new product
                should be appended to.
            src (list): Input arguments to compilation call that was used to
                generate the output file (usually one or more source files).
            new (str): New product that should be appended to the list.
            new_dir (str, optional): Directory that should be used as base when
                adding files listed in cls.product_files. Defaults to
                os.path.dirname(new).
            dont_append_src (bool, optional): If True and src is in the list of
                products, it will be removed. Defaults to False.

        """
        super(FortranCompilerBase, cls).append_product(
            products, src, new, new_dir=new_dir,
            dont_append_src=dont_append_src)
        if os.path.basename(new).startswith('YggInterface_f90'):
            products.append(os.path.join(_top_lang_dir,
                                         'fygg.mod'))


class GFortranCompiler(FortranCompilerBase):
    r"""Interface class for gfortran compiler/linker."""
    toolname = 'gfortran'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_archiver = 'ar'
    flag_options = OrderedDict(list(FortranCompilerBase.flag_options.items())
                               + [('module-dir', '-J%s'),
                                  ('module-search-path', '-I%s')])


# class IFortCompiler(FortranCompilerBase):
#     r"""Interface class for ifort compiler/linker."""
#     toolname = 'ifort'
#     platforms = ['MacOS', 'Linux', 'Windows']
#     default_archiver = 'ar'
#     flag_options = OrderedDict(list(FortranCompilerBase.flag_options.items())
#                                + [('module-dir', '-module'),
#                                   ('module-search-path', '-module')])


class FortranModelDriver(CompiledModelDriver):
    r"""Class for running Fortran models."""
                
    _schema_subtype_description = ('Model is written in Fortran.')
    language = 'fortran'
    language_ext = ['.f77', '.f90', '.f', '.h']
    base_languages = ['c']
    interface_library = 'fygg'
    # To prevent inheritance
    default_compiler = 'gfortran'
    default_linker = None
    external_libraries = CModelDriver.CModelDriver.external_libraries
    internal_libraries = dict(
        _c_internal_libs,
        fygg={'source': os.path.join(_incl_interface,
                                     'YggInterface.f90'),
              'libtype': 'static',
              'internal_dependencies': (
                  _c_internal_libs['ygg']['internal_dependencies']
                  + ['ygg']),
              'external_dependencies': (
                  _c_internal_libs['ygg']['external_dependencies']),
              'include_dirs': (
                  _c_internal_libs['ygg']['include_dirs'])})
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
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        cls.internal_libraries['ygg']['libtype'] = 'object'
        CompiledModelDriver.before_registration(cls)
        
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
        conda_prefix = tools.get_conda_prefix()
        if conda_prefix and platform._is_mac:
            out.setdefault('DYLD_FALLBACK_LIBRARY_PATH',
                           os.path.join(conda_prefix, 'lib'))
        return out
