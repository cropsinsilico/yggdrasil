import os
import re
import warnings
import copy
import shutil
import subprocess
import numpy as np
import sysconfig
from collections import OrderedDict
from yggdrasil import platform, tools
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, LinkerBase, ArchiverBase,
    get_compilation_tool)
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    _valid_types)
from yggdrasil.languages import get_language_dir
from yggdrasil.config import ygg_cfg
from numpy import distutils as numpy_distutils


_default_internal_libtype = 'object'
# if platform._is_win:  # pragma: windows
#     _default_internal_libtype = 'static'
_top_lang_dir = get_language_dir('c')


def get_OSX_SYSROOT():
    r"""Determin the path to the OSX SDK.

    Returns:
        str: Full path to the SDK directory if one is located. None
            otherwise.

    """
    fname = None
    if platform._is_mac:
        try:
            xcode_dir = subprocess.check_output(
                'echo "$(xcode-select -p)"', shell=True).decode("utf-8").strip()
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
    linker_attributes = {'default_executable_env': 'LD',
                         'default_flags_env': 'LDFLAGS',
                         'search_path_envvar': ['LIBRARY_PATH', 'LD_LIBRARY_PATH']}
    search_path_envvar = ['C_INCLUDE_PATH']
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
            grp = re.search(r'MacOSX(?P<target>[0-9]+\.[0-9]+)?',
                            _osx_sysroot).groupdict()
            # This is only utilized on local installs where a
            # non-default SDK is installed in addition to the default
            if grp['target']:  # pragma: debug
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
    
    @classmethod
    def get_search_path(cls, *args, **kwargs):
        r"""Determine the paths searched by the tool for external library files.

        Args:
            *args: Additional arguments are passed to the parent
                class's method.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: List of paths that the tools will search.

        """
        cfg = kwargs.get('cfg', ygg_cfg)
        libtype = kwargs.get('libtype', None)
        out = super(CompilerBase, cls).get_search_path(*args, **kwargs)
        macos_sdkroot = cfg.get('c', 'macos_sdkroot', _osx_sysroot)
        if platform._is_mac and (macos_sdkroot is not None):
            base_path = os.path.join(macos_sdkroot, 'usr')
            assert(libtype == 'include')
            new = os.path.join(base_path, 'include')
            if new not in out:
                out.append(new)
        return out


class GCCCompiler(CCompilerBase):
    r"""Interface class for gcc compiler/linker."""
    toolname = 'gcc'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_archiver = 'ar'
    linker_attributes = dict(
        CCompilerBase.linker_attributes,
        flag_options=OrderedDict(
            list(LinkerBase.flag_options.items())
            + list(CCompilerBase.linker_attributes.get('flag_options', {}).items())
            + [('library_rpath', '-Wl,-rpath')]))
    toolset = 'gnu'
    aliases = ['gnu-cc']

    @classmethod
    def is_installed(cls):
        r"""Determine if this tool is installed by looking for the executable.

        Returns:
            bool: True if the tool is installed, False otherwise.

        """
        out = super(GCCCompiler, cls).is_installed()
        if out and platform._is_mac:  # pragma: debug
            ver = cls.call(cls.version_flags, skip_flags=True, allow_error=True)
            if 'clang' in ver:
                out = False  # Disable gcc when it is an alias for clang
        return out

    def dll2a(cls, dll, dst=None, overwrite=False):
        r"""Convert a window's .dll library into a static library.

        Args:
            dll (str): Full path to .dll library to convert.
            dst (str, optional): Full path to location where the new
                library should be saved. Defaults to None and will be
                set based on lib or will be placed in the same directory
                as dll.
            overwrite (bool, optional): If True, the static file will
                be created even if it already exists. Defaults to False.

        Returns:
            str: Full path to new .a static library.

        """
        # https://sourceforge.net/p/mingw-w64/wiki2/
        # Answer%20generation%20of%20DLL%20import%20library/
        base = os.path.splitext(os.path.basename(dll))[0]
        if dst is None:
            libbase = base
            if not libbase.startswith('lib'):
                libbase = 'lib' + libbase
            libdir = os.path.dirname(dll)
            dst = os.path.join(libdir, libbase + '.dll.a')
        if (not os.path.isfile(dst)) or overwrite:
            gendef = shutil.which("gendef")
            dlltool = shutil.which("dlltool")
            if gendef and dlltool:
                subprocess.check_call([gendef, dll])
                subprocess.check_call(
                    [dlltool, '-D', dll, '-d', '%s.def' % base, '-l', dst])
            else:
                dst = dll
        assert(os.path.isfile(dst))
        return dst


class ClangCompiler(CCompilerBase):
    r"""Interface class for clang compiler/linker."""
    toolname = 'clang'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_linker = 'clang'
    default_archiver = 'libtool'
    flag_options = OrderedDict(list(CCompilerBase.flag_options.items())
                               + [('sysroot', '--sysroot'),
                                  ('isysroot', {'key': '-isysroot',
                                                'prepend': True}),
                                  ('mmacosx-version-min',
                                   '-mmacosx-version-min=%s')])
    # Set to False since ClangLinker has its own class to handle
    # conflict between versions of clang and ld.
    is_linker = False
    toolset = 'llvm'

    @classmethod
    def get_flags(cls, *args, **kwargs):
        r"""Get a list of compiler flags."""
        out = super(ClangCompiler, cls).get_flags(*args, **kwargs)
        if '-fopenmp' in out:
            idx = out.index('-fopenmp')
            if (idx > 0) and (out[idx - 1] != '-Xpreprocessor'):
                out.insert(idx, '-Xpreprocessor')
        return out
        

