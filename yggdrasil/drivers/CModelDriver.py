import os
import copy
from collections import OrderedDict
from yggdrasil import platform, tools
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, ArchiverBase)


class CCompilerBase(CompilerBase):
    r"""Base class for C compilers."""
    languages = ['c']
    default_executable_env = 'CC'
    # TODO: Additional flags environment variables?
    default_executable_flags_env = 'CFLAGS'
    default_flags = ['-g', '-Wall']
    # GCC & CLANG have similar call patterns
    linker_attributes = {'default_executable_flags_env': 'LDFLAGS'}
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
    

class GCCCompiler(CCompilerBase):
    r"""Interface class for gcc compiler/linker."""
    name = 'gcc'
    platforms = ['MacOS', 'Linux', 'Windows']
    default_archiver = 'ar'


class ClangCompiler(CCompilerBase):
    r"""clang compiler on Apple Mac OS."""
    name = 'clang'
    platforms = ['MacOS']
    default_archiver = 'libtool'


class MSVCCompiler(CCompilerBase):
    r"""Microsoft Visual Studio C Compiler."""
    # TODO: This class dosn't check the CXX and CXXFLAGS environment variables
    # for C++ currently because it is a C subclass.
    name = 'cl'
    languages = ['c', 'c++']
    platforms = ['Windows']
    # TODO: Currently everything compiled as C++ on windows to allow use
    # of complex types. Use '/TC' instead of '/TP' for strictly C
    default_flags = ['/W4', '/Zi', "/EHsc", '/TP',
                     "/nologo", "-D_CRT_SECURE_NO_WARNINGS"]
    output_key = '/Fo%s'
    output_first = True
    default_linker = 'LINK'
    default_archiver = 'LIB'
    linker_switch = '/link'
    search_path_env = 'INCLUDE'
    search_path_flags = None
    linker_attributes = dict(GCCCompiler.linker_attributes,
                             default_executable_flags_env=None,
                             output_key='/OUT:%s',
                             output_first=True,
                             output_first_library=False,
                             flag_options=OrderedDict(
                                 [('library_libs', ''),
                                  ('library_dirs', '/LIBPATH:%s')]),
                             shared_library_flag='/DLL',
                             search_path_env='LIB',
                             search_path_flags=None)

    
# C Archivers
class ARArchiver(ArchiverBase):
    r"""Archiver class for ar tool."""
    name = 'ar'
    languages = ['c', 'c++']
    default_executable_env = 'AR'
    static_library_flag = 'rcs'
    output_key = ''
    output_first_library = True


class LibtoolArchiver(ArchiverBase):
    r"""Archiver class for libtool tool."""
    name = 'libtool'
    languages = ['c', 'c++']
    default_executable_env = 'LIBTOOL'
    static_library_flag = '-static'  # This is the default
    

class MSVCArchiver(ArchiverBase):
    r"""Microsoft Visual Studio C Archiver."""
    name = 'LIB'
    languages = ['c', 'c++']
    platforms = ['Windows']
    static_library_flag = None
    output_key = '/OUT:%s'
    

_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')
_incl_seri = os.path.join(_top_dir, 'serialize')
_incl_comm = os.path.join(_top_dir, 'communication')


class CModelDriver(CompiledModelDriver):
    r"""Class for running C models."""

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
                'libtype': 'static',
                'language': 'c'},  # static added in before_registration
        'czmq': {'include': 'czmq.h',
                 'libtype': 'static',
                 'language': 'c'}}
    internal_libraries = {
        'ygg': {'source': 'YggInterface.c',
                'directory': _incl_interface,
                'linker_language': 'c++',  # Some dependencies are C++
                'internal_dependencies': ['datatypes', 'regex'],
                'external_dependencies': ['rapidjson'],
                'include_dirs': [_top_dir, _incl_io, _incl_comm, _incl_seri],
                'compiler_flags': []},
        'regex_win32': {'source': 'regex_win32.cpp',
                        'directory': os.path.join(_top_dir, 'regex'),
                        'language': 'c++',
                        'libtype': 'object',
                        'internal_dependencies': [],
                        'external_dependencies': []},
        'regex_posix': {'source': 'regex_posix.h',
                        'directory': os.path.join(_top_dir, 'regex'),
                        'language': 'c',
                        'libtype': 'header_only',
                        'internal_dependencies': [],
                        'external_dependencies': []},
        'datatypes': {'source': 'datatypes.cpp',
                      'directory': os.path.join(_top_dir, 'metaschema',
                                                'datatypes'),
                      'language': 'c++',
                      'libtype': 'object',
                      'internal_dependencies': ['regex'],
                      'external_dependencies': ['rapidjson'],
                      'include_dirs': []}}
    function_param = {
        'comment': '//',
        'indent': 2 * ' ',
        'block_end': '}',
        'if_begin': 'if ({cond}) {',
        'for_begin': ('for ({iter_var} = {iter_begin}; {iter_var} < {iter_end}; '
                      '{iter_var}++) {'),
        'while_begin': 'while ({cond}) {'}

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        if platform._is_mac and (cls.default_compiler is None):
            cls.default_compiler = 'clang'
        CompiledModelDriver.before_registration(cls)
        archiver = cls.get_tool('archiver')
        linker = cls.get_tool('linker')
        for x in ['zmq', 'czmq']:
            if x not in cls.external_libraries:
                continue
            libtype = cls.external_libraries[x]['libtype']
            if libtype == 'static':
                tool = archiver
            else:
                tool = linker
            cls.external_libraries[x][libtype] = tool.get_output_file(x)
        # Platform specific regex internal library
        if platform._is_win:  # pragma: windows
            regex_lib = cls.internal_libraries['regex_win32']
        else:
            regex_lib = cls.internal_libraries['regex_posix']
        cls.internal_libraries['regex'] = regex_lib
        # Platform specific internal library options
        if platform._is_win:  # pragma: windows
            cls.internal_libraries['datatypes']['include_dirs'] += [_top_dir]
        if platform._is_linux:
            for x in ['ygg', 'datatypes']:
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
        out = super(CModelDriver, cls).configure(cfg)
        # Change configuration to be directory containing include files
        rjlib = cfg.get(cls._language, 'rapidjson_include', None)
        if (rjlib is not None) and os.path.isfile(rjlib):
            cfg.set(cls._language, 'rapidjson_include',
                    os.path.dirname(os.path.dirname(rjlib)))
        return out
        
    def compile_model(self, **kwargs):
        r"""Compile model executable(s) and appends any products produced by
        the compilation that should be removed after the run is complete."""
        # Always link using C++ because the interface depends on wrapped C++
        # libraries in order to use rapidjson
        kwargs.setdefault('linker_language', 'c++')
        out = super(CModelDriver, self).compile_model(**kwargs)
        if platform._is_win:  # pragma: windows
            for x in copy.deepcopy(self.products):
                base = os.path.splitext(x)[0]
                self.products += [base + ext for ext in ['.ilk', '.pdb', '.obj']]
        return out
