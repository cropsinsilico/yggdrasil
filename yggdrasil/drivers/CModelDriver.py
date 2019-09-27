import os
import re
import copy
import shutil
import subprocess
import numpy as np
from collections import OrderedDict
from yggdrasil import platform, tools, backwards
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, ArchiverBase)
from yggdrasil.languages import get_language_dir
from yggdrasil.config import ygg_cfg


_default_internal_libtype = 'object'
# if platform._is_win:  # pragma: windows
#     _default_internal_libtype = 'static'


def get_OSX_SYSROOT():
    r"""Determin the path to the OSX SDK.

    Returns:
        str: Full path to the SDK directory if one is located. None
            otherwise.

    """
    fname = None
    if platform._is_mac:
        try:
            xcode_dir = backwards.as_str(subprocess.check_output(
                'echo "$(xcode-select -p)"', shell=True).strip())
        except BaseException:  # pragma: debug
            xcode_dir = None
        fname_try = []
        cfg_sdkroot = ygg_cfg.get('c', 'macos_sdkroot', None)
        if cfg_sdkroot:
            fname_try.append(cfg_sdkroot)
        if xcode_dir is not None:
            fname_base = os.path.join(xcode_dir, 'Platforms',
                                      'MacOSX.platform', 'Developer',
                                      'SDKs', 'MacOSX%s.sdk')
            fname_try += [
                fname_base % os.environ.get('MACOSX_DEPLOYMENT_TARGET', ''),
                fname_base % '',
                os.path.join(xcode_dir, 'SDKs', 'MacOSX.sdk')]
        if os.environ.get('SDKROOT', False):
            fname_try.insert(0, os.environ['SDKROOT'])
        for fcheck in fname_try:
            if os.path.isdir(fcheck):
                fname = fcheck
                break
    return fname


_osx_sysroot = get_OSX_SYSROOT()


