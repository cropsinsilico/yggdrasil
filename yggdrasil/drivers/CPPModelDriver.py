import os
import copy
from yggdrasil import platform
from yggdrasil.drivers.CModelDriver import (
    CCompilerBase, CModelDriver, GCCCompiler, ClangCompiler)


class CPPCompilerBase(CCompilerBase):
    r"""Base class for C++ compilers."""
    languages = ['c++']
    default_executable_env = 'CXX'
    default_flags_env = 'CXXFLAGS'
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
    toolname = 'g++'


class ClangPPCompiler(CPPCompilerBase, ClangCompiler):
    r"""clang++ compiler on Apple Mac OS."""
    toolname = 'clang++'


class CPPModelDriver(CModelDriver):
    r"""Class for running C++ models."""
                
    _schema_subtype_description = ('Model is written in C++.')
    language = 'c++'
    language_ext = ['.cpp', '.CPP', '.cxx', '.C', '.c++', '.cc', '.cp', '.tcc',
                    '.hpp', '.HPP', '.hxx', '.H', '.h++', '.hh', '.hp', '.h']
    language_aliases = ['cpp']
    base_languages = ['c']
    interface_library = 'ygg++'
    # To prevent inheritance
    default_compiler = None
    default_linker = None
    type_map = dict(
        CModelDriver.type_map,
        array='std::vector<void*>',
        object='std::map<char*,void*>',
        schema='MetaschemaType')
    function_param = dict(
        CModelDriver.function_param,
        exec_prefix=('#include <iostream>\n'
                     '#include <exception>\n'),
        # print='std::cout << "{message}" << std::endl;',
        error='throw \"{error_msg}\";',
        try_begin='try {',
        try_error_type='const std::exception&',
        try_except='}} catch ({error_type} {error_var}) {{')
    
    @staticmethod
    def after_registration(cls):
        r"""Operations that should be performed to modify class attributes after
        registration."""
        if cls.default_compiler is None:
            if platform._is_linux:
                cls.default_compiler = 'g++'
            elif platform._is_mac:
                cls.default_compiler = 'clang++'
            elif platform._is_win:  # pragma: windows
                cls.default_compiler = 'cl'
        cls.function_param['print'] = 'std::cout << "{message}" << std::endl;'
        CModelDriver.after_registration(cls)
        internal_libs = copy.deepcopy(cls.internal_libraries)
        internal_libs[cls.interface_library] = internal_libs.pop(
            CModelDriver.interface_library)
        internal_libs[cls.interface_library]['source'] = os.path.join(
            cls.get_language_dir(),
            os.path.splitext(os.path.basename(
                internal_libs[cls.interface_library]['source']))[0]
            + cls.language_ext[0])
        internal_libs[cls.interface_library]['include_dirs'].append(
            cls.get_language_dir())
        cls.internal_libraries = internal_libs

    @classmethod
    def write_try_except(cls, try_contents, except_contents, error_var='e',
                         error_type=None, **kwargs):
        r"""Return the lines required to complete a try/except block.

        Args:
            try_contents (list): Lines of code that should be executed inside
                the try block.
            except_contents (list): Lines of code that should be executed inside
                the except block.
            error_var (str, optional): Name of variable where the caught error
                should be stored. Defaults to 'e'. If '...', the catch clause
                will catch all errors, but there will not be a name error.
            error_type (str, optional): Name of error type that should be caught.
                If not provided, defaults to None and will be set based on the
                class function_param entry for 'try_error_type'. If '...', the
                catch clause will catch all errors and error_var will be
                ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            Lines of code perfoming a try/except block.

        """
        if (error_type == '...') or (error_var == '...'):
            error_type = ''
            error_var = '...'
        kwargs.update(error_var=error_var, error_type=error_type)
        return super(CPPModelDriver, cls).write_try_except(
            try_contents, except_contents, **kwargs)
