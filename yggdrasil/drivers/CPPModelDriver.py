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
    function_param = dict(
        CModelDriver.function_param,
        input='YggInput {channel}(\"{channel_name}\", {channel_type});',
        output='YggOutput {channel}(\"{channel_name}\", {channel_type});',
        recv_heap='{channel}.recvRealloc',
        recv_stack='{channel}.recv',
        recv_function='{channel}.recvRealloc',
        send_function='{channel}.send',
        exec_prefix=('#include <iostream>\n'
                     '#include <exception>\n'),
        print_generic='std::cout << {object} << std::endl << std::flush;',
        error='throw \"{error_msg}\";',
        try_begin='try {',
        try_error_type='const std::exception&',
        try_except='}} catch ({error_type} {error_var}) {{',
        function_def_regex=(
            r'(?P<flag_type>.+?)\s*{function_name}\s*'
            r'\((?P<inputs>(?:[^{{&])*?)'
            r'(?:,\s*(?P<outputs>'
            r'(?:\s*(?:[^\s])+(?:\s+)(?:\()?&(?:[^{{])+)+'
            r'))?\)\s*\{{'
            r'(?P<body>(?:.*?\n?)*?)'
            r'(?:(?:return +(?P<flag_var>.+?)?;(?:.*?\n?)*?\}})'
            r'|(?:\}}))'),
        outputs_def_regex=(
            r'\s*(?P<native_type>(?:[^\s])+)(\s+)?'
            r'(\()?(?P<ref>&)(?(1)(?:\s*)|(?:\s+))'
            r'(?P<name>.+?)(?(2)(?:\)|(?:)))(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?'))
    include_arg_count = True
    include_channel_obj = False
    
    @staticmethod
    def after_registration(cls, **kwargs):
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
        CModelDriver.after_registration(cls, **kwargs)
        if kwargs.get('second_pass', False):
            return
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

    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CPPModelDriver, self).set_env(**kwargs)
        out = CModelDriver.update_ld_library_path(out)
        return out
        
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
                out = dict(out, name='&' + out['name'])
                if ((('shape' in out.get('datatype', {}))
                     or ('length' in out.get('datatype', {})))):
                    out['name'] = '(%s)' % out['name']
            else:
                if not (out.get('ref', False)
                        or out.get('is_length_var', False)):
                    out = dict(out, name='&' + out['name'])
        return out
