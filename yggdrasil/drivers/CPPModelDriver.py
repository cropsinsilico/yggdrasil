import os
import copy
from yggdrasil import platform
from yggdrasil.drivers.CModelDriver import (
    CCompilerBase, CModelDriver, GCCCompiler, ClangCompiler)
from yggdrasil.schema import register_component


class CPPCompilerBase(CCompilerBase):
    r"""Base class for C++ compilers."""
    languages = ['c++']
    default_executable_env = 'CXX'
    default_executable_flags_env = 'CXXFLAGS'
    cpp_std = 'c++11'
    search_path_flags = ['-E', '-v', '-xc++', '/dev/null']
    default_linker = None
    default_executable = None

    @classmethod
    def get_flags(cls, **kwargs):
        r"""Get a list of compiler flags.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Compiler flags.

        """
        out = super(CCompilerBase, cls).get_flags(**kwargs)
        # Add standard library flag
        std_flag = None
        for i, a in enumerate(out):
            if a.startswith('-std='):
                std_flag = i
                break
        if std_flag is None:
            out.append('-std=%s' % cls.cpp_std)
        return out
    

class GPPCompiler(CPPCompilerBase, GCCCompiler):
    r"""Interface class for G++ compiler/linker."""
    name = 'g++'


class ClangPPCompiler(CPPCompilerBase, ClangCompiler):
    r"""clang++ compiler on Apple Mac OS."""
    name = 'clang++'


@register_component
class CPPModelDriver(CModelDriver):
    r"""Class for running C++ models."""
                
    language = 'c++'
    language_ext = ['.cpp', '.CPP', '.cxx', '.C', '.c++', '.cc', '.cp', '.tcc',
                    '.hpp', '.HPP', '.hxx', '.H', '.h++', '.hh', '.hp', '.h']
    language_aliases = ['cpp']
    base_languages = ['c']
    interface_library = 'ygg++'
    # To prevent inheritance
    default_compiler = None
    default_linker = None
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        if platform._is_mac and (cls.default_compiler is None):
            cls.default_compiler = 'clang++'
        CModelDriver.before_registration(cls)
        internal_libs = copy.deepcopy(cls.internal_libraries)
        internal_libs[cls.interface_library] = internal_libs.pop(
            CModelDriver.interface_library)
        internal_libs[cls.interface_library]['source'] = os.path.splitext(
            internal_libs[cls.interface_library]['source'])[0] + cls.language_ext[0]
        cls.internal_libraries = internal_libs