class MSVCCompiler(CCompilerBase):
    r"""Microsoft Visual Studio C Compiler."""
    toolname = 'cl'
    platforms = ['Windows']
    # TODO: Currently everything compiled as C++ on windows to allow use
    # of complex types. Use '/TC' instead of '/TP' for strictly C
    default_flags = ['/W4',      # Display all errors
                     '/Zi',      # Symbolic debug in .pdb (implies debug)
                     '/FS',      # Allow synchronous write to .pdb
                     # '/MD',
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
    search_path_envvar = ['INCLUDE']
    search_path_flags = None
    version_flags = []
    product_exts = ['.dir', '.ilk', '.pdb', '.sln', '.vcxproj', '.vcxproj.filters',
                    '.exp', '.lib']
    combine_with_linker = True  # Must be explicit; linker is separate .exe
    linker_attributes = dict(GCCCompiler.linker_attributes,
                             default_executable=None,
                             default_executable_env='LINK',
                             output_key='/OUT:%s',
                             output_first=True,
                             output_first_library=False,
                             flag_options=OrderedDict(
                                 [('library_libs', ''),
                                  ('library_libs_nonstd', ''),
                                  ('library_dirs', '/LIBPATH:%s')]),
                             shared_library_flag='/DLL',
                             search_path_envvar=['LIB'],
                             search_path_flags=None)
    toolset = 'msvc'
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        compiler_path = shutil.which('cl.exe')
        linker_path = shutil.which('link.exe')
        if (((compiler_path and linker_path)
             and (os.path.dirname(compiler_path).lower()
                  != os.path.dirname(linker_path).lower()))):
            cls.linker_attributes['default_executable'] = os.path.join(
                os.path.dirname(compiler_path), os.path.basename(linker_path))
            assert(os.path.isfile(
                cls.linker_attributes['default_executable']))
        CCompilerBase.before_registration(cls)
        
    @classmethod
    def tool_version(cls, **kwargs):  # pragma: windows
        r"""Determine the version of this tool.

        Args:
            **kwargs: Keyword arguments are passed to cls.call.

        Returns:
            str: Version of the tool.

        """
        out = cls.call(cls.version_flags, skip_flags=True,
                       allow_error=True, **kwargs)
        if 'Copyright' not in out:  # pragma: debug
            raise RuntimeError("Version call failed: %s" % out)
        return out.split('Copyright')[0]


# C Linkers
class LDLinker(LinkerBase):
    r"""Linker class for ld tool."""
    toolname = 'ld'
    # Languages disabled for ld by default to prevent it being
    # selected instead of the default which seems to be happening
    # on the CI
    languages = ['c']  # ['c', 'c++', 'fortran']
    default_executable_env = 'LD'
    default_flags_env = 'LDFLAGS'
    version_flags = ['-v']
    search_path_envvar = ['LIBRARY_PATH', 'LD_LIBRARY_PATH']

    @classmethod
    def tool_version(cls, **kwargs):
        r"""Determine the version of this tool.

        Args:
            **kwargs: Keyword arguments are passed to cls.call.

        Returns:
            str: Version of the tool.

        """
        out = cls.call(cls.version_flags, skip_flags=True,
                       allow_error=True, **kwargs)
        if platform._is_mac:
            regex = r'PROJECT:ld64-(?P<version>\d+(?:\.\d+)?)'
        else:
            regex = (r'GNU ld \(GNU Binutils(?: for (?P<os>.+))?\) '
                     r'(?P<version>\d+(?:\.\d+){0,2})')
        match = re.search(regex, out)
        if match is None:  # pragma: debug
            raise RuntimeError("Could not locate version in string: %s" % out)
        return match.group('version')


class ClangLinker(LDLinker):
    r"""Interface class for clang linker (calls to ld)."""
    toolname = ClangCompiler.toolname
    aliases = ClangCompiler.aliases
    languages = ClangCompiler.languages
    platforms = ClangCompiler.platforms
    default_executable = ClangCompiler.default_executable
    toolset = ClangCompiler.toolset
    search_path_flags = ['-Xlinker', '-v']
    search_regex = [r'\t([^\t\n]+)\n']
    search_regex_begin = 'Library search paths:'
    flag_options = OrderedDict(LDLinker.flag_options,
                               **{'linker-version': '-mlinker-version=%s',
                                  'library_rpath': '-rpath',
                                  'library_libs_nonstd': ''})

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        LDLinker.before_registration(cls)
        if platform._is_win:  # pragma: windows
            # One windows clang calls the MSVC linker LINK.exe which does not
            # accept rpath. Runtime libraries must be in the same directory
            # as the executable or a directory in the PATH env variable.
            cls.flag_options.pop('library_rpath', None)

    @classmethod
    def get_flags(cls, *args, **kwargs):
        r"""Get a list of linker flags."""
        # Handle case where clang (10.0.0) is trying to pass
        # -platform_version to a version of ld64 that dosn't support
        # it (<520).
        # https://bugs.llvm.org/show_bug.cgi?id=44813
        # https://reviews.llvm.org/D71579
        # https://reviews.llvm.org/D74784
        out = cls.call(cls.version_flags, skip_flags=True, allow_error=True)
        regex = r'clang version (?P<version>\d+)\.\d+\.\d+'
        match = re.search(regex, out)
        if (match is not None) and (int(match.group('version')) >= 10):
            ld_version = LDLinker.tool_version()
            if float(ld_version.split('.')[0]) < 520:  # pragma: version
                # No longer covered as the default conda
                # install no longer causes this configuration
                # to occur, but this will not be deprecated
                # as existing installs still have this mismatch
                kwargs['linker-version'] = ld_version
        out = super(ClangLinker, cls).get_flags(*args, **kwargs)
        if '-lstdc++' not in out:
            out.append('-lstdc++')
        if '-fopenmp' in out:
            out[out.index('-fopenmp')] = '-lomp'
        return out


# C Archivers
class ARArchiver(ArchiverBase):
    r"""Archiver class for ar tool."""
    toolname = 'ar'
    languages = ['c', 'c++', 'fortran']
    default_executable_env = 'AR'
    default_flags_env = None
    static_library_flag = 'rcs'
    output_key = ''
    output_first_library = True
    toolset = 'gnu'
    compatible_toolsets = ['llvm']
    search_path_envvar = ['LIBRARY_PATH']


class LibtoolArchiver(ArchiverBase):
    r"""Archiver class for libtool tool."""
    toolname = 'libtool'
    languages = ['c', 'c++']
    default_executable_env = 'LIBTOOL'
    static_library_flag = '-static'  # This is the default
    toolset = 'clang'
    search_path_envvar = ['LIBRARY_PATH']
    

class MSVCArchiver(ArchiverBase):
    r"""Microsoft Visual Studio C Archiver."""
    toolname = 'LIB'
    languages = ['c', 'c++']
    platforms = ['Windows']
    static_library_flag = None
    output_key = '/OUT:%s'
    toolset = 'msvc'
    compatible_toolsets = ['llvm']
    search_path_envvar = ['LIB']
    
    # @classmethod
    # def is_import_lib(cls, libpath):
    #     r"""Determine if a library is an import library or a static
    #     library.
        
    #     Args:
    #         libpath (str): Full path to library.

    #     Returns:
    #         bool: True if the library is an import library, False otherwise.

    #     """
    #     if (not os.path.isfile(libpath)) or (not libpath.endswith('.lib')):
    #         return False
    #     out = subprocess.check_output([cls.get_executable(full_path=True),
    #                                    '/list', libpath])
    #     files = set(out.splitlines())
    #     if any([f.endswith('.obj') for f in files]):
    #         return False
    #     return True

    
_incl_interface = _top_lang_dir
_incl_seri = os.path.join(_top_lang_dir, 'serialize')
_incl_comm = os.path.join(_top_lang_dir, 'communication')
_python_inc = ygg_cfg.get('c', 'python_include', None)
if (_python_inc is None) or (not os.path.isfile(_python_inc)):  # pragma: no cover
    _python_inc = sysconfig.get_paths()['include']
else:
    _python_inc = os.path.dirname(_python_inc)
try:
    if platform._is_win:  # pragma: windows
        libtype_order = ['static', 'shared']
    else:
        libtype_order = ['shared', 'static']
    _python_lib = ygg_cfg.get('c', 'python_%s' % libtype_order[0],
                              ygg_cfg.get('c', 'python_%s' % libtype_order[1], None))
    if (_python_lib is None) or (not os.path.isfile(_python_lib)):  # pragma: no cover
        _python_lib = tools.get_python_c_library(
            allow_failure=False, libtype=libtype_order[0])
except BaseException as e:  # pragma: debug
    warnings.warn("ERROR LOCATING PYTHON LIBRARY: %s" % e)
    _python_lib = None
_numpy_inc = numpy_distutils.misc_util.get_numpy_include_dirs()
_numpy_lib = None  # os.path.join(os.path.dirname(_numpy_inc[0]), 'lib', 'npymath.lib')


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
                 'language': 'c'},
        'numpy': {'include': os.path.join(_numpy_inc[0], 'numpy',
                                          'arrayobject.h'),
                  'libtype': 'header_only',
                  'language': 'c'},
        'python': {'include': os.path.join(_python_inc, 'Python.h'),
                   'language': 'c'}}
    internal_libraries = {
        'ygg': {'source': os.path.join(_incl_interface, 'YggInterface.c'),
                'language': 'c',
                'linker_language': 'c++',  # Some dependencies are C++
                'internal_dependencies': ['regex', 'datatypes',
                                          'python_wrapper'],
                'external_dependencies': ['rapidjson',
                                          'python', 'numpy'],
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
                      'external_dependencies': ['rapidjson',
                                                'python', 'numpy'],
                      'include_dirs': []},
        'python_wrapper': {'source': 'python_wrapper.c',
                           'directory': _top_lang_dir,
                           'language': 'c',
                           'libtype': 'shared',
                           'external_dependencies': ['python', 'numpy'],
                           'linker_language': 'c',
                           'include_dirs': [_top_lang_dir]}}
    type_map = {
        'comm': 'comm_t*',
        'dtype': 'dtype_t*',
        'int': 'intX_t',
        'float': 'double',
        'string': 'string_t',
        'array': 'json_array_t',
        'object': 'json_object_t',
        'integer': 'int',
        'boolean': 'bool',
        'null': 'void*',
        'uint': 'uintX_t',
        'complex': 'complex_X',
        'bytes': 'char*',
        'unicode': 'unicode_t',
        '1darray': '*',
        'ndarray': '*',
        'ply': 'ply_t',
        'obj': 'obj_t',
        'schema': 'schema_t',
        'flag': 'int',
        'class': 'python_class_t',
        'function': 'python_function_t',
        'instance': 'python_instance_t',
        'any': 'generic_t'}
    interface_map = {
        'import': '#include "YggInterface.h"',
        'input': 'yggInputType("{channel_name}", {datatype})',
        'output': 'yggOutputType("{channel_name}", {datatype})',
        'server': 'yggRpcServerType("{channel_name}", {datatype_in}, {datatype_out})',
        'client': 'yggRpcClientType("{channel_name}", {datatype_out}, {datatype_in})',
        'timesync': 'yggTimesync("{channel_name}", "{time_units}")',
        'send': 'flag = yggSend({channel_obj}, {outputs})',
        'recv': 'flag = yggRecv({channel_obj}, {input_refs})',
        'call': 'flag = rpcCall({channel_obj}, {outputs}, {inputs})',
    }
    type_class_map = {}
    function_param = {
        'import': '#include \"{filename}\"',
        'index': '{variable}[{index}]',
        'interface': '#include \"{interface_library}\"',
        'input': ('{channel} = yggInputType('
                  '\"{channel_name}\", {channel_type});'),
        'output': ('{channel} = yggOutputType('
                   '\"{channel_name}\", {channel_type});'),
        'recv_heap': 'yggRecvRealloc',
        'recv_stack': 'yggRecv',
        'recv_function': 'yggRecvRealloc',
        'send_function': 'yggSend',
        'not_flag_cond': '{flag_var} < 0',
        'flag_cond': '{flag_var} >= 0',
        'declare': '{type_name} {variable};',
        'init_array': 'init_json_array()',
        'init_object': 'init_json_object()',
        'init_schema': 'init_schema()',
        'init_ply': 'init_ply()',
        'init_obj': 'init_obj()',
        'init_class': 'init_python()',
        'init_function': 'init_python()',
        'init_instance': 'init_generic()',
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
        'init_type_ndarray_arr': ('create_dtype_ndarray_arr(\"{subtype}\", '
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
        'copy_array': '{name} = copy_json_array({value});',
        'copy_object': '{name} = copy_json_object({value});',
        'copy_schema': '{name} = copy_schema({value});',
        'copy_ply': '{name} = copy_ply({value});',
        'copy_obj': '{name} = copy_obj({value});',
        'copy_class': '{name} = copy_python({value});',
        'copy_function': '{name} = copy_python({value});',
        'copy_instance': '{name} = copy_generic({value});',
        'copy_any': '{name} = copy_generic({value});',
        'free_array': 'free_json_array({variable});',
        'free_object': 'free_json_object({variable});',
        'free_schema': 'free_schema({variable});',
        'free_ply': 'free_ply({variable});',
        'free_obj': 'free_obj({variable});',
        'free_class': 'destroy_python({variable});',
        'free_function': 'destroy_python({variable});',
        'free_instance': 'free_generic({variable});',
        'free_any': 'free_generic({variable});',
        'print_float': 'printf("%f\\n", {object});',
        'print_int': 'printf("%i\\n", {object});',
        'print_uint': 'printf("%u\\n", {object});',
        'print_string': 'printf("%s\\n", {object});',
        'print_unicode': 'printf("%s\\n", {object});',
        'print_bytes': 'printf("%s\\n", {object});',
        'print_complex': 'print_complex({object});',
        'print_array': 'display_json_array({object});',
        'print_object': 'display_json_object({object});',
        'print_schema': 'display_schema({object});',
        'print_ply': 'display_ply({object});',
        'print_obj': 'display_obj({object});',
        'print_class': 'display_python({object});',
        'print_function': 'display_python({object});',
        'print_instance': 'display_generic({object});',
        'print_any': 'display_generic({object});',
        'assign': '{name} = {value};',
        'assign_copy': 'memcpy({name}, {value}, {N}*sizeof({native_type}));',
        'comment': '//',
        'true': 'true',
        'false': 'false',
        'true_flag': '1',
        'false_flag': '0',
        'null': 'NULL',
        'not': '!',
        'and': '&&',
        'indent': 2 * ' ',
        'quote': '\"',
        'print': 'printf(\"{message}\\n\");',
        'fprintf': 'printf(\"{message}\\n\", {variables});',
        'error': 'printf(\"{error_msg}\\n\"); return -1;',
        'block_end': '}',
        'line_end': ';',
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
        'free': 'if ({variable} != NULL) {{ free({variable}); {variable} = NULL; }}',
        'function_def_begin': '{output_type} {function_name}({input_var}) {{',
        'return': 'return {output_var};',
        'function_def_regex': (
            r'(?P<flag_type>.+?)\s*{function_name}\s*'
            r'\((?P<inputs>(?:[^{{])*?)\)\s*\{{'
            r'(?P<body>(?:.*?\n?)*?)'
            r'(?:(?:return *(?P<flag_var>.+?)?;(?:.*?\n?)*?\}})'
            r'|(?:\}}))'),
        'inputs_def_regex': (
            r'\s*(?P<native_type>(?:[^\s\*])+(\s+)?'
            r'(?P<ptr>\*+)?)(?(ptr)(?(1)(?:\s*)|(?:\s+)))'
            r'(\((?P<name_ptr>\*+)?)?(?P<name>.+?)(?(4)(?:\)))'
            r'(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?'),
        'outputs_def_regex': (
            r'\s*(?P<native_type>(?:[^\s\*])+(\s+)?'
            r'(?P<ptr>\*+)?)(?(ptr)(?(1)(?:\s*)|(?:\s+)))'
            r'(?P<name>.+?)(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?')}
    outputs_in_inputs = True
    include_channel_obj = True
    is_typed = True
    brackets = (r'{', r'}')

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration."""
        if cls.default_compiler is None:
            if platform._is_linux:
                cls.default_compiler = 'gcc'
            elif platform._is_mac:
                cls.default_compiler = 'clang'
            elif platform._is_win:  # pragma: windows
                cls.default_compiler = 'cl'
        CompiledModelDriver.after_registration(cls, **kwargs)
        if kwargs.get('second_pass', False):
            return
        if _python_lib:
            if ((_python_lib.endswith(('.lib', '.a'))
                 and not _python_lib.endswith('.dll.a'))):
                cls.external_libraries['python']['libtype'] = 'static'
                cls.external_libraries['python']['static'] = _python_lib
            else:
                cls.external_libraries['python']['libtype'] = 'shared'
                cls.external_libraries['python']['shared'] = _python_lib
        if platform._is_win:  # pragma: windows
            for libtype in ['static', 'shared']:
                if libtype in cls.external_libraries['python']:
                    continue
                cls.external_libraries['python'][libtype] = tools.get_python_c_library(
                    allow_failure=True, libtype=libtype)
            for x in ['zmq', 'czmq', 'python']:
                if x in cls.external_libraries:
                    cls.external_libraries[x]['libtype'] = 'windows_import'
            cls.internal_libraries['python_wrapper']['libtype'] = 'windows_import'
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
            for x in ['ygg', 'datatypes', 'python_wrapper']:
                if 'compiler_flags' not in cls.internal_libraries[x]:
                    cls.internal_libraries[x]['compiler_flags'] = []
                if '-fPIC' not in cls.internal_libraries[x]['compiler_flags']:
                    cls.internal_libraries[x]['compiler_flags'].append('-fPIC')
        
    @classmethod
    def configure(cls, cfg, macos_sdkroot=None, vcpkg_dir=None, **kwargs):
        r"""Add configuration options for this language. This includes locating
        any required external libraries and setting option defaults.

        Args:
            cfg (YggConfigParser): Config class that options should be set for.
            macos_sdkroot (str, optional): Full path to the root directory for
                the MacOS SDK that should be used. Defaults to None and is
                ignored.
            vcpkg_dir (str, optional): Full path to the root directory containing
                a vcpkg installation. This should be the directory that contains
                the vcpkg executable and any packages installed by vcpkg (in
                subdirectories). Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        # Set vcpkg_dir & macos_sdkroot before calling parent so that it can be
        # used in get_search_path when searching for dependencies
        if (cls.language is not None) and (not cfg.has_section(cls.language)):
            cfg.add_section(cls.language)
        if vcpkg_dir is None:
            vcpkg_dir = os.environ.get('VCPKG_ROOT', None)
        if vcpkg_dir is not None:
            vcpkg_dir = os.path.abspath(vcpkg_dir)
            if not os.path.isdir(vcpkg_dir):  # pragma: debug
                raise ValueError("Path to vcpkg root directory "
                                 "does not exist: %s." % vcpkg_dir)
            cfg.set(cls._language, 'vcpkg_dir', vcpkg_dir)
        if macos_sdkroot is None:
            macos_sdkroot = _osx_sysroot
        if macos_sdkroot is not None:
            if not os.path.isdir(macos_sdkroot):  # pragma: debug
                raise ValueError("Path to MacOS SDK root directory "
                                 "does not exist: %s." % macos_sdkroot)
            cfg.set(cls._language, 'macos_sdkroot', macos_sdkroot)
        # Call __func__ to avoid direct invoking of class which dosn't exist
        # in after_registration where this is called
        out = CompiledModelDriver.configure.__func__(cls, cfg, **kwargs)
        # Change configuration to be directory containing include files
        rjlib = cfg.get(cls._language, 'rapidjson_include', None)
        if (rjlib is not None) and os.path.isfile(rjlib):
            cfg.set(cls._language, 'rapidjson_include',
                    os.path.dirname(os.path.dirname(rjlib)))
        nplib = cfg.get(cls._language, 'numpy_include', None)
        if (nplib is not None) and os.path.isfile(nplib):
            cfg.set(cls._language, 'numpy_include',
                    os.path.dirname(os.path.dirname(nplib)))
        return out

    @classmethod
    def get_dependency_info(cls, dep, toolname=None, default=None):
        r"""Get the dictionary of information associated with a
        dependency.

        Args:
            dep (str): Name of internal or external dependency or full path
                to the library.
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.
            default (dict, optional): Information dictionary that should
                be returned if dep cannot be located. Defaults to None
                and an error will be raised if dep cannot be found.

        Returns:
            dict: Dependency info.

        """
        replaced_toolname = False
        if platform._is_win and (dep == 'python_wrapper'):
            # The Python library is compiled against MSVC so a wrapper is requried
            # to reconcile the differences in FILE* between gcc and MSVC.
            if get_compilation_tool('compiler', 'cl').is_installed():
                replaced_toolname = True
                toolname = 'cl'
        out = super(CModelDriver, cls).get_dependency_info(
            dep, toolname=toolname, default=default)
        if replaced_toolname:
            out['remove_flags'] = ['/TP']
            out['toolname'] = toolname
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
    def update_ld_library_path(cls, env, paths_to_add=None,
                               add_to_front=False, add_libpython_dir=False,
                               toolname=None, env_var=None, **kwargs):
        r"""Update provided dictionary of environment variables so that
        LD_LIBRARY_PATH includes the interface directory containing the interface
        libraries.

        Args:
            env (dict): Dictionary of enviroment variables to be updated.
            paths_to_add (list, optional): Paths that should be added. If not
                provided, defaults to [cls.get_language_dir()].
            add_to_front (bool, optional): If True, new paths are added to the
                front, rather than the end. Defaults to False.
            add_libpython_dir (bool, optional): If True, the directory
                containing the Python C library will be added. Defaults
                to False.
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.
            env_var (str, optional): Environment variable where the paths
                should be added. Defaults to None and is only set for
                linux (LD_LIBRARY_PATH) and windows (PATH).
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            dict: Updated dictionary of environment variables.

        """
        if paths_to_add is None:
            paths_to_add = []
        paths_to_add = paths_to_add + [cls.get_language_dir()]
        if add_libpython_dir:
            paths_to_add = paths_to_add + [os.path.dirname(
                cls.get_dependency_library('python', toolname=toolname))]
        if platform._is_win and ygg_cfg.get('c', 'vcpkg_dir', None):
            if platform._is_64bit:
                arch = 'x64-windows'
            else:  # pragma: debug
                arch = 'x86-windows'
                raise NotImplementedError("Not yet tested on 32bit Python")
            paths_to_add.append(os.path.join(ygg_cfg.get('c', 'vcpkg_dir'),
                                             'installed', arch, 'bin'))
        if env_var is None:
            if platform._is_linux:
                env_var = 'LD_LIBRARY_PATH'
            elif platform._is_win:
                env_var = 'PATH'
        if env_var is not None:
            path_list = []
            prev_path = env.pop(env_var, '')
            prev_path_list = prev_path.split(os.pathsep)
            if prev_path:
                path_list.append(prev_path)
            for x in paths_to_add:
                if x not in prev_path_list:
                    if add_to_front:
                        path_list.insert(0, x)
                    else:
                        path_list.append(x)
            if path_list:
                env[env_var] = os.pathsep.join(path_list)
        return env

    @classmethod
    def update_python_path(cls, env):
        r"""Update provided dictionary of environment variables so that
        PYTHONPATH and PYTHONHOME are set as needed (primarily on windows).

        Args:
            env (dict): Dictionary of enviroment variables to be updated.

        Returns:
            dict: Updated dictionary of environment variables.

        """
        if platform._is_win:  # pragma: windows
            env.setdefault('PYTHONHOME', sysconfig.get_config_var('prefix'))
            env.setdefault('PYTHONPATH', os.pathsep.join([
                sysconfig.get_path('stdlib'), sysconfig.get_path('purelib'),
                os.path.join(sysconfig.get_config_var('prefix'), 'DLLs')]))
        return env

    @classmethod
    def set_env_class(cls, **kwargs):
        r"""Set environment variables that are instance independent.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and update_ld_library_path.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CModelDriver, cls).set_env_class(**kwargs)
        out = cls.update_ld_library_path(out, **kwargs)
        out = cls.update_python_path(out)
        return out
    
    @classmethod
    def parse_var_definition(cls, io, value, **kwargs):
        r"""Extract information about input/output variables from a
        string definition.

        Args:
            io (str): Description of variables contained in the provided
                string. Must be 'inputs' or 'outputs'.
            value (str): String containing one or more variable definitions.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: List of information about the variables contained in
                the provided string.

        Raises:
            AssertionError: If io is not 'inputs' or 'outputs'.
            NotImplementedError: If the def_regex for the specified
                io is not defined.

        """
        out = super(CModelDriver, cls).parse_var_definition(io, value, **kwargs)
        io_map = {x['name']: x for x in out}
        for i, x in enumerate(out):
            if (x['name'] + '_length') in io_map:
                x['length_var'] = x['name'] + '_length'
            elif ('length_' + x['name']) in io_map:
                x['length_var'] = 'length_' + x['name']
            elif (((x['name'] + '_ndim') in io_map)
                  and ((x['name'] + '_shape') in io_map)):
                x['ndim_var'] = x['name'] + '_ndim'
                x['shape_var'] = x['name'] + '_shape'
                x['datatype']['type'] = 'ndarray'
            elif ((('ndim_' + x['name']) in io_map)
                  and (('shape_' + x['name']) in io_map)):
                x['ndim_var'] = 'ndim_' + x['name']
                x['shape_var'] = 'shape_' + x['name']
                x['datatype']['type'] = 'ndarray'
            elif 'shape' in x:
                x['datatype']['shape'] = [
                    int(float(s.strip('[]')))
                    for s in x.pop('shape').split('][')]
                assert(x['datatype']['subtype'] in _valid_types)
                if len(x['datatype']['shape']) == 1:
                    x['datatype']['length'] = x['datatype'].pop(
                        'shape')[0]
                    x['datatype']['type'] = '1darray'
                else:
                    x['datatype']['type'] = 'ndarray'
        return out
        
    @classmethod
    def finalize_function_io(cls, direction, x):
        r"""Finalize info for an input/output channel following function
        parsing.

        Args:
            direction (str): Direction of channel ('input' or 'output')
            x (dict): Channel info.

        """
        super(CModelDriver, cls).finalize_function_io(direction, x)
        if direction == 'input':
            # Add length_vars if missing for use by yggdrasil
            for v in x['vars']:
                if cls.requires_length_var(v) and (not v.get('length_var', False)):
                    v['length_var'] = {'name': v['name'] + '_length',
                                       'datatype': {'type': 'uint',
                                                    'precision': 64},
                                       'is_length_var': True,
                                       'dependent': True}
                elif cls.requires_shape_var(v):
                    if not (v.get('ndim_var', False)
                            and v.get('shape_var', False)):  # pragma: debug
                        raise RuntimeError("Uncomment logic that follows.")
                    # if not v.get('ndim_var', False):
                    #     v['ndim_var'] = {
                    #         'name': v['name'] + '_ndim',
                    #         'datatype': {'type': 'uint',
                    #                      'precision': 64},
                    #         'is_length_var': True,
                    #         'dependent': True}
                    # if not v.get('shape_var', False):
                    #     v['shape_var'] = {
                    #         'name': v['name'] + '_ndim',
                    #         'datatype': {'type': '1darray',
                    #                      'subtype': 'uint',
                    #                      'precision': 64},
                    #         'is_length_var': True,
                    #         'dependent': True}
            # Flag input variables for reallocation
            allows_realloc = [cls.allows_realloc(v) for v in x['vars']]
            if all(allows_realloc):
                for v in x['vars']:
                    if (((v['native_type'] not in ['char*', 'string_t',
                                                   'bytes_t', 'unicode_t'])
                         and (not v.get('is_length_var', False))
                         and (v['datatype']['type'] not in
                              ['any', 'object', 'array', 'schema',
                               'instance', '1darray', 'ndarray'])
                         and (cls.function_param['recv_function']
                              == cls.function_param['recv_heap']))):
                        v['allow_realloc'] = True
        elif direction == 'output':
            # Add length_vars if missing for use by yggdrasil
            for v in x['vars']:
                if cls.requires_length_var(v) and (not v.get('length_var', False)):
                    if v['datatype']['type'] in ['1darray', 'ndarray']:
                        if 'iter_datatype' not in v:  # pragma: debug
                            raise RuntimeError("Length must be defined for "
                                               "arrays.")
                    elif v['datatype'].get('subtype', v['datatype']['type']) == 'bytes':
                        v['length_var'] = 'strlen(%s)' % v['name']
                    else:
                        v['length_var'] = 'strlen4(%s)' % v['name']
                elif (cls.requires_shape_var(v)
                      and not (v.get('ndim_var', False)
                               and v.get('shape_var', False))):  # pragma: debug
                    raise RuntimeError("Shape must be defined for ND arrays.")
        if x['datatype']['type'] == 'array':
            nvars_items = len(x['datatype'].get('items', []))
            nvars = sum([(not ix.get('is_length_var', False))
                         for ix in x['vars']])
            if nvars_items == nvars:
                x['use_generic'] = False
            else:
                x['use_generic'] = True

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
        if out.get('ptr', ''):
            assert(out['native_type'].endswith('*'))
            out['ptr'] = out['ptr'][:-1]
            out['native_type'] = out['native_type'][:-1]
            out['datatype'] = cls.get_json_type(out['native_type'])
            if (((out['datatype']['type'] == '1darray')
                 and var.get('ndim_var', False)
                 and var.get('shape_var', False))):
                out['datatype']['type'] = 'ndarray'
        return out

    @classmethod
    def output2input(cls, var, in_definition=True):
        r"""Perform conversion necessary to turn an output variable
        into an corresponding input that can be used to format a
        function definition.

        Args:
            var (dict): Variable definition.
            in_definition (bool, optional): If True, the returned
                dictionary corresponds to an input variable in a
                function definition. If False, the returned value
                will correspond to an input to a function. Defaults to
                True.

        Returns:
            dict: Updated variable definition.

        """
        out = super(CModelDriver, cls).output2input(var)
        if isinstance(var, dict):
            if in_definition:
                out = dict(out, name='*' + out['name'])
                if ((('shape' in out.get('datatype', {}))
                     or ('length' in out.get('datatype', {})))):
                    out['name'] = '(%s)' % out['name']
            else:
                out = dict(out, name='&' + out['name'])
                if ('shape' in out.get('datatype', {})) and (not platform._is_win):
                    out['name'] += len(out['datatype']['shape']) * '[0]'
        return out
        
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
        return True
        
    @classmethod
    def requires_length_var(cls, var):
        r"""Determine if a variable requires a separate length variable.

        Args:
            var (dict): Dictionary of variable properties.

        Returns:
            bool: True if a length variable is required, False otherwise.

        """
        if ((isinstance(var, dict)
             and ((cls.get_native_type(**var) in ['char*', 'string_t',
                                                  'bytes_t', 'unicode_t'])
                  or var.get('datatype', {}).get(
                      'type', var.get('type', None)) in ['1darray'])
             and (not var.get('is_length_var', False))
             and ('length' not in var.get('datatype', {})))):
            return True
        return False
    
    @classmethod
    def requires_shape_var(cls, var):
        r"""Determine if a variable requires a separate shape variable.

        Args:
            var (dict): Dictionary of variable properties.

        Returns:
            bool: True if a shape variable is required, False otherwise.

        """
        if ((isinstance(var, dict)
             and (var.get('datatype', {}).get(
                 'type', var.get('type', None)) == 'ndarray')
             and (not var.get('is_length_var', False))
             and ('shape' not in var.get('datatype', {})))):
            return True
        return False
              
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
        json_type = kwargs.get('datatype', kwargs)
        if isinstance(json_type, str):
            json_type = {'type': json_type}
        # if 'type' in kwargs:
        #     json_type.update(kwargs)
        assert(isinstance(json_type, dict))
        json_type = get_type_class(json_type['type']).normalize_definition(
            json_type)
        if out == '*':
            json_subtype = copy.deepcopy(json_type)
            json_subtype['type'] = json_subtype.pop('subtype')
            out = cls.get_native_type(datatype=json_subtype)
            if ('length' not in json_type) and ('shape' not in json_type):
                out += '*'
        elif 'X' in out:
            precision = json_type['precision']
            if json_type['type'] == 'complex':
                precision_map = {64: 'float',
                                 128: 'double',
                                 256: 'long_double'}
                if precision in precision_map:
                    out = out.replace('X', precision_map[precision])
                else:  # pragma: debug
                    raise ValueError("Unsupported precision for complex types: %d"
                                     % precision)
            else:
                out = out.replace('X', str(precision))
        elif out == 'double':
            if json_type['precision'] == 32:
                out = 'float'
        return out.replace(' ', '')
        
    @classmethod
    def get_json_type(cls, native_type):
        r"""Get the JSON type from the native language type.

        Args:
            native_type (str): The native language type.

        Returns:
            str, dict: The JSON type.

        """
        out = {}
        regex_var = r'(?P<type>.+?(?P<precision>\d*)(?:_t)?)\s*(?P<pointer>\**)'
        grp = re.fullmatch(regex_var, native_type).groupdict()
        if grp.get('precision', False):
            out['precision'] = int(grp['precision'])
            grp['type'] = grp['type'].replace(grp['precision'], 'X')
        if grp['type'] == 'char':
            out['type'] = 'bytes'
            out['precision'] = 0
        elif grp['type'] == 'void':
            out['type'] = 'null'
        elif grp['type'].startswith('complex'):
            out['type'] = 'complex'
            precision_map = {'long_double': 256,
                             'double': 128,
                             'float': 64}
            prec_str = grp['type'].split('complex_')[-1]
            if prec_str in precision_map:
                out['precision'] = precision_map[prec_str]
            else:  # pragma: debug
                raise ValueError("Cannot determine precision for complex type '%s'"
                                 % grp['type'])
        else:
            if grp['type'] == 'double':
                out['precision'] = 8 * 8
            elif grp['type'] == 'float':
                grp['type'] = 'double'
                out['precision'] = 4 * 8
            elif grp['type'] in ['int', 'uint']:
                grp['type'] += 'X_t'
                out['precision'] = 8 * np.dtype('intc').itemsize
            elif grp['type'] in ['bytes_t', 'string_t', 'unicode_t']:
                out['precision'] = 0
            out['type'] = super(CModelDriver, cls).get_json_type(grp['type'])
        if grp.get('pointer', False):
            nptr = len(grp['pointer'])
            if grp['type'] in ['char', 'void']:
                nptr -= 1
            if nptr > 0:
                out['subtype'] = out['type']
                out['type'] = '1darray'
        if out['type'] in _valid_types:
            out['subtype'] = out['type']
            out['type'] = 'scalar'
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
    def write_model_function_call(cls, model_function, flag_var,
                                  inputs, outputs, **kwargs):
        r"""Write lines necessary to call the model function.

        Args:
            model_function (str): Handle of the model function that should be
                called.
            flag_var (str): Name of variable that should be used as a flag.
            inputs (list): List of dictionaries describing inputs to the model.
            outputs (list): List of dictionaries describing outputs from the model.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Lines required to carry out a call to a model function in
                this language.

        """
        new_inputs = copy.deepcopy(inputs)
        for x in new_inputs:
            for v in x['vars']:
                if v.get('allow_realloc', False):
                    v['name'] = '*' + v['name']
        return super(CModelDriver, cls).write_model_function_call(
            model_function, flag_var, new_inputs, outputs, **kwargs)
        
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
        return super(CModelDriver, cls).write_model_recv(channel, recv_var_str, **kwargs)
            
    @classmethod
    def write_initialize_oiter(cls, var, value=None, **kwargs):
        r"""Get the lines necessary to initialize an array for iteration
        output.

        Args:
            var (dict, str): Name or information dictionary for the variable
                being initialized.
            value (str, optional): Value that should be assigned to the
                variable.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: The lines initializing the variable.

        """
        value = '({type}*)realloc({name}, {length}*sizeof({type}))'.format(
            type=cls.get_native_type(**var['iter_datatype']),
            name=var['name'], length=var['iter_var']['end'])
        out = super(CModelDriver, cls).write_initialize_oiter(
            var, value=value, **kwargs)
        return out
    
    @classmethod
    def write_declaration(cls, var, **kwargs):
        r"""Return the lines required to declare a variable with a certain
        type.

        Args:
            var (dict, str): Name or information dictionary for the variable
                being declared.
            **kwargs: Addition keyword arguments are passed to the parent
                class's method.

        Returns:
            list: The lines declaring the variable.

        """
        if isinstance(var, str):  # pragma: no cover
            var = {'name': var}
        type_name = cls.get_native_type(**var)
        if var.get('allow_realloc', False):
            type_name += '*'
            var = dict(var, native_type=type_name)
        if (((type_name.endswith('*')
              or (type_name in ['bytes_t', 'string_t', 'unicode_t']))
             and (not type_name.startswith(('comm_t', 'dtype_t')))
             and (not (('length' in var.get('datatype', var))
                       or ('shape' in var.get('datatype', var)))))):
            kwargs.get('requires_freeing', []).append(var)
            kwargs.setdefault('value', 'NULL')
        elif var.get('is_length_var', False):
            kwargs.setdefault('value', '0')
        out = super(CModelDriver, cls).write_declaration(var, **kwargs)
        for k in ['length', 'ndim', 'shape']:
            if ((isinstance(var.get(k + '_var', None), dict)
                 and var[k + '_var'].get('dependent', False))):
                out += cls.write_declaration(var[k + '_var'])
        return out

    @classmethod
    def get_name_declare(cls, var):
        r"""Determine the name that should be used for declaration.

        Args:
            var (str, dict): Name of variable or dictionary of information.

        Returns:
            str: Modified name for declaration.

        """
        if isinstance(var, str):  # pragma: no cover
            return var
        assert(isinstance(var, dict))
        out = var['name']
        if 'length' in var.get('datatype', {}):
            out += '[%d]' % var['datatype']['length']
        elif 'shape' in var.get('datatype', {}):
            for s in var['datatype']['shape']:
                out += '[%d]' % s
        return out
        
    @classmethod
    def write_free(cls, var, **kwargs):
        r"""Return the lines required to free a variable with a certain type.

        Args:
            var (dict, str): Name or information dictionary for the variable
                being declared.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: The lines freeing the variable.

        """
        out = []
        if isinstance(var, str):  # pragma: no cover
            var = {'name': var}
        if ((isinstance(var.get('datatype', False), dict)
             and (('free_%s' % var['datatype']['type'])
                  in cls.function_param))):
            if var.get('allow_realloc', False):
                out += super(CModelDriver, cls).write_free(
                    var, **kwargs)
                var = {'name': var['name']}
            else:
                var = dict(var, name=('&' + var['name']))
        out += super(CModelDriver, cls).write_free(var, **kwargs)
        return out
        
    @classmethod
    def prepare_variables(cls, vars_list, in_definition=False,
                          for_yggdrasil=False):
        r"""Concatenate a set of input variables such that it can be passed as a
        single string to the function_call parameter.

        Args:
            vars_list (list): List of variable dictionaries containing info
                (e.g. names) that should be used to prepare a string representing
                input/output to/from a function call.
            in_definition (bool, optional): If True, the returned sequence
                will be of the format required for specifying variables
                in a function definition. Defaults to False.
            for_yggdrasil (bool, optional): If True, the variables will be
                prepared in the formated expected by calls to yggdarsil
                send/recv methods. Defaults to False.

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
                if for_yggdrasil and x.get('is_length_var', False):
                    continue
                new_vars_list.append(x)
                if for_yggdrasil:
                    for k in ['length', 'ndim', 'shape']:
                        kvar = k + '_var'
                        if x.get(kvar, False):
                            if ((x['name'].startswith('*')
                                 or x['name'].startswith('&'))):
                                new_vars_list.append(
                                    dict(x[kvar],
                                         name=x['name'][0] + x[kvar]['name']))
                            else:
                                new_vars_list.append(x[kvar])
        if in_definition:
            new_vars_list2 = []
            for x in new_vars_list:
                if x['name'].startswith('*'):
                    name = '%s%s* %s' % tuple(
                        [cls.get_native_type(**x)]
                        + x['name'].rsplit('*', 1))
                else:
                    name = '%s %s' % (cls.get_native_type(**x), x['name'])
                new_var = dict(x, name=name)
                new_var['name'] = cls.get_name_declare(new_var)
                new_vars_list2.append(new_var)
            new_vars_list = new_vars_list2
        return super(CModelDriver, cls).prepare_variables(
            new_vars_list, in_definition=in_definition,
            for_yggdrasil=for_yggdrasil)
    
    @classmethod
    def prepare_output_variables(cls, vars_list, in_definition=False,
                                 in_inputs=False, for_yggdrasil=False):
        r"""Concatenate a set of output variables such that it can be passed as
        a single string to the function_call parameter.

        Args:
            vars_list (list): List of variable names to concatenate as output
                from a function call.
            in_definition (bool, optional): If True, the returned sequence
                will be of the format required for specifying output
                variables in a function definition. Defaults to False.
            in_inputs (bool, optional): If True, the output variables should
                be formated to be included as input variables. Defaults to
                False.
            for_yggdrasil (bool, optional): If True, the variables will be
                prepared in the formated expected by calls to yggdarsil
                send/recv methods. Defaults to False.

        Returns:
            str: Concatentated variables list.

        """
        if not in_inputs:
            # If the output is a True output and not passed as an input
            # parameter, then the output should not include the type
            # information that is added if in_definition is True.
            in_definition = False
        return super(CModelDriver, cls).prepare_output_variables(
            vars_list, in_definition=in_definition, in_inputs=in_inputs,
            for_yggdrasil=for_yggdrasil)

    @classmethod
    def write_print_output_var(cls, var, in_inputs=False, **kwargs):
        r"""Get the lines necessary to print an output variable in this
        language.

        Args:
            var (dict): Variable information.
            in_inputs (bool, optional): If True, the output variable
                is passed in as an input variable to be populated.
                Defaults to False.
            **kwargs: Additional keyword arguments are passed to write_print_var.

        Returns:
            list: Lines printing the specified variable.

        """
        if in_inputs and (cls.language != 'c++'):
            if isinstance(var, dict):
                var = dict(var, name='%s[0]' % var['name'])
            else:
                var = '%s[0]' % var
        return super(CModelDriver, cls).write_print_output_var(
            var, in_inputs=in_inputs, **kwargs)
        
    @classmethod
    def write_function_def(cls, function_name, dont_add_lengths=False,
                           use_length_prefix=False, **kwargs):
        r"""Write a function definition.

        Args:
            function_name (str): Name fo the function being defined.
            dont_add_lengths (bool, optional): If True, length variables
                are not added for arrays. Defaults to False.
            use_length_prefix (bool, optional): If True and length variables
                are added, they will be named using prefixes. Otherwise,
                suffixes will be used. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Lines completing the function call.

        Raises:
            ValueError: If outputs_in_inputs is not True and more than
                one output variable is specified.

        """
        if not dont_add_lengths:
            for io in ['input', 'output']:
                if io + '_var' in kwargs:
                    io_var = cls.parse_var_definition(
                        io + 's', kwargs.pop(io + '_var'))
                else:
                    io_var = kwargs.get(io + 's', [])
                for x in io_var:
                    if use_length_prefix:
                        v_length = 'length_' + x['name']
                        v_ndim = 'ndim_' + x['name']
                        v_shape = 'shape_' + x['name']
                    else:
                        v_length = x['name'] + '_length'
                        v_ndim = x['name'] + '_ndim'
                        v_shape = x['name'] + '_shape'
                    if x.get('is_length_var', False):
                        continue
                    if cls.requires_length_var(x):
                        if not x.get('length_var', False):
                            x['length_var'] = {
                                'name': v_length,
                                'datatype': {'type': 'uint',
                                             'precision': 64},
                                'is_length_var': True}
                            io_var.append(x['length_var'])
                    elif cls.requires_shape_var(x):
                        if not x.get('ndim_var', False):
                            x['ndim_var'] = {
                                'name': v_ndim,
                                'datatype': {'type': 'uint',
                                             'precision': 64},
                                'is_length_var': True}
                            io_var.append(x['ndim_var'])
                        if not x.get('shape_var', False):
                            x['shape_var'] = {
                                'name': v_shape,
                                'datatype': {'type': '1darray',
                                             'subtype': 'uint',
                                             'precision': 64},
                                'is_length_var': True}
                            io_var.append(x['shape_var'])
                        length_var = {
                            'name': v_length,
                            'datatype': {'type': 'uint',
                                         'precision': 64},
                            'is_length_var': True}
                        kwargs['function_contents'] = (
                            cls.write_declaration(length_var)
                            + kwargs.get('function_contents', []))
                kwargs[io + 's'] = io_var
        output_type = None
        if kwargs.get('outputs_in_inputs', False):
            output_type = cls.get_native_type(datatype='flag')
        else:
            if 'output_var' in kwargs:
                kwargs['outputs'] = cls.parse_var_definition(
                    'outputs', kwargs.pop('output_var'))
            outputs = kwargs.get('outputs', [])
            nout = len(outputs)
            if nout == 0:
                output_type = 'void'
            elif nout == 1:
                output_type = cls.get_native_type(**(outputs[0]))
            else:  # pragma: debug
                raise ValueError("C does not support more than one "
                                 "output variable.")
        kwargs['output_type'] = output_type
        return super(CModelDriver, cls).write_function_def(
            function_name, **kwargs)

    @classmethod
    def write_assign_to_output(cls, dst_var, src_var,
                               outputs_in_inputs=False,
                               dont_add_lengths=False,
                               use_length_prefix=False, **kwargs):
        r"""Write lines assigning a value to an output variable.

        Args:
            dst_var (str, dict): Name or information dictionary for
                variable being assigned to.
            src_var (str, dict): Name or information dictionary for
                value being assigned to dst_var.
            outputs_in_inputs (bool, optional): If True, outputs are passed
                as input parameters. In some languages, this means that a
                pointer or reference is passed (e.g. C) and so the assignment
                should be to the memory indicated rather than the variable.
                Defaults to False.
            dont_add_lengths (bool, optional): If True, length variables
                are not added for arrays. Defaults to False.
            use_length_prefix (bool, optional): If True and length variables
                are added, they will be named using prefixes. Otherwise,
                suffixes will be used. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Lines achieving assignment.

        """
        out = []
        if cls.requires_length_var(dst_var):
            src_var_length = None
            dst_var_length = None
            if isinstance(src_var, dict):
                src_var_length = src_var.get('length_var', None)
            if isinstance(dst_var, dict):
                dst_var_length = dst_var.get('length_var', None)
            if not dont_add_lengths:
                if src_var_length is None:
                    if use_length_prefix:
                        src_var_length = 'length_' + src_var['name']
                    else:
                        src_var_length = src_var['name'] + '_length'
                if dst_var_length is None:
                    if use_length_prefix:
                        dst_var_length = 'length_' + dst_var['name']
                    else:
                        dst_var_length = dst_var['name'] + '_length'
                out += cls.write_assign_to_output(
                    dst_var_length, src_var_length,
                    outputs_in_inputs=outputs_in_inputs)
            elif src_var_length is None:
                if ((dst_var['datatype']['type']
                     in ['1darray', 'ndarray'])):  # pragma: debug
                    raise RuntimeError("Length must be set in order "
                                       "to write array assignments.")
                elif (dst_var['datatype'].get('subtype', dst_var['datatype']['type'])
                      in ['bytes']):
                    src_var_length = '(strlen(%s)+1)' % src_var['name']
                else:
                    src_var_length = '(strlen4(%s)+1)' % src_var['name']
            src_var_dtype = cls.get_native_type(**src_var)
            if src_var_dtype in ['bytes_t', 'unicode_t', 'string_t']:
                src_var_dtype = 'char*'
            src_var_dtype = src_var_dtype.rsplit('*', 1)[0]
            out += cls.write_assign_to_output(
                dst_var['name'], 'value',
                outputs_in_inputs=outputs_in_inputs,
                replacement=('{name} = ({native_type}*)realloc({name}, '
                             '{N}*sizeof({native_type}));'),
                native_type=src_var_dtype, N=src_var_length)
            kwargs.update(copy=True, native_type=src_var_dtype,
                          N=src_var_length)
        elif cls.requires_shape_var(dst_var):
            if dont_add_lengths:  # pragma: debug
                raise RuntimeError("Shape must be set in order "
                                   "to write ND array assignments.")
            # Dimensions
            src_var_ndim = None
            dst_var_ndim = None
            if isinstance(src_var, dict):
                src_var_ndim = src_var.get('ndim_var', None)
            if isinstance(dst_var, dict):
                dst_var_ndim = dst_var.get('ndim_var', None)
            if src_var_ndim is None:
                if use_length_prefix:
                    src_var_ndim = 'ndim_' + src_var['name']
                else:
                    src_var_ndim = src_var['name'] + '_ndim'
            if dst_var_ndim is None:
                if use_length_prefix:
                    dst_var_ndim = 'ndim_' + dst_var['name']
                else:
                    dst_var_ndim = dst_var['name'] + '_ndim'
            if isinstance(src_var_ndim, str):
                src_var_ndim = {'name': src_var_ndim,
                                'datatype': {'type': 'uint',
                                             'precision': 64}}
            if isinstance(dst_var_ndim, str):
                dst_var_ndim = {'name': dst_var_ndim,
                                'datatype': {'type': 'uint',
                                             'precision': 64}}

            out += cls.write_assign_to_output(
                dst_var_ndim, src_var_ndim,
                outputs_in_inputs=outputs_in_inputs)
            # Shape
            src_var_shape = None
            dst_var_shape = None
            if isinstance(src_var, dict):
                src_var_shape = src_var.get('shape_var', None)
            if isinstance(dst_var, dict):
                dst_var_shape = dst_var.get('shape_var', None)
            if src_var_shape is None:
                if use_length_prefix:
                    src_var_shape = 'shape_' + src_var['name']
                else:
                    src_var_shape = src_var['name'] + '_shape'
            if dst_var_shape is None:
                if use_length_prefix:
                    dst_var_shape = 'shape_' + dst_var['name']
                else:
                    dst_var_shape = dst_var['name'] + '_shape'
            if isinstance(src_var_shape, str):
                src_var_shape = {'name': src_var_shape,
                                 'datatype': {'type': '1darray',
                                              'subtype': 'uint',
                                              'precision': 64},
                                 'length_var': src_var_ndim['name']}
            if isinstance(dst_var_shape, str):
                dst_var_shape = {'name': dst_var_shape,
                                 'datatype': {'type': '1darray',
                                              'subtype': 'uint',
                                              'precision': 64},
                                 'length_var': dst_var_ndim['name']}
            out += cls.write_assign_to_output(
                dst_var_shape, src_var_shape,
                outputs_in_inputs=outputs_in_inputs,
                dont_add_lengths=True)
            src_var_dtype = cls.get_native_type(**src_var).rsplit('*', 1)[0]
            if use_length_prefix:
                src_var_length = 'length_' + src_var['name']
            else:
                src_var_length = src_var['name'] + '_length'
            out += (('{length} = 1;\n'
                     'size_t cdim;\n'
                     'for (cdim = 0; cdim < {ndim}; cdim++) {{\n'
                     '  {length} = {length}*{shape}[cdim];\n'
                     '}}\n').format(length=src_var_length,
                                    ndim=src_var_ndim['name'],
                                    shape=src_var_shape['name'])).splitlines()
            out += cls.write_assign_to_output(
                dst_var['name'], 'value',
                outputs_in_inputs=outputs_in_inputs,
                replacement=('{name} = ({native_type}*)realloc({name}, '
                             '{N}*sizeof({native_type}));'),
                native_type=src_var_dtype, N=src_var_length)
            kwargs.update(copy=True, native_type=src_var_dtype,
                          N=src_var_length)
        elif isinstance(dst_var, dict):
            if 'shape' in dst_var.get('datatype', {}):
                nele = 1
                for s in dst_var['datatype']['shape']:
                    nele *= s
                kwargs.update(copy=True, N=nele,
                              native_type=dst_var['datatype']['subtype'])
            elif 'length' in dst_var.get('datatype', {}):
                kwargs.update(copy=True, N=dst_var['datatype']['length'],
                              native_type=dst_var['datatype']['subtype'])
        if outputs_in_inputs and (cls.language != 'c++'):
            if isinstance(dst_var, dict):
                dst_var = dict(dst_var,
                               name='%s[0]' % dst_var['name'])
            else:
                dst_var = '%s[0]' % dst_var
        out += super(CModelDriver, cls).write_assign_to_output(
            dst_var, src_var, outputs_in_inputs=outputs_in_inputs,
            **kwargs)
        return out
