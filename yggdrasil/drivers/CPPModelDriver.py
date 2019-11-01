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
        print_any='std::cout << {object} << std::endl << std::flush;',
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
            r'(?:return +(?P<flag_var>.+?)?;(?:.*?\n?)*?\}})'
            r'|(?:\}})'),
        outputs_def_regex=(
            r'\s*(?P<native_type>(?:[^\s])+)(\s+)?'
            r'(\()?(?P<ref>&)(?(1)(?:\s*)|(?:\s+))'
            r'(?P<name>.+?)(?(2)(?:\)|(?:)))(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?'))
    include_arg_count = True
    include_channel_obj = False
    
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
    def input2output(cls, var):
        r"""Perform conversion necessary to turn a variable extracted from a
        function definition from an input to an output.

        Args:
            var (dict): Variable definition.

        Returns:
            dict: Updated variable definition.

        """
        if var['name'].startswith('&'):
            var['name'] = var['name'][1:]
        elif var['native_type'].endswith('&'):
            var['native_type'] = var['native_type'][:-1]
        else:
            return super(CPPModelDriver, cls).input2output(var)
        return super(CModelDriver, cls).input2output(var)

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
        if in_inputs:
            if in_definition:
                vars_list = [dict(y, name='&' + y['name'])
                             for y in vars_list]
                for y in vars_list:
                    if ((('shape' in y.get('datatype', {}))
                         or ('length' in y.get('datatype', {})))):
                        y['name'] = '(%s)' % y['name']
            else:
                vars_list = copy.deepcopy(vars_list)
                for y in vars_list:
                    if not (y.get('ref', False)
                            or (for_yggdrasil
                                and (y.get('is_length_var', False)))):
                        y['name'] = '&' + y['name']
        else:
            # If the output is a True output and not passed as an input
            # parameter, then the output should not include the type
            # information that is added if in_definition is True.
            in_definition = False
        return super(CModelDriver, cls).prepare_output_variables(
            vars_list, in_definition=in_definition, in_inputs=in_inputs,
            for_yggdrasil=for_yggdrasil)
