import os
import shutil
from collections import OrderedDict
from yggdrasil import platform, tools
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, ArchiverBase)
from yggdrasil.languages import get_language_dir


_default_internal_libtype = 'object'
# if platform._is_win:  # pragma: windows
#     _default_internal_libtype = 'static'


class CCompilerBase(CompilerBase):
    r"""Base class for C compilers."""
    languages = ['c']
    default_executable_env = 'CC'
    # TODO: Additional flags environment variables?
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
    

# _top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
# _incl_interface = os.path.join(_top_dir, 'interface')
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
                # 'directory': _incl_interface,
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
        'float': 'floatX_t',
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
        'schema': 'map_t'}
    function_param = {
        'comment': '//',
        'true': '1',
        'indent': 2 * ' ',
        'print': 'printf(\"{message}\");',
        'error': 'return -1;',
        'block_end': '}',
        'if_begin': 'if ({cond}) {{',
        'for_begin': ('for ({iter_var} = {iter_begin}; {iter_var} < {iter_end}; '
                      '{iter_var}++) {{'),
        'while_begin': 'while ({cond}) {{',
        'break': 'break;',
        'declare': '{type} {name};',
        'assign': '{name} = {value};',
        'exec_begin': 'int main() {',
        'exec_end': '  return 0;\n}'}

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
                cls.internal_libraries[x]['compiler_flags'].append('-fPIC')
        
    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language. This includes locating
        any required external libraries and setting option defaults.

        Args:
            cfg (YggConfigParser): Config class that options should be set for.

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
        return out
        
    @classmethod
    def update_ld_library_path(cls, env):
        r"""Update provided dictionary of environment variables so that
        LD_LIBRARY_PATH includes the interface directory containing the interface
        libraries.

        Args:
            env (dict): Dictionary of enviroment variables to be updated.

        Returns:
            dict: Updated dictionary of environment variables.

        """
        if platform._is_linux:
            path_list = []
            prev_path = env.pop('LD_LIBRARY_PATH', '')
            if prev_path:
                path_list.append(prev_path)
            for x in [cls.get_language_dir()]:
                if x not in prev_path:
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