class CCompilerBase(CompilerBase):
    r"""Base class for C compilers."""
    languages = ['c']
    default_executable_env = 'CC'
    default_flags_env = 'CFLAGS'
    default_flags = ['-g', '-Wall']
    # GCC & CLANG have similar call patterns
    linker_attributes = {'default_flags_env': 'LDFLAGS',
                         'search_path_env': ['LIBRARY_PATH', 'LD_LIBRARY_PATH']}
    search_path_env = ['C_INCLUDE_PATH']
    search_path_flags = ['-E', '-v', '-xc', '/dev/null']
    search_regex_begin = '#include "..." search starts here:'
    search_regex_end = 'End of search list.'
    search_regex = [r'(?:#include <...> search starts here:)|'
                    r'(?: ([^\n]+?)(?: \(framework directory\))?)\n']

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        if platform._is_mac:
            cls.linker_attributes = dict(cls.linker_attributes,
                                         search_path_flags=['-Xlinker', '-v'],
                                         search_regex=[r'\t([^\t\n]+)\n'],
                                         search_regex_begin='Library search paths:')
        elif platform._is_linux:
            cls.linker_attributes = dict(cls.linker_attributes,
                                         search_path_flags=['-Xlinker', '--verbose'],
                                         search_regex=[r'SEARCH_DIR\("=([^"]+)"\);'])
        CompilerBase.before_registration(cls)

    @classmethod
    def set_env(cls, *args, **kwargs):
        r"""Set environment variables required for compilation.

        Args:
            *args: Arguments are passed to the parent class's method.
            **kwargs: Keyword arguments  are passed to the parent class's
                method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CCompilerBase, cls).set_env(*args, **kwargs)
        if _osx_sysroot is not None:
            out['CONDA_BUILD_SYSROOT'] = _osx_sysroot
            out['SDKROOT'] = _osx_sysroot
            grp = re.search(r'MacOSX(?P<target>[0-9]+\.[0-9]+)',
                            _osx_sysroot).groupdict()
            out['MACOSX_DEPLOYMENT_TARGET'] = grp['target']
        return out
    
    @classmethod
    def call(cls, args, **kwargs):
        r"""Call the compiler with the provided arguments. For |yggdrasil| C
        models will always be linked using the C++ linker since some parts of
        the interface library are written in C++."""
        if not kwargs.get('dont_link', False):
            kwargs.setdefault('linker_language', 'c++')
        return super(CCompilerBase, cls).call(args, **kwargs)
    

class GCCCompiler(CCompilerBase):
    r"""Interface class for gcc compiler/linker."""
    toolname = 'gcc'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_archiver = 'ar'


class ClangCompiler(CCompilerBase):
    r"""clang compiler on Apple Mac OS."""
    toolname = 'clang'
    platforms = ['MacOS']
    default_archiver = 'libtool'
    flag_options = OrderedDict(list(CCompilerBase.flag_options.items())
                               + [('sysroot', '--sysroot'),
                                  ('isysroot', {'key': '-isysroot',
                                                'prepend': True}),
                                  ('mmacosx-version-min',
                                   '-mmacosx-version-min=%s')])


class MSVCCompiler(CCompilerBase):
    r"""Microsoft Visual Studio C Compiler."""
    toolname = 'cl'
    languages = ['c', 'c++']
    platforms = ['Windows']
    default_flags_env = ['CFLAGS', 'CXXFLAGS']
    # TODO: Currently everything compiled as C++ on windows to allow use
    # of complex types. Use '/TC' instead of '/TP' for strictly C
    default_flags = ['/W4',      # Display all errors
                     '/Zi',      # Symbolic debug in .pdb (implies debug)
                     # '/MTd',     # Use LIBCMTD.lib to create multithreaded .exe
                     # '/Z7',      # Symbolic debug in .obj (implies debug)
                     "/EHsc",    # Catch C++ exceptions only (C don't throw C++)
                     '/TP',      # Treat all files as C++
                     "/nologo",  # Suppress startup banner
                     # Don't show errors from using scanf, strcpy, etc.
                     "-D_CRT_SECURE_NO_WARNINGS"]
    output_key = '/Fo%s'
    output_first = True
    default_linker = 'LINK'
    default_archiver = 'LIB'
    linker_switch = '/link'
    search_path_env = 'INCLUDE'
    search_path_flags = None
    version_flags = []
    product_exts = ['.dir', '.ilk', '.pdb', '.sln', '.vcxproj', '.vcxproj.filters']
    combine_with_linker = True  # Must be explicit; linker is separate .exe
    linker_attributes = dict(GCCCompiler.linker_attributes,
                             default_executable=None,
                             default_flags_env=None,
                             output_key='/OUT:%s',
                             output_first=True,
                             output_first_library=False,
                             flag_options=OrderedDict(
                                 [('library_libs', ''),
                                  ('library_dirs', '/LIBPATH:%s')]),
                             shared_library_flag='/DLL',
                             search_path_env='LIB',
                             search_path_flags=None)
    
    @classmethod
    def language_version(cls, **kwargs):  # pragma: windows
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.call.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        out = cls.call(cls.version_flags, skip_flags=True,
                       allow_error=True, **kwargs)
        if 'Copyright' not in out:  # pragma: debug
            raise RuntimeError("Version call failed: %s" % out)
        return out.split('Copyright')[0]

    
# C Archivers
class ARArchiver(ArchiverBase):
    r"""Archiver class for ar tool."""
    toolname = 'ar'
    languages = ['c', 'c++']
    default_executable_env = 'AR'
    default_flags_env = None
    static_library_flag = 'rcs'
    output_key = ''
    output_first_library = True


class LibtoolArchiver(ArchiverBase):
    r"""Archiver class for libtool tool."""
    toolname = 'libtool'
    languages = ['c', 'c++']
    default_executable_env = 'LIBTOOL'
    static_library_flag = '-static'  # This is the default
    

class MSVCArchiver(ArchiverBase):
    r"""Microsoft Visual Studio C Archiver."""
    toolname = 'LIB'
    languages = ['c', 'c++']
    platforms = ['Windows']
    static_library_flag = None
    output_key = '/OUT:%s'
    

_top_lang_dir = get_language_dir('c')
_incl_interface = _top_lang_dir
_incl_seri = os.path.join(_top_lang_dir, 'serialize')
_incl_comm = os.path.join(_top_lang_dir, 'communication')


class CModelDriver(CompiledModelDriver):
    r"""Class for running C models."""

    _schema_subtype_description = ('Model is written in C.')
    language = 'c'
    language_ext = ['.c', '.h']
    interface_library = 'ygg'
    supported_comms = ['ipc', 'zmq']
    supported_comm_options = {
        'ipc': {'platforms': ['MacOS', 'Linux']},
        'zmq': {'libraries': ['zmq', 'czmq']}}
    interface_dependencies = ['rapidjson']
    interface_directories = [_incl_interface]
    external_libraries = {
        'rapidjson': {'include': os.path.join(os.path.dirname(tools.__file__),
                                              'rapidjson', 'include',
                                              'rapidjson', 'rapidjson.h'),
                      'libtype': 'header_only',
                      'language': 'c'},
        'zmq': {'include': 'zmq.h',
                'libtype': 'shared',
                'language': 'c'},
        'czmq': {'include': 'czmq.h',
                 'libtype': 'shared',
                 'language': 'c'}}
    internal_libraries = {
        'ygg': {'source': os.path.join(_incl_interface, 'YggInterface.c'),
                'linker_language': 'c++',  # Some dependencies are C++
                'internal_dependencies': ['datatypes', 'regex'],
                'external_dependencies': ['rapidjson'],
                'include_dirs': [_incl_comm, _incl_seri],
                'compiler_flags': []},
        'regex_win32': {'source': 'regex_win32.cpp',
                        'directory': os.path.join(_top_lang_dir, 'regex'),
                        'language': 'c++',
                        'libtype': _default_internal_libtype,
                        'internal_dependencies': [],
                        'external_dependencies': []},
        'regex_posix': {'source': 'regex_posix.h',
                        'directory': os.path.join(_top_lang_dir, 'regex'),
                        'language': 'c',
                        'libtype': 'header_only',
                        'internal_dependencies': [],
                        'external_dependencies': []},
        'datatypes': {'directory': os.path.join(_top_lang_dir, 'datatypes'),
                      'language': 'c++',
                      'libtype': _default_internal_libtype,
                      'internal_dependencies': ['regex'],
                      'external_dependencies': ['rapidjson'],
                      'include_dirs': []}}
    type_map = {
        'int': 'intX_t',
        'float': 'double',
        'string': 'char*',
        'array': 'vector_t',
        'object': 'map_t',
        'boolean': 'bool',
        'null': 'NULL',
        'uint': 'uintX_t',
        'complex': 'complex_X',
        'bytes': 'char*',
        'unicode': 'char*',
        '1darray': '*',
        'ndarray': '*',
        'ply': 'ply_t',
        'obj': 'obj_t',
        'schema': 'map_t',
        'flag': 'int'}
    function_param = {
        'import': '#include \"{filename}\"',
        'index': '{variable}[{index}]',
        'interface': '#include \"{interface_library}\"',
        'input': ('yggInput_t {channel} = yggInputType('
                  '\"{channel_name}\", {channel_type});'),
        'output': ('yggOutput_t {channel} = yggOutputType('
                   '\"{channel_name}\", {channel_type});'),
        'recv_function': 'yggRecvRealloc',
        'send_function': 'yggSend',
        'not_flag_cond': '{flag_var} < 0',
        'flag_cond': '{flag_var} >= 0',
        'declare': '{type_name} {variable};',
        'define': '{variable} = {value};',
        'assign': '{name} = {value};',
        'comment': '//',
        'true': '1',
        'not': '!',
        'and': '&&',
        'indent': 2 * ' ',
        'quote': '\"',
        'print': 'printf(\"{message}\\n\");',
        'fprintf': 'printf(\"{message}\\n\", {variables});',
        'error': 'printf(\"{error_msg}\\n\"); return -1;',
        'block_end': '}',
        'if_begin': 'if ({cond}) {{',
        'if_elif': '}} else if ({cond}) {{',
        'if_else': '}} else {{',
        'for_begin': ('for ({iter_var} = {iter_begin}; {iter_var} < {iter_end}; '
                      '{iter_var}++) {{'),
        'while_begin': 'while ({cond}) {{',
        'break': 'break;',
        'exec_begin': 'int main() {',
        'exec_end': '  return 0;\n}',
        'exec_prefix': '#include <stdbool.h>',
        'free': 'if ({variable} != NULL) free({variable});',
        'function_def_regex': (r'(?P<flag_type>.+?)\s*{function_name}\s*'
                               r'\((?P<inputs>(?:[^)])*?)\)\s*\{{'),
        'inputs_def_regex': (r'\s*(?P<native_type>(?:[^\s\*])+(\s+)?'
                             r'(?P<ptr>\*+)?)(?(ptr)(?(1)(?:\s*)|(?:\s+)))'
                             r'(?P<name>.+?)\s*(?:,|$)(?:\n)?'),
        'outputs_def_regex': (r'\s*(?P<native_type>(?:[^\s\*])+(\s+)?'
                              r'(?P<ptr>\*+)?)(?(ptr)(?(1)(?:\s*)|(?:\s+)))'
                              r'(?P<name>.+?)\s*(?:,|$)(?:\n)?')}
    outputs_in_inputs = True
    include_channel_obj = True
    is_typed = True

    @staticmethod
    def after_registration(cls):
        r"""Operations that should be performed to modify class attributes after
        registration."""
        if cls.default_compiler is None:
            if platform._is_linux:
                cls.default_compiler = 'gcc'
            elif platform._is_mac:
                cls.default_compiler = 'clang'
            elif platform._is_win:  # pragma: windows
                cls.default_compiler = 'cl'
        CompiledModelDriver.after_registration(cls)
        archiver = cls.get_tool('archiver')
        linker = cls.get_tool('linker')
        for x in ['zmq', 'czmq']:
            if x in cls.external_libraries:
                if platform._is_win:  # pragma: windows
                    cls.external_libraries[x]['libtype'] = 'static'
                libtype = cls.external_libraries[x]['libtype']
                if libtype == 'static':  # pragma: debug
                    tool = archiver
                    kwargs = {}
                else:
                    tool = linker
                    kwargs = {'build_library': True}
                cls.external_libraries[x][libtype] = tool.get_output_file(
                    x, **kwargs)
        # Platform specific regex internal library
        if platform._is_win:  # pragma: windows
            regex_lib = cls.internal_libraries['regex_win32']
        else:
            regex_lib = cls.internal_libraries['regex_posix']
        cls.internal_libraries['regex'] = regex_lib
        # Platform specific internal library options
        cls.internal_libraries['ygg']['include_dirs'] += [_top_lang_dir]
        if platform._is_win:  # pragma: windows
            stdint_win = os.path.join(_top_lang_dir, 'windows_stdint.h')
            assert(os.path.isfile(stdint_win))
            shutil.copy(stdint_win, os.path.join(_top_lang_dir, 'stdint.h'))
            cls.internal_libraries['datatypes']['include_dirs'] += [_top_lang_dir]
        if platform._is_linux:
            for x in ['ygg', 'datatypes']:
                if 'compiler_flags' not in cls.internal_libraries[x]:
                    cls.internal_libraries[x]['compiler_flags'] = []
                if '-fPIC' not in cls.internal_libraries[x]['compiler_flags']:
                    cls.internal_libraries[x]['compiler_flags'].append('-fPIC')
        
    @classmethod
    def update_config_argparser(cls, parser):
        r"""Add arguments for configuration options specific to this
        language.

        Args:
            parser (argparse.ArgumentParser): Parser to add arguments to.

        """
        super(CModelDriver, cls).update_config_argparser(parser)
        if platform._is_mac and (cls.language == 'c'):
            parser.add_argument('--macos-sdkroot', '--sdkroot',
                                help=('The full path to the MacOS SDK '
                                      'that should be used.'))
        
    @classmethod
    def configure(cls, cfg, macos_sdkroot=None):
        r"""Add configuration options for this language. This includes locating
        any required external libraries and setting option defaults.

        Args:
            cfg (YggConfigParser): Config class that options should be set for.
            macos_sdkroot (str, optional): Full path to the root directory for
                the MacOS SDK that should be used. Defaults to None and is
                ignored.

        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        # Call __func__ to avoid direct invoking of class which dosn't exist
        # in after_registration where this is called
        out = CompiledModelDriver.configure.__func__(cls, cfg)
        # Change configuration to be directory containing include files
        rjlib = cfg.get(cls._language, 'rapidjson_include', None)
        if (rjlib is not None) and os.path.isfile(rjlib):
            cfg.set(cls._language, 'rapidjson_include',
                    os.path.dirname(os.path.dirname(rjlib)))
        if macos_sdkroot is not None:
            if not os.path.isdir(macos_sdkroot):  # pragma: debug
                raise ValueError("Path to MacOS SDK root directory "
                                 "does not exist: %s." % macos_sdkroot)
            cfg.set(cls._language, 'macos_sdkroot', macos_sdkroot)
        return out

    @classmethod
    def call_linker(cls, obj, language=None, **kwargs):
        r"""Link several object files to create an executable or library (shared
        or static), checking for errors.

        Args:
            obj (list): Object files that should be linked.
            language (str, optional): Language that should be used to link
                the files. Defaults to None and the language of the current
                driver is used.
            **kwargs: Additional keyword arguments are passed to run_executable.

        Returns:
            str: Full path to compiled source.

        """
        if (((cls.language == 'c') and (language is None)
             and kwargs.get('for_model', False)
             and (not kwargs.get('skip_interface_flags', False)))):
            language = 'c++'
            kwargs.update(cls.update_linker_kwargs(**kwargs))
            kwargs['skip_interface_flags'] = True
        return super(CModelDriver, cls).call_linker(obj, language=language,
                                                    **kwargs)
        
    @classmethod
    def update_ld_library_path(cls, env, paths_to_add=None, add_to_front=False):
        r"""Update provided dictionary of environment variables so that
        LD_LIBRARY_PATH includes the interface directory containing the interface
        libraries.

        Args:
            env (dict): Dictionary of enviroment variables to be updated.
            paths_to_add (list, optional): Paths that should be added. If not
                provided, defaults to [cls.get_language_dir()].
            add_to_front (bool, optional): If True, new paths are added to the
                front, rather than the end. Defaults to False.

        Returns:
            dict: Updated dictionary of environment variables.

        """
        if paths_to_add is None:
            paths_to_add = [cls.get_language_dir()]
        if platform._is_linux:
            path_list = []
            prev_path = env.pop('LD_LIBRARY_PATH', '')
            if prev_path:
                path_list.append(prev_path)
            for x in paths_to_add:
                if x not in prev_path:
                    if add_to_front:
                        path_list.insert(0, x)
                    else:
                        path_list.append(x)
            if path_list:
                env['LD_LIBRARY_PATH'] = os.pathsep.join(path_list)
        return env

    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CModelDriver, self).set_env(**kwargs)
        out = self.update_ld_library_path(out)
        return out
    
    @classmethod
    def update_io_from_function(cls, model_file, model_function,
                                inputs=[], outputs=[]):
        r"""Update inputs/outputs from the function definition.

        Args:
            model_file (str): Full path to the file containing the model
                function's declaration.
            model_function (str): Name of the model function.
            inputs (list, optional): List of model inputs including types.
                Defaults to [].
            outputs (list, optional): List of model outputs including types.
                Defaults to [].

        """
        super(CModelDriver, cls).update_io_from_function(
            model_file, model_function, inputs=inputs, outputs=outputs)
        for x in inputs:
            for v in x['vars']:
                if (((v['native_type'] != 'char*')
                     and ('Realloc' in cls.function_param['recv_function']))):
                    v['allow_realloc'] = True
        
    @classmethod
    def input2output(cls, var):
        r"""Perform conversion necessary to turn a variable extracted from a
        function definition from an input to an output.

        Args:
            var (dict): Variable definition.

        Returns:
            dict: Updated variable definition.

        """
        out = super(CModelDriver, cls).input2output(var)
        if out['native_type'] != out.get('native_type_cast', out['native_type']):
            out['native_type'] = out['native_type_cast']
            del out['native_type_cast']
        if out.get('ptr', ''):
            assert(out['native_type'].endswith('*'))
            out['ptr'] = out['ptr'][:-1]
            out['native_type'] = out['native_type'][:-1]
            out['datatype'] = cls.get_json_type(out['native_type'])
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
        out = super(CModelDriver, cls).get_native_type(**kwargs)
        if not ((out == '*') or ('X' in out) or (out == 'double')):
            return out
        from yggdrasil.metaschema.datatypes import get_type_class
        json_type = kwargs.get('datatype', kwargs.get('type', 'bytes'))
        if isinstance(json_type, str):
            json_type = {'type': json_type}
        assert(isinstance(json_type, dict))
        json_type = get_type_class(json_type['type']).normalize_definition(
            json_type)
        if out == '*':
            json_subtype = copy.deepcopy(json_type)
            json_subtype['type'] = json_subtype.pop('subtype')
            out = cls.get_native_type(datatype=json_subtype) + '*'
        elif 'X' in out:
            precision = json_type['precision']
            out = out.replace('X', str(precision))
        elif out == 'double':
            if json_type['precision'] == 32:
                out = 'float'
        return out
        
    @classmethod
    def get_json_type(cls, native_type=None):
        r"""Get the JSON type from the native language type.

        Args:
            native_type (str, optional): The native language type. Defaults
                to None.

        Returns:
            str, dict: The JSON type.

        """
        if native_type is None:
            return super(CModelDriver, cls).get_json_type(native_type)
        out = {}
        regex_var = r'(?P<type>.+?(?P<precision>\d*)(?:_t)?)\s*(?P<pointer>\**)'
        if backwards.PY2:  # pragma: Python 2
            grp = re.search(r'^' + regex_var + r'$',
                            native_type).groupdict()
        else:
            grp = re.fullmatch(regex_var, native_type).groupdict()
        if grp.get('precision', False):
            out['precision'] = int(grp['precision'])
            grp['type'] = grp['type'].replace(grp['precision'], 'X')
        if grp['type'] == 'char':
            out['type'] = 'bytes'
            out['precision'] = 0
        else:
            if grp['type'] == 'double':
                out['precision'] = 8 * 8
            elif grp['type'] == 'float':
                grp['type'] = 'double'
                out['precision'] = 4 * 8
            elif grp['type'] in ['int', 'uint']:
                grp['type'] += 'X_t'
                out['precision'] = 8 * np.dtype('intc').itemsize
            out['type'] = super(CModelDriver, cls).get_json_type(grp['type'])
        if grp.get('pointer', False):
            nptr = len(grp['pointer'])
            if grp['type'] == 'char':
                nptr -= 1
            if nptr > 0:
                out['subtype'] = out['type']
                if nptr == 1:
                    out['type'] = '1darray'
                else:
                    out['type'] = 'ndarray'
        return out
        
    @classmethod
    def format_function_param(cls, key, default=None, **kwargs):
        r"""Return the formatted version of the specified key.

        Args:
            key (str): Key in cls.function_param mapping that should be
                formatted.
            default (str, optional): Format that should be returned if key
                is not in cls.function_param. Defaults to None.
            **kwargs: Additional keyword arguments are used in formatting the
                request function parameter.

        Returns:
            str: Formatted string.

        Raises:
            NotImplementedError: If key is not in cls.function_param and default
                is not set.

        """
        if (key == 'import') and ('filename' in kwargs):
            kwargs['filename'] = os.path.basename(kwargs['filename'])
        elif (key == 'interface') and ('interface_library' in kwargs):
            kwargs['interface_library'] = os.path.basename(
                kwargs['interface_library']).replace('.c', '.h')
        kwargs['default'] = default
        return super(CModelDriver, cls).format_function_param(key, **kwargs)
    
    @classmethod
    def write_model_function_call(cls, model_function, flag_var, inputs, outputs):
        r"""Write lines necessary to call the model function.

        Args:
            model_function (str): Handle of the model function that should be
                called.
            flag_var (str): Name of variable that should be used as a flag.
            inputs (list): List of dictionaries describing inputs to the model.
            outputs (list): List of dictionaries describing outputs from the model.

        Returns:
            list: Lines required to carry out a call to a model function in
                this language.

        """
        new_inputs = copy.deepcopy(inputs)
        for x in new_inputs:
            for v in x['vars']:
                if v.get('allow_realloc', False):
                    v['name'] = '*' + v['name']
                if 'native_type_cast' in v:
                    v['name'] = '(%s)(%s)' % (v['native_type_cast'], v['name'])
        return super(CModelDriver, cls).write_model_function_call(
            model_function, flag_var, new_inputs, outputs)
        
    @classmethod
    def write_declaration(cls, name, **kwargs):
        r"""Return the line required to declare a variable with a certain
        type.

        Args:
            name (str): Name of variable being declared.
            **kwargs: Addition keyword arguments are passed to get_native_type.

        Returns:
            str: The line declaring the variable.

        """
        orig_name = name
        type_name = cls.get_native_type(**kwargs)
        if kwargs.get('allow_realloc', False):
            type_name += '*'
            kwargs['native_type'] = type_name
        if type_name.endswith('*'):
            kwargs.get('requires_freeing', []).append(name)
            name = '%s = NULL' % name
        out = super(CModelDriver, cls).write_declaration(name, **kwargs)
        if type_name.replace(' ', '') == 'char*':
            length_name = orig_name + '_length = 0'
            length_type = {'type': 'uint', 'precision': 64}
            out += ' ' + cls.write_declaration(length_name,
                                               datatype=length_type)
        return out
        
    @classmethod
    def prepare_variables(cls, vars_list):
        r"""Concatenate a set of input variables such that it can be passed as a
        single string to the function_call parameter.

        Args:
            vars_list (list): List of variable dictionaries containing info
                (e.g. names) that should be used to prepare a string representing
                input/output to/from a function call.

        Returns:
            str: Concatentated variables list.

        """
        if not isinstance(vars_list, list):
            vars_list = [vars_list]
        new_vars_list = []
        for x in vars_list:
            if isinstance(x, str):
                new_vars_list.append(x)
            else:
                assert(isinstance(x, dict))
                new_vars_list.append(x)
                if cls.get_native_type(**x).replace(' ', '') == 'char*':
                    new_vars_list.append({'name': x['name'] + '_length'})
        return super(CModelDriver, cls).prepare_variables(new_vars_list)
            
    @classmethod
    def prepare_output_variables(cls, vars_list, in_inputs=False):
        r"""Concatenate a set of output variables such that it can be passed as
        a single string to the function_call parameter.

        Args:
            vars_list (list): List of variable names to concatenate as output
                from a function call.
            in_inputs (bool, optional): If True, the output variables should
                be formated to be included as input variables. Defaults to
                False.

        Returns:
            str: Concatentated variables list.

        """
        if in_inputs:
            vars_list = [dict(y, name='&' + y['name']) for y in vars_list]
        return super(CModelDriver, cls).prepare_output_variables(vars_list)

    @classmethod
    def write_native_type_definition(cls, name, datatype, as_seri=False,
                                     requires_freeing=None, no_decl=False):
        r"""Get lines declarining the data type within the language.

        Args:
            name (str): Name of variable that definition should be stored in.
            datatype (dict): Type definition.
            as_seri (bool, optional): If True, the type variable is wrapped as
                a serialization structure. Defaults to False.
            requires_freeing (list, optional): List that variables requiring
                freeing should be appended to. Defaults to None.
            no_decl (bool, optional): If True, the variable is defined without
                declaring it (assumes that variable has already been declared).
                Defaults to False.

        Returns:
            list: Lines required to define a type definition.

        """
        out = []
        fmt = None
        keys = {}
        typename = datatype['type']
        if datatype['type'] == 'array':
            assert(isinstance(datatype['items'], list))
            keys['nitems'] = len(datatype['items'])
            keys['items'] = '%s_items' % name
            fmt = 'create_dtype_json_array({nitems}, {items})'
            out += [('dtype_t** %s = '
                     '(dtype_t**)malloc(%d*sizeof(dtype_t*));')
                    % (keys['items'], keys['nitems'])]
            for i, x in enumerate(datatype['items']):
                out += cls.write_native_type_definition(
                    '%s_items[%d]' % (name, i), x,
                    requires_freeing=requires_freeing, no_decl=True)
            assert(isinstance(requires_freeing, list))
            requires_freeing += [keys['items']]
        elif datatype['type'] == 'object':
            assert(isinstance(datatype['properties'], dict))
            keys['nitems'] = len(datatype['properties'])
            keys['keys'] = '%s_keys' % name
            keys['values'] = '%s_vals' % name
            fmt = 'create_dtype_json_object({nitems}, {keys}, {values})'
            out += [('dtype_t** %s = '
                     '(dtype_t**)malloc(%d*sizeof(dtype_t*));')
                    % (keys['values'], keys['nitems']),
                    ('char** %s = (char**)malloc(%d*sizeof(char*));')
                    % (keys['keys'], keys['nitems'])]
            for i, (k, v) in enumerate(datatype['properties'].items()):
                out += ['%s[%d] = \"%s\"' % (keys['keys'], i, k)]
                out += cls.write_native_type_definition(
                    '%s[%d]' % (keys['values'], i), v,
                    requires_freeing=requires_freeing)
            assert(isinstance(requires_freeing, list))
            requires_freeing += [keys['values'], keys['keys']]
        elif datatype['type'] in ['ply', 'obj']:
            fmt = 'create_dtype_%s()' % datatype['type']
        elif datatype['type'] == '1darray':
            fmt = ('create_dtype_1darray(\"{subtype}\", {precision}, {length}, '
                   '\"{units}\")')
            keys = {k: datatype[k] for k in ['subtype', 'precision', 'length']}
            keys['units'] = datatype.get('units', '')
        elif datatype['type'] in ['1darray', 'ndarray']:
            fmt = ('create_dtype_ndarray(\"{subtype}\", {precision}, {ndim}, {shape}, '
                   '\"{units}\")')
            keys = {k: datatype[k] for k in ['subtype', 'precision', 'shape']}
            keys['ndim'] = len(keys['shape'])
            keys['units'] = datatype.get('units', '')
        else:
            fmt = 'create_dtype_scalar(\"{subtype}\", {precision}, \"{units}\")'
            keys = {}
            keys['subtype'] = datatype.get('subtype', datatype['type'])
            keys['units'] = datatype.get('units', '')
            if keys['subtype'] in ['bytes']:
                keys['precision'] = datatype.get('precision', 0)
            else:
                keys['precision'] = datatype['precision']
            typename = 'scalar'
        if as_seri:
            def_line = ('seri_t* %s = init_serializer(\"%s\", %s);'
                        % (name, typename, fmt.format(**keys)))
        else:
            def_line = '%s = %s;' % (name, fmt.format(**keys))
            if not no_decl:
                def_line = 'dtype_t* ' + def_line
        out.append(def_line)
        return out

    @classmethod
    def write_channel_def(cls, key, datatype=None, requires_freeing=None,
                          **kwargs):
        r"""Write an channel declaration/definition.

        Args:
            key (str): Entry in cls.function_param that should be used.
            datatype (dict, optional): Data type associated with the channel.
                Defaults to None and is ignored.
            requires_freeing (list, optional): List that variables requiring
                freeing should be appended to. Defaults to None.
            **kwargs: Additional keyword arguments are passed as parameters
                to format_function_param.

        Returns:
            list: Lines required to declare and define an output channel.

        """
        out = []
        if (datatype is not None) and ('{channel_type}' in cls.function_param[key]):
            kwargs['channel_type'] = '%s_type' % kwargs['channel']
            out += cls.write_native_type_definition(
                kwargs['channel_type'], datatype,
                requires_freeing=requires_freeing)
        out += super(CModelDriver, cls).write_channel_def(key, datatype=datatype,
                                                          **kwargs)
        return out
