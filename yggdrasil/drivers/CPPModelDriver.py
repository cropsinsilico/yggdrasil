import os
import copy
import logging
from yggdrasil import platform
from yggdrasil.drivers.CModelDriver import (
    CCompilerBase, CModelDriver, GCCCompiler, ClangCompiler, MSVCCompiler,
    GCCLinker, ClangLinker, MSVCLinker)
logger = logging.getLogger(__name__)


class CPPCompilerBase(CCompilerBase):
    r"""Base class for C++ compilers."""
    languages = ['c++']
    default_executable_env = 'CXX'
    default_flags_env = 'CXXFLAGS'
    cpp_std = 'c++14'
    search_path_flags = ['-E', '-v', '-xc++', '/dev/null']
    default_linker = None
    default_executable = None

    @classmethod
    def find_standard_flag(cls, flags):
        r"""Locate the standard flag in a list of flags.

        Args:
            flags (list): Compilation flags.

        Returns:
            int: Index of the standard flag. -1 if not present.

        """
        for i, a in enumerate(flags):
            if a.startswith('-std='):
                return i
        return -1

    @classmethod
    def handle_standard_flag(cls, flags, skip_standard_flag=False):
        r"""Add or remove standard flag from a list of flags.

        Args:
            flags (list): Compilation flags.
            skip_standard_flag (bool, optional): If True, the C++
                standard flag will not be added. Defaults to False.

        """
        std_flag_idx = cls.find_standard_flag(flags)
        if skip_standard_flag and (std_flag_idx != -1):
            del flags[std_flag_idx]
        elif (not skip_standard_flag) and (std_flag_idx == -1):
            flags.append('-std=%s' % cls.cpp_std)
        return flags


class GPPCompiler(CPPCompilerBase, GCCCompiler):
    r"""Interface class for G++ compiler/linker."""
    toolname = 'g++'
    aliases = ['gnu-c++']
    default_linker = 'g++'
    is_linker = False

    @classmethod
    def get_flags(cls, skip_standard_flag=False, **kwargs):
        r"""Get a list of compiler flags.

        Args:
            skip_standard_flag (bool, optional): If True, the C++ standard flag
                will not be added. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Compiler flags.

        """
        out = super(GPPCompiler, cls).get_flags(**kwargs)
        # Add/remove standard library flag
        out = cls.handle_standard_flag(out, skip_standard_flag)
        return out


