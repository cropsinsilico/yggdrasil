import os
import re
import copy
from collections import OrderedDict
from yggdrasil import platform, tools
from yggdrasil.languages import get_language_dir
from yggdrasil.drivers import CModelDriver
from yggdrasil.drivers.CompiledModelDriver import (
    CompilerBase, CompiledModelDriver)
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    _valid_types)


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
        out = super(FortranCompilerBase, cls).get_flags(**kwargs)
        for x in ['-O', '-O2', '-O3', 'Os', 'Ofast']:
            if x in out:
                out.remove(x)
        return out
        
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
    language_ext = ['.f90', '.f77', '.f', '.h']
    base_languages = ['c']
    interface_library = 'fygg'
    # To prevent inheritance
    default_compiler = 'gfortran'
    default_linker = None
    supported_comm_options = dict(
        CModelDriver.CModelDriver.supported_comm_options,
        zmq={'libraries': [('c', x) for x in
                           CModelDriver.CModelDriver.supported_comm_options[
                               'zmq']['libraries']]})
    external_libraries = {'c++': {}}
    internal_libraries = dict(
        fygg={'source': os.path.join(_incl_interface,
                                     'YggInterface.f90'),
              'libtype': 'static',
              'internal_dependencies': (
                  [('c', x) for x in
                   _c_internal_libs['ygg']['internal_dependencies']]
                  + [('c', 'ygg'), 'c_wrappers']),
              'external_dependencies': (
                  [('c', x) for x in
                   _c_internal_libs['ygg']['external_dependencies']]),
              'include_dirs': (
                  _c_internal_libs['ygg']['include_dirs'])},
        c_wrappers={'source': os.path.join(_incl_interface,
                                           'c_wrappers.c'),
                    'language': 'c',
                    'libtype': 'object',
                    'internal_dependencies': [('c', 'ygg')],
                    'external_dependencies': (
                        [('c', x) for x in
                         _c_internal_libs['ygg']['external_dependencies']]),
                    'include_dirs': [_incl_interface]})
    type_map = {
        'comm': 'yggcomm',
        'dtype': 'yggdtype',
        'int': 'integer(kind = X)',
        'float': 'real(kind = X)',
        'string': 'character(len = X)',
        'array': 'yggarr',
        'object': 'yggmap',
        'integer': 'integer',
        'boolean': 'logical',
        'null': 'yggnull',
        'uint': 'integer(kind = X)',  # Fortran has no unsigned int
        'complex': 'complex(kind = X)',
        'bytes': 'character(len = X)',
        'unicode': 'character(len = X)',
        '1darray': '*',
        'ndarray': '*',
        '1darray_pointer': '{type}{precision}_1d',
        'ndarray_pointer': '{type}{precision}_nd',
        'ply': 'yggply',
        'obj': 'yggobj',
        'schema': 'yggschema',
        'flag': 'logical',
        'class': 'yggpyfunc',
        'instance': 'yggpyinst',
        'any': 'ygggeneric'}
    function_param = {
        'import_nofile': 'use {function}',
        'import': 'include "{filename}"',
        'index': '{variable}({index})',
        'interface': 'use fygg',
        'input': ('{channel} = ygg_input_type('
                  '\"{channel_name}\", {channel_type})'),
        'output': ('{channel} = ygg_output_type('
                   '\"{channel_name}\", {channel_type})'),
        'recv_heap': 'ygg_recv_var_realloc',
        'recv_stack': 'ygg_recv_var',
        'recv_function': 'ygg_recv_var_realloc',
        'send_function': 'ygg_send_var',
        'not_flag_cond': '.not.{flag_var}',
        'flag_cond': '{flag_var}',
        'declare': '{type_name} :: {variable}',
        'init_array': 'yggarr(init_generic())',
        'init_object': 'yggmap(init_generic())',
        'init_schema': 'yggschema(init_generic())',
        'init_ply': 'init_ply()',
        'init_obj': 'init_obj()',
        'init_class': 'yggpyfunc(init_python())',
        'init_function': 'yggpyfunc(init_python())',
        'init_instance': 'yggpyinst(init_generic())',
        'init_any': 'init_generic()',
        'init_type_array': ('create_dtype_json_array({nitems}, '
                            '{items}, {use_generic})'),
        'init_type_object': ('create_dtype_json_object({nitems}, '
                             '{keys}, {values}, {use_generic})'),
        'init_type_ply': 'create_dtype_ply({use_generic})',
        'init_type_obj': 'create_dtype_obj({use_generic})',
        'init_type_1darray': ('create_dtype_1darray(\"{subtype}\", '
                              '{precision}, {length}, \"{units}\", '
                              '{use_generic})'),
        'init_type_ndarray': ('create_dtype_ndarray(\"{subtype}\", '
                              '{precision}, {ndim}, {shape}, '
                              '\"{units}\", {use_generic})'),
        'init_type_ndarray_arr': ('create_dtype_ndarray(\"{subtype}\", '
                                  '{precision}, {ndim}, {shape}, '
                                  '\"{units}\", {use_generic})'),
        'init_type_scalar': ('create_dtype_scalar(\"{subtype}\", '
                             '{precision}, \"{units}\", '
                             '{use_generic})'),
        'init_type_default': ('create_dtype_default(\"{type}\", '
                              '{use_generic})'),
        'init_type_pyobj': ('create_dtype_pyobj(\"{type}\", '
                            '{use_generic})'),
        'init_type_empty': ('create_dtype_empty({use_generic})'),
        'init_type_schema': ('create_dtype_schema({use_generic})'),
        'copy_array': '{name} = yggarr(copy_generic(ygggeneric({value})))',
        'copy_object': '{name} = yggmap(copy_generic(ygggeneric({value})))',
        'copy_schema': '{name} = yggschema(copy_generic(ygggeneric({value})))',
        'copy_ply': '{name} = copy_ply({value})',
        'copy_obj': '{name} = copy_obj({value})',
        'copy_class': '{name} = yggpyfunc(copy_python(yggpython({value})))',
        'copy_function': '{name} = yggpyfunc(copy_python(yggpython({value})))',
        'copy_instance': '{name} = yggpyinst(copy_generic(ygggeneric({value})))',
        'copy_generic': '{name} = copy_generic({value})',
        'copy_any': '{name} = copy_generic({value})',
        'free_array': 'call free_generic(ygggeneric({variable}))',
        'free_object': 'call free_generic(ygggeneric({variable}))',
        'free_schema': 'call free_generic(ygggeneric({variable}))',
        'free_ply': 'call free_ply({variable})',
        'free_obj': 'call free_obj({variable})',
        'free_class': 'call free_python(yggpython({variable}))',
        'free_function': 'call free_python(yggpython({variable}))',
        'free_instance': 'call free_generic(ygggeneric({variable}))',
        'free_any': 'call free_generic({variable})',
        'print_generic': 'write(*, *) {object}',
        'print': 'write(*, \'(\"{message}\")\')',
        'fprintf': 'write(*, \'(\"{message}\")\') {variables}',
        'print_array': 'call display_generic(ygggeneric({object}))',
        'print_object': 'call display_generic(ygggeneric({object}))',
        'print_schema': 'call display_generic(ygggeneric({object}))',
        'print_ply': 'call display_ply({object})',
        'print_obj': 'call display_obj({object})',
        'print_class': 'call display_python(yggpython({object}))',
        'print_function': 'call display_python(yggpython({object}))',
        'print_instance': 'call display_generic(ygggeneric({object}))',
        'print_any': 'call display_generic({object})',
        'assign': '{name} = {value}',
        'comment': '!',
        'true': '.true.',
        'false': '.false.',
        'null': 'c_null_ptr',
        'not': '.not.',
        'and': '.and.',
        'or': '.or.',
        'indent': 3 * ' ',
        'quote': "'",
        'error': ("write(*, \'(\"{error_msg}\")\')\n"
                  "call exit(-1)"),
        'continuation_before': '&',
        'continuation_after': '     &',
        'block_end': 'END',
        'if_begin': 'IF ({cond}) THEN',
        'if_elif': 'ELSE IF ({cond}) THEN',
        'if_else': 'ELSE',
        'if_end': 'END IF',
        'for_begin': 'DO {iter_var} = {iter_begin}, {iter_end}',
        'for_end': 'END DO',
        'while_begin': 'DO WHILE ({cond})',
        'while_end': 'END DO',
        'break': 'EXIT',
        'exec_begin': 'PROGRAM main\n   use iso_c_binding',
        'exec_end': '   call exit(0)\nEND PROGRAM main',
        'free': 'DEALLOCATE({variable})',
        'function_def_begin': (
            'FUNCTION {function_name}({input_var}) '
            'result({output_var})'),
        'function_def_end': 'END FUNCTION {function_name}',
        'subroutine_def_begin': (
            'SUBROUTINE {function_name}({input_var}) '),
        'subroutine_def_end': 'END SUBROUTINE {function_name}',
        'function_call_noout': 'call {function_name}({input_var})',
        'function_def_regex': (
            r'(?P<procedure_type>(?i:(?:subroutine)|(?:function)))\s+'
            r'{function_name}\s*\((?P<inputs>(?:[^\(]*?))\)\s*'
            r'(?:result\s*\((?P<flag_var>.+)\))?\s*\n'
            r'(?P<preamble>(?:[^:]*?\n)*?)'
            r'(?P<definitions>(?:(?:(?: )|(?:.))+\s*::\s*(?:.+)\n)+)'
            r'(?P<body>(?:.*?\n?)*?)'
            r'(?i:end\s+(?P=procedure_type))\s+{function_name}'),
        'definition_regex': (
            r'\s*(?P<type>(?:(?: )|(?:.))+)\s*::\s*(?P<name>.+)'
            r'(?:\s*=\s*(?P<value>.+))?\n'),
        'inputs_def_regex': (
            r'\s*(?P<name>.+?)\s*(?:,|$)(?:\n)?'),
        'outputs_def_regex': (
            r'\s*(?P<name>.+?)\s*(?:,|$)(?:\n)?')
    }
    outputs_in_inputs = True
    include_channel_obj = True
    is_typed = True
    types_in_funcdef = False
    interface_inside_exec = True
    import_after_exec = True
    declare_functions_as_var = True
    zero_based = False
    max_line_width = 72
    
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

    def compile_model(self, **kwargs):
        r"""Compile model executable(s).

        Args:
            **kwargs: Keyword arguments are passed to the parent class's
            method.

        Returns:
            str: Compiled model file path.

        """
        kwargs.setdefault('libraries', [])
        kwargs['libraries'].append('c++')
        return super(FortranModelDriver, self).compile_model(**kwargs)

    @classmethod
    def get_internal_suffix(cls, commtype=None):
        r"""Determine the suffix that should be used for internal libraries.

        Args:
            commtype (str, optional): If provided, this is the communication
                type that should be used for the model. If None, the
                default comm is used.

        Returns:
            str: Suffix that should be added to internal libraries to
                differentiate between different dependencies.

        """
        out = super(FortranModelDriver, cls).get_internal_suffix(
            commtype=commtype)
        if commtype is None:
            commtype = tools.get_default_comm()
        out += '_%s' % commtype[:3].lower()
        return out

    @classmethod
    def get_native_type(cls, **kwargs):
        r"""Get the native type.

        Args:
            type (str, optional): Name of |yggdrasil| extended JSON
                type or JSONSchema dictionary defining a datatype.
            **kwargs: Additional keyword arguments may be used in determining
                the precise declaration that should be used.

        Returns:
            str: The native type.

        """
        out = super(FortranModelDriver, cls).get_native_type(**kwargs)
        if not ((out == '*') or ('X' in out)):
            if out.startswith('ygg'):
                out = 'type(%s)' % out
            return out
        from yggdrasil.metaschema.datatypes import get_type_class
        json_type = kwargs.get('datatype', kwargs.get('type', 'bytes'))
        if isinstance(json_type, str):
            json_type = {'type': json_type}
        if 'type' in kwargs:
            json_type.update(kwargs)
        assert(isinstance(json_type, dict))
        json_type = get_type_class(json_type['type']).normalize_definition(
            json_type)
        if out == '*':
            dim_str = ''
            if json_type['type'] == '1darray':
                if 'length' in json_type:
                    dim_str = ', dimension(%s)' % str(json_type['length'])
            elif json_type['type'] == 'ndarray':
                if 'shape' in json_type:
                    dim_str = ', dimension(%s)' % ','.join(
                        [str(x) for x in json_type['shape']])
            json_subtype = copy.deepcopy(json_type)
            json_subtype['type'] = json_subtype.pop('subtype')
            out = cls.get_native_type(datatype=json_subtype) + dim_str
            if not dim_str:
                json_subtype['type'] = out.split('(')[0]
                if json_subtype['type'] == 'character':
                    json_subtype['precision'] = ''
                else:
                    json_subtype['precision'] = int(json_subtype['precision'] / 8)
                out = 'type(%s)' % cls.get_native_type(
                    type=('%s_pointer' % json_type['type'])).format(
                        **json_subtype)
        elif 'X' in out:
            precision = json_type['precision']
            out = out.replace('X', str(int(precision / 8)))
        return out
        
    @classmethod
    def get_json_type(cls, native_type):
        r"""Get the JSON type from the native language type.

        Args:
            native_type (str): The native language type.

        Returns:
            str, dict: The JSON type.

        """
        out = {}
        regex_var = (r'(type\()?(?P<type>[^,\(]+)(?(1)(?:\)))'
                     r'(?:\s*\(\s*'
                     r'(?:kind\s*=\s*(?P<precision>\d*))?,?'
                     r'(?:len\s*=\s*(?P<length>\d*))?'
                     r'\))?'
                     r'(?:\s*,\s*dimension\((?P<shape>.*?)\))?'
                     r'(?:\s*,\s*(?P<pointer>pointer))?'
                     r'(?:\s*,\s*(?P<allocatable>allocatable))?'
                     r'(?:\s*,\s*(?P<parameter>parameter))?'
                     r'(?:\s*,\s*intent\((?P<intent>.*?)\))?')
        grp = re.fullmatch(regex_var, native_type).groupdict()
        if grp['type'].endswith(('_1d', '_nd')):
            regex_nd = r'(?P<type>.*?)(?P<precision>\d+)?_(?P<ndim>(?:1)|(?:n))d'
            grp = re.fullmatch(regex_nd, grp['type']).groupdict()
            if grp['ndim'] == '1':
                grp['shape'] = ':'
            else:
                grp['shape'] = ':,:'
        if grp.get('precision', False):
            out['precision'] = 8 * int(grp['precision'])
            grp['type'] += '(kind = X)'
        if grp['type'] == 'character':
            out['type'] = 'bytes'
            out['precision'] = grp.get('length', 0)
        else:
            out['type'] = super(FortranModelDriver, cls).get_json_type(grp['type'])
        if grp.get('shape', False):
            shape = grp['shape'].split(',')
            ndim = len(shape)
            out['subtype'] = out['type']
            if ndim == 1:
                out['type'] = '1darray'
                if shape[0] != ':':
                    out['length'] = int(shape[0])
            else:
                out['type'] = 'ndarray'
                if shape[0] != ':':
                    out['shape'] = [int(i) for i in shape]
        if out['type'] in _valid_types:
            out['subtype'] = out['type']
            out['type'] = 'scalar'
        return out

    @classmethod
    def parse_function_definition(cls, model_file, model_function, **kwargs):
        r"""Get information about the inputs & outputs to a model from its
        defintition if possible.

        Args:
            model_file (str): Full path to the file containing the model
                function's declaration.
            model_function (str): Name of the model function.
            **kwargs: Additional keyword arugments are passed to the parent
                class's method.

        Returns:
            dict: Parameters extracted from the function definitions.

        """
        out = super(FortranModelDriver, cls).parse_function_definition(
            model_file, model_function, **kwargs)
        var_type_map = {}
        for x in re.finditer(cls.function_param['definition_regex'],
                             out['definitions']):
            x_vars = [v.strip() for v in
                      x.groupdict()['name'].split(',')]
            for v in x_vars:
                var_type_map[v] = x.groupdict()['type']
        for x in out.get('inputs', []) + out.get('outputs', []):
            x['native_type'] = var_type_map[x['name']].strip()
            x['datatype'] = cls.get_json_type(x['native_type'])
        return out

    @classmethod
    def update_io_from_function(cls, model_file, model_function, **kwargs):
        r"""Update inputs/outputs from the function definition.

        Args:
            model_file (str): Full path to the file containing the model
                function's declaration.
            model_function (str): Name of the model function.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            dict, None: Flag variable used by the model. If None, the
                model does not use a flag variable.

        """
        out = super(FortranModelDriver, cls).update_io_from_function(
            model_file, model_function, **kwargs)
        for x in kwargs.get('inputs', []) + kwargs.get('outputs', []):
            if x['datatype']['type'] == 'array':
                nvars_items = len(x['datatype'].get('items', []))
                nvars = sum([(not ix.get('is_length_var', False))
                             for ix in x['vars']])
                if nvars_items == nvars:
                    x['use_generic'] = False
                else:
                    x['use_generic'] = True
        return out
        
    @classmethod
    def prepare_variables(cls, vars_list, for_yggdrasil=False, **kwargs):
        r"""Concatenate a set of input variables such that it can be passed as a
        single string to the function_call parameter.

        Args:
            vars_list (list): List of variable dictionaries containing info
                (e.g. names) that should be used to prepare a string representing
                input/output to/from a function call.
            for_yggdrasil (bool, optional): If True, the variables will be
                prepared in the formated expected by calls to yggdarsil
                send/recv methods. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            str: Concatentated variables list.

        """
        new_vars_list = vars_list
        if for_yggdrasil:
            new_vars_list = []
            for v in vars_list:
                if isinstance(v, dict):
                    v = dict(v, name=('yggarg(%s)' % v['name']))
                else:
                    v = 'yggarg(%s)' % v
                new_vars_list.append(v)
        out = super(FortranModelDriver, cls).prepare_variables(
            new_vars_list, for_yggdrasil=for_yggdrasil, **kwargs)
        if for_yggdrasil and (len(new_vars_list) > 1):
            return '[%s]' % out
        return out
        
    @classmethod
    def write_executable(cls, lines, **kwargs):
        r"""Return the lines required to complete a program that will run
        the provided lines.

        Args:
            lines (list): Lines of code to be wrapped as an executable.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            lines: Lines of code wrapping the provided lines with the
                necessary code to run it as an executable (e.g. C/C++'s main).

        """
        if 'implicit none' not in lines:
            for i, line in enumerate(lines):
                if not line.lstrip().lower().startswith('use'):
                    lines.insert(i, 'implicit none')
                    break
        out = super(FortranModelDriver, cls).write_executable(
            lines, **kwargs)
        return out
        
    @classmethod
    def write_function_def(cls, function_name, **kwargs):
        r"""Write a function definition.

        Args:
            function_name (str): Name fo the function being defined.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Lines completing the function call.

        """
        if (((not kwargs.get('outputs_in_inputs', False))
             and (len(kwargs.get('outputs', [])) == 0))):
            kwargs.setdefault(
                'function_keys',
                ('subroutine_def_begin', 'subroutine_def_end'))
        return super(FortranModelDriver, cls).write_function_def(
            function_name, **kwargs)

    @classmethod
    def escape_quotes(cls, x):
        r"""Escape quotes in a string.

        Args:
           x (str): String to escape quotes in.

        Returns:
           str: x with escaped quotes.

        """
        out = x.replace('"', '""')
        out = out.replace("'", "''")
        return out

    @classmethod
    def split_line(cls, line, length=None):
        r"""Split a line as close to (or before) a given character as
        possible.

        Args:
            line (str): Line to split.
            length (int, optional): Maximum length of split lines. Defaults
                to cls.max_line_width if not provided.

        Returns:
            list: Set of lines resulting from spliting the provided line.

        """
        if line.lstrip().lower().startswith("include"):
            return [line]
        return super(FortranModelDriver, cls).split_line(
            line, length=length)

    @classmethod
    def allows_realloc(cls, var):
        r"""Determine if a variable allows the receive call to perform
        realloc.

        Args:
            var (dict): Dictionary of variable properties.

        Returns:
            bool: True if the variable allows realloc, False otherwise.

        """
        if isinstance(var, dict):
            datatype = var.get('datatype', var)
            if ('shape' in datatype) or ('length' in datatype):
                return False
            if ((datatype.get('subtype', datatype.get('type', None))
                 in ['bytes', 'unicode']) and ('precision' in datatype)):
                return False
        return True
        
    @classmethod
    def write_model_recv(cls, channel, recv_var, **kwargs):
        r"""Write a model receive call include checking the return flag.

        Args:
            channel (str): Name of variable that the channel being received from
                was stored in.
            recv_var (dict, list): Information of one or more variables that
                receieved information should be stored in.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Lines required to carry out a receive call in this language.

        """
        recv_var_str = recv_var
        if not isinstance(recv_var, str):
            recv_var_par = cls.channels2vars(recv_var)
            allows_realloc = [cls.allows_realloc(v)
                              for v in recv_var_par]
            if all(allows_realloc):
                kwargs['alt_recv_function'] = cls.function_param['recv_heap']
            else:
                kwargs['alt_recv_function'] = cls.function_param['recv_stack']
            recv_var_str = cls.prepare_output_variables(
                recv_var_par, in_inputs=cls.outputs_in_inputs,
                for_yggdrasil=True)
        return super(FortranModelDriver, cls).write_model_recv(
            channel, recv_var_str, **kwargs)

    @classmethod
    def write_print_var(cls, var, **kwargs):
        r"""Get the lines necessary to print a variable in this language.

        Args:
            var (dict): Variable information.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Lines printing the specified variable.

        """
        if isinstance(var, dict):
            datatype = var.get('datatype', var)
            typename = datatype.get('type', None)
            if ((((typename == '1darray') and ('length' not in datatype))
                 or ((typename == 'ndarray') and ('shape' not in datatype)))):
                return []
        return super(FortranModelDriver, cls).write_print_var(
            var, **kwargs)

    @classmethod
    def write_type_def(cls, name, datatype, **kwargs):
        r"""Get lines declaring the data type within the language.

        Args:
            name (str): Name of variable that definition should be stored in.
            datatype (dict): Type definition.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Lines required to define a type definition.

        """
        if datatype['type'] == 'array':
            datatype.setdefault('items', [])
        elif datatype['type'] == 'object':
            datatype.setdefault('properties', {})
        out = super(FortranModelDriver, cls).write_type_def(
            name, datatype, **kwargs)
        return out
    
    @classmethod
    def write_type_decl(cls, name, datatype, **kwargs):
        r"""Get lines declaring the datatype within the language.

        Args:
            name (str): Name of variable that should be declared.
            datatype (dict): Type definition.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Lines required to define a type declaration.

        """
        if datatype['type'] == 'array':
            datatype.setdefault('items', [])
        elif datatype['type'] == 'object':
            datatype.setdefault('properties', {})
        out = super(FortranModelDriver, cls).write_type_decl(
            name, datatype, **kwargs)
        return out