class ClangPPCompiler(CPPCompilerBase, ClangCompiler):
    r"""Interface class for clang++ compiler."""
    toolname = 'clang++'
    default_linker = 'clang++'
    # Set to False since ClangLinker has its own class to handle
    # conflict between versions of clang and ld.
    is_linker = False

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        if platform._is_win:  # pragma: windows
            cls.default_executable = 'clang'
        CPPCompilerBase.before_registration(cls)

    @classmethod
    def get_flags(cls, skip_standard_flag=False, **kwargs):
        r"""Get a list of compiler flags.

        Args:
            skip_standard_flag (bool, optional): If True, the C++ standard flag
                will not be added. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Compiler flags.

        """
        out = super(ClangPPCompiler, cls).get_flags(**kwargs)
        # Add/remove standard library flag
        out = cls.handle_standard_flag(out, skip_standard_flag)
        return out
        
    @classmethod
    def get_executable_command(cls, args, skip_flags=False, unused_kwargs=None,
                               **kwargs):
        r"""Determine the command required to run the tool using the specified
        arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool. If
                skip_flags is False, these are treated as input files that will
                be used by the tool.
            **kwargs: Additional keyword arguments will be passed to the parent
                class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        if platform._is_win or platform._is_mac:
            for a in args:
                if a.endswith('.c'):
                    kwargs['skip_standard_flag'] = True
                    break
        return super(ClangPPCompiler, cls).get_executable_command(args, **kwargs)


class MSVCPPCompiler(CPPCompilerBase, MSVCCompiler):
    r"""Inteface class for MSVC compiler when compiling C++."""
    toolname = 'cl++'
    default_linker = MSVCCompiler.default_linker
    default_archiver = MSVCCompiler.default_archiver
    default_executable = MSVCCompiler.default_executable
    search_path_flags = None
    dont_create_linker = True
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        return MSVCCompiler.before_registration(cls)


class GPPLinker(GCCLinker):
    r"""Interface class for clang++ linker (calls to ld)."""
    toolname = GPPCompiler.toolname
    aliases = GPPCompiler.aliases
    languages = GPPCompiler.languages
    default_executable = GPPCompiler.default_executable
    toolset = GPPCompiler.toolset


class ClangPPLinker(ClangLinker):
    r"""Interface class for clang++ linker (calls to ld)."""
    toolname = ClangPPCompiler.toolname
    aliases = ClangPPCompiler.aliases
    languages = ClangPPCompiler.languages
    default_executable = ClangPPCompiler.default_executable
    toolset = ClangPPCompiler.toolset


class MSVCPPLinker(MSVCLinker):
    r"""Interface class for MSVC C++ linker."""
    toolname = 'LINK++'
    languages = MSVCPPCompiler.languages


class CPPModelDriver(CModelDriver):
    r"""Class for running C++ models."""
    _schema_subtype_description = ('Model is written in C++.')
    language = 'c++'
    language_ext = ['.cpp', '.CPP', '.cxx', '.C', '.c++', '.cc', '.cp', '.tcc',
                    '.hpp', '.HPP', '.hxx', '.H', '.h++', '.hh', '.hp', '.h']
    language_aliases = ['cpp', 'cxx']
    base_languages = ['c']
    interface_library = 'ygg++'
    # To prevent inheritance
    default_compiler = None
    default_linker = None
    interface_map = {
        'import': '#include "YggInterface.hpp"',
        'input': 'YggInput {channel_obj}("{channel_name}")',
        'output': 'YggOutput {channel_obj}("{channel_name}")',
        'server': (
            'YggRpcServer {channel_obj}("{channel_name}", '
            '{datatype_in}, {datatype_out})'),
        'client': (
            'YggRpcClient {channel_obj}("{channel_name}", '
            '{datatype_out}, {datatype_in})'),
        'timesync': 'YggTimesync {channel_obj}("{channel_name}", "{time_units}")',
        'send': 'flag = {channel_obj}.send({nargs}, {outputs})',
        'recv': 'flag = {channel_obj}.recv({nargs}, {input_refs})',
        'call': 'flag = {channel_obj}.call({nargs}, {outputs}, {input_refs})',
    }
    type_map = dict(
        CModelDriver.type_map,
        array='rapidjson::Document',
        object='rapidjson::Document',
        any='rapidjson::Document',
        schema='rapidjson::Document',
        ply='rapidjson::Ply',
        obj='rapidjson::ObjWavefront')
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
        error='throw \"{error_msg}\";',
        try_begin='try {',
        try_error_type='const std::exception&',
        try_except='}} catch ({error_type} {error_var}) {{',
        function_def_regex=(
            r'(?P<flag_type>.+?)\s*{function_name}\s*'
            r'\(\s*(?P<inputs>'
            r'(?:(?:const\s+[^{{\&]+\s+\&[^{{\&]+)|(?:[^{{\&]+))'
            r'(?:\s*,\s*(?:const\s+[^{{\&]+\s+\&[^{{\&]+)|(?:[^{{\&]+))*?'
            r')'
            r'(?:,\s*(?P<outputs>'
            r'(?:\s*(?:[^\s\&]+)'
            r'(?:(?:\&\s+)|(?:\s+(?:\()?\&))'
            r'(?:[^{{])+)+))?\)\s*\{{'
            r'(?P<body>(?:.*?\n?)*?)'
            r'(?:(?:return +(?P<flag_var>.+?)?;(?:.*?\n?)*?\}})'
            r'|(?:\}}))'),
        inputs_def_regex=(
            r'\s*(?:const\s+)?(?P<native_type>(?:[^\s\&\<\*])+'
            r'(?:\<(?P<subtypes>\s*.+?(?:\s*,\s*.+?)*\s*)\>)?(\s+)?'
            r'(?P<ptr>\*+)?)(?:\s*\&)?'
            r'(?(ptr)(?(3)(?:\s*)|(?:\s+)))'
            r'(\((?P<name_ptr>\*+)?)?(?P<name>[^\&\>\*]+?)(?(5)(?:\)))'
            r'(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?'),
        outputs_def_regex=(
            r'\s*(?P<native_type>(?:[^\s])+)(\s+)?'
            r'(\()?(?P<ref>\&)(?(1)(?:\s*)|(?:\s+))'
            r'(?P<name>.+?)(?(2)(?:\)|(?:)))(?P<shape>(?:\[.+?\])+)?\s*(?:,|$)(?:\n)?'),
        vector_regex=r'(?:std\:\:)?vector\<\s*(?P<type>.*)\s*\>')
    include_arg_count = True
    include_channel_obj = False
    dont_declare_channel = True
    _document_types = ['array', 'object', 'schema', 'any']
    _cpp_class_types = ['ply', 'obj']
    
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
        for k in cls._document_types + cls._cpp_class_types:
            cls.function_param.pop(f'init_{k}', None)
            cls.function_param.pop(f'print_{k}', None)
            cls.function_param.pop(f'copy_{k}', None)
        for k in cls._document_types:
            cls.function_param[f'print_{k}'] = (
                'std::cout << document2string({object}) << std::endl;')
            cls.function_param[f'copy_{k}'] = (
                '{name}.CopyFrom({value}, {name}.GetAllocator(), true);')
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
        internal_libs[cls.interface_library]['language'] = cls.language
        cls.internal_libraries = internal_libs

    @classmethod
    def set_env_class(cls, **kwargs):
        r"""Set environment variables that are instance independent.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and update_ld_library_path.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CPPModelDriver, cls).set_env_class(**kwargs)
        out = CModelDriver.update_ld_library_path(out, **kwargs)
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
    def add_extra_vars(cls, direction, x):
        r"""Add extra variables required for communication.
        
        Args:
            direction (str): Direction of channel ('input' or 'output').
            x (dict): Dictionary describing the variable.
        
        """
        super(CPPModelDriver, cls).add_extra_vars(direction, x)
        if cls.is_std_class(x):
            x['extra_vars']['std'] = {
                'name': f'std_{direction}',
                'datatype': {'type': 'any'},
                'use_generic': True}
            
    @classmethod
    def requires_length_var(cls, var):
        r"""Determine if a variable requires a separate length variable.

        Args:
            var (dict): Dictionary of variable properties.

        Returns:
            bool: True if a length variable is required, False otherwise.

        """
        if cls.is_std_class(var):
            return False
        return super(CPPModelDriver, cls).requires_length_var(var)
        
    @classmethod
    def is_cpp_class(cls, var):
        r"""Determine if a variable uses a C++ class.

        Args:
            var (dict): Variable.

        Returns:
            bool: True if it is a C++ class, False otherwise.

        """
        return (isinstance(var, dict)
                and (var.get('datatype', {}).get('type', None)
                     in ['obj', 'ply', 'any', 'schema',
                         'array', 'object']
                     or ('::' in var.get('native_type', '')
                         and not var.get('ptr', ''))))

    @classmethod
    def is_std_class(cls, var):
        r"""Determine if a variable utilizing a C++ stdlib class.

        Args:
           var (dict): Variable.

        Returns:
            bool: True if var is a C++ stdlib class, False otherwise.
        
        """
        return (isinstance(var, dict)
                and var.get('native_type', '').startswith(
                    ('std::string', 'std::vector', 'std::map')))

    @classmethod
    def allows_realloc(cls, var):
        r"""Determine if a variable allows the receive call to perform
        realloc.

        Args:
            var (dict): Dictionary of variable properties.

        Returns:
            bool: True if the variable allows realloc, False otherwise.

        """
        if cls.is_cpp_class(var):
            return False
        return super(CPPModelDriver, cls).allows_realloc(var)
        
    @classmethod
    def prepare_input_variables(cls, vars_list, in_definition=False,
                                for_yggdrasil=False):
        r"""Concatenate a set of input variables such that it can be passed as a
        single string to the function_call parameter.

        Args:
            vars_list (list): List of variable dictionaries containing info
                (e.g. names) that should be used to prepare a string representing
                input to a function call.
            in_definition (bool, optional): If True, the returned sequence
                will be of the format required for specifying input
                variables in a function definition. Defaults to False.
            for_yggdrasil (bool, optional): If True, the variables will be
                prepared in the formated expected by calls to yggdarsil
                send/recv methods. Defaults to False.

        Returns:
            str: Concatentated variables list.

        """
        if in_definition:
            new_vars_list = []
            for x in vars_list:
                if isinstance(x, dict) and cls.is_cpp_class(x):
                    new_vars_list.append(dict(x, name=f"&{x['name']}",
                                              const=True))
                else:
                    new_vars_list.append(x)
            vars_list = new_vars_list
        return super(CPPModelDriver, cls).prepare_input_variables(
            vars_list, in_definition=in_definition,
            for_yggdrasil=for_yggdrasil)

    @classmethod
    def write_doc2vars(cls, channel, std, var_list):
        r"""Generate the lines of code required to unpack a document
        into a list of variables.

        Args:
            channel (str): Name of variable that the channel that the
                document was received from is stored in.
            std (dict): Variable information for the received document.
            var_list (list): Variables that the document should be
                unpacked into.

        """
        nVar = sum([(not v.get('is_length_var', False))
                    for v in var_list])
        out = cls.write_if_block(
            f"(!({std['name']}.IsArray() && "
            f"({std['name']}.Size() == {nVar})))",
            [cls.format_function_param(
                'error', error_msg=("Received document does not match "
                                    "variables"))])
        i = 0
        for v in var_list:
            if not v.get('is_length_var', False):
                v_str = cls.prepare_input_variables(
                    [v], for_yggdrasil=True)
                out += [
                    f"{std['name']}[{i}].Get({v_str});"
                ]
                i += 1
        return out

    @classmethod
    def write_vars2doc(cls, channel, var_list, std):
        r"""Generate the lines of code required to pack a list of
        variables into a document.

        Args:
            channel (str): Name of variable that the channel that will be
                used to send the document is stored in.
            var_list (list): Variables that should be packed into the
                document.
            std (dict): Variable information for the document that will be
                generated.

        """
        out = [f"{std['name']}.SetArray();"]
        for v in var_list:
            if not v.get('is_length_var', False):
                v_str = cls.prepare_input_variables([v], for_yggdrasil=True)
                out += [
                    "{",
                    "  rapidjson::Value tmp;",
                    f"  tmp.Set({v_str}, {std['name']}.GetAllocator());",
                    f"  {std['name']}.PushBack(tmp,"
                    f" {std['name']}.GetAllocator());",
                    "}"
                ]
        return out

    @classmethod
    def write_model_recv(cls, channel, recv_var, **kwargs):
        r"""Write a model receive call include checking the return flag.

        Args:
            channel (str): Name of variable that the channel being received
                from was stored in.
            recv_var (dict, list): Information of one or more variables that
                receieved information should be stored in.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Lines required to carry out a receive call in this language.

        """
        out_after = []
        if not isinstance(recv_var, str):
            recv_var_par = cls.channels2vars(recv_var)
            std_var = None
            for v in recv_var_par:
                std_var = v['extra_vars'].get('std', None)
                if std_var:
                    break
            if std_var:
                kwargs['alt_recv_function'] = '{channel}.recvVar'
                kwargs['include_arg_count'] = False
                if len(recv_var_par) == 1:
                    recv_var = v['name']
                else:
                    new_recv_var_par = [std_var]
                    out_after += cls.write_doc2vars(
                        channel, std_var, recv_var_par)
                    recv_var_par = new_recv_var_par
                    recv_var = std_var['name']
        out = super(CPPModelDriver, cls).write_model_recv(
            channel, recv_var, **kwargs)
        return out + out_after

    @classmethod
    def write_model_send(cls, channel, send_var, **kwargs):
        r"""Write a model send call include checking the return flag.

        Args:
            channel (str): Name of variable that the channel being sent to
                was stored in.
            send_var (dict, list): Information on one or more variables
                containing information that will be sent.
            flag_var (str, optional): Name of flag variable that the flag
                should be stored in. Defaults to 'flag',
            allow_failure (bool, optional): If True, the returned lines will
                call a break if the flag is False. Otherwise, the returned
                lines will issue an error. Defaults to False.

        Returns:
            list: Lines required to carry out a send call in this language.

        """
        send_var_str = send_var
        out_before = []
        if not isinstance(send_var, str):
            send_var_par = cls.channels2vars(send_var)
            std_var = None
            for v in send_var_par:
                std_var = v['extra_vars'].get('std', None)
                if std_var:
                    break
            new_send_var_par = []
            if std_var:
                kwargs['alt_send_function'] = '{channel}.sendVar'
                kwargs['include_arg_count'] = False
                if len(send_var_par) == 1:
                    new_send_var_par.append(send_var_par[0])
                else:
                    new_send_var_par.append(std_var)
                    out_before += cls.write_vars2doc(
                        channel, send_var_par, std_var)
            else:
                for v in send_var_par:
                    if cls.is_cpp_class(v):
                        new_send_var_par.append(
                            dict(v, name=f"&{v['name']}"))
                    else:
                        new_send_var_par.append(v)
            send_var_par = new_send_var_par
            send_var_str = cls.prepare_input_variables(
                send_var_par, for_yggdrasil=True)
        out = super(CPPModelDriver, cls).write_model_send(
            channel, send_var_str, **kwargs)
        return out_before + out
    
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

    @classmethod
    def get_json_type(cls, native_type):
        r"""Get the JSON type from the native language type.

        Args:
            native_type (str): The native language type.

        Returns:
            str, dict: The JSON type.

        """
        if '<' in native_type:
            base, subtypes = native_type.split('<', 1)
            subtypes = subtypes.rsplit('>', 1)[0]
            subtypes = cls.split_variables(subtypes)
            if base == 'std::vector':
                assert len(subtypes) == 1
                items = cls.get_json_type(subtypes[0])
                assert items['type'] == 'scalar'
                out = items
                out['type'] = '1darray'
            elif base == 'std::map':
                assert len(subtypes) == 2
                items = [cls.get_json_type(x) for x in subtypes]
                if items[0]['type'] != 'string':  # pragma: debug
                    raise ValueError("std::map with non-string keys not "
                                     "currently supported")
                out = {'type': 'object',
                       'additionalProperties': items[1]}
            else:  # pragma: debug
                raise ValueError(f"Template class '{base}' not "
                                 f"currently supported")
        elif 'std::string' in native_type:
            out = super(CPPModelDriver, cls).get_json_type(
                native_type.replace('std::string', 'char*'))
        else:
            return super(CPPModelDriver, cls).get_json_type(native_type)
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        from yggdrasil import tools
        out = super(CPPModelDriver, cls).get_testing_options(**kwargs)
        out['deps'] = ["cmake",
                       {"package_manager": "pip", "package": "pyyaml",
                        "arguments": "-v"},
                       {"package": "cmake", "arguments": "-v"}]
        if platform._is_win:  # pragma: windows
            if not tools.get_conda_prefix():
                out['deps'].append({"package_manager": "vcpkg",
                                    "package": "czmq"})
            else:
                out['deps'].append('doxygen')
        out['write_try_except_kwargs'] = {'error_type': '...'}
        # out['kwargs'].setdefault('compiler_flags', [])
        # out['kwargs']['compiler_flags'].append('-std=c++11')
        return out
