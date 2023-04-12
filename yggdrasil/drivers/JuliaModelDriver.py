from yggdrasil import platform
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver


class JuliaModelDriver(InterpretedModelDriver):  # pragma: Julia
    r"""Class for running Julia models."""

    _schema_subtype_description = ('Model is written in Julia.')
    language = 'julia'
    language_ext = '.jl'
    base_languages = ['python']
    default_interpreter = 'julia'
    interface_library = 'Yggdrasil'
    interface_dependencies = ['PyCall', 'Unitful']
    type_map = {
        'int': 'Int',
        'float': 'Float',
        'string': 'String',
        'array': 'Array',
        'object': 'Dict{AbstractString,Any}',
        'boolean': 'Bool',
        'null': 'Nothing',
        'uint': 'Uint',
        'complex': 'Complex',
        'bytes': 'CodeUnits{UInt8,String}',
        'unicode': 'String',
        '1darray': 'Array{X}',
        'ndarray': 'Array{X}',
        'ply': 'PlyDict',
        'obj': 'ObjDict',
        'schema': 'Dict'}
    interface_map = {
        'import': 'import Yggdrasil: commtype',
        'input': 'Yggdrasil.YggInterface("YggInput", "{channel_name}")',
        'output': 'Yggdrasil.YggInterface("YggOutput", "{channel_name}")',
        'server': 'Yggdrasil.YggInterface("YggRpcServer", "{channel_name}")',
        'client': 'Yggdrasil.YggInterface("YggRpcClient", "{channel_name}")',
        'timesync': 'Yggdrasil.YggInterface("YggTimesync", "{channel_name}")',
        'send': 'flag = {channel_obj}.send({outputs})',
        'recv': 'flag, {inputs} = {channel_obj}.recv()',
        'call': 'flag, {inputs} = {channel_obj}.call({outputs})',
    }
    function_param = {
        'import_nofile': 'using {function}',
        'import': 'include("{filename}")',  # "{function}")',
        'istype': '{variable} isa {type}',
        'len': 'length({variable})',
        'index': '{variable}[{index}]',
        'first_index': 1,
        'interface': 'using {interface_library}',
        'input': ('{channel} = Yggdrasil.YggInterface(\"YggInput\", '
                  '\"{channel_name}\")'),
        'output': ('{channel} = Yggdrasil.YggInterface(\"YggOutput\", '
                   '\"{channel_name}\")'),
        'python_interface': ('{channel} = Yggdrasil.YggInterface('
                             '\"{python_interface}\", \"{channel_name}\")'),
        'python_interface_format': ('{channel} = Yggdrasil.YggInterface('
                                    '\"{python_interface}\", '
                                    '\"{channel_name}\", \"{format_str}\")'),
        'recv_function': '{channel}.recv',
        'send_function': '{channel}.send',
        'comment': '#',
        'true': 'true',
        'false': 'false',
        'not': '!',
        'and': '&&',
        'or': '||',
        'indent': 4 * ' ',
        'quote': '\"',
        'print_generic': 'println({object})',
        'print': 'println(\"{message}\")',
        'fprintf': '@printf(\"{message}\", {variables})',
        'error': 'error(\"{error_msg}\")',
        'block_end': 'end',
        'if_begin': 'if {cond}',
        'if_elif': 'elseif {cond}',
        'if_else': 'else',
        'for_begin': 'for {iter_var} in {iter_begin}:{iter_end}',
        'while_begin': 'while {cond}',
        'break': 'break',
        'try_begin': 'try',
        'try_except': 'catch',
        'assign': 'global {name} = {value}',
        'function_def_begin': 'function {function_name}({input_var})',
        'return': 'return {output_var}',
        'function_def_regex': (
            r'\n?( *)function +{function_name}'
            r'(?P<outtype>\:\:[^\(]+?)?'
            r' *\((?P<inputs>(?:[^\)]+?)?)\) *'
            r'(?P<body>(?:(?:\1(?: *)(?!return)[^ ].*?\n)|(?: *\n))*)'
            r'(?:\1(?: *)'
            r'(?:return *)?(?P<outputs>.*?) *\n)?'),
        'inputs_def_regex': r'\s*(?P<name>.+?)\s*(?:,|$)',
        'outputs_def_regex': r'\s*(?P<name>.+?)\s*(?:,|$)'}
    zero_based = False

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        if lib not in cls._library_cache:
            try:
                cls.run_executable(['-e', f'using {lib}'],
                                   env=cls.set_env_class())
                cls._library_cache[lib] = True
            except RuntimeError:
                cls._library_cache[lib] = False
        return cls._library_cache[lib]

    @classmethod
    def set_env_class(cls, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(JuliaModelDriver, cls).set_env_class(**kwargs)
        out['PYTHON'] = PythonModelDriver.get_interpreter()
        return out

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
        value = 'Array{Any, 1}(undef, %s)' % var['iter_var']['end']
        out = super(JuliaModelDriver, cls).write_initialize_oiter(
            var, value=value, **kwargs)
        return out
    
    @classmethod
    def write_finalize_oiter(cls, var):
        r"""Get the lines necessary to finalize an array after iteration.

        Args:
            var (dict, str): Name or information dictionary for the variable
                being initialized.

        Returns:
            list: The lines finalizing the variable.

        """
        out = super(JuliaModelDriver, cls).write_finalize_oiter(var)
        out += [f"{var['name']}_type = typeof({var['name']}[1])",
                f"global {var['name']} = Array{{{var['name']}_type}}({var['name']})"]
        return out

    @classmethod
    def write_executable_import(cls, **kwargs):
        r"""Add import statements to executable lines.
       
        Args:
            **kwargs: Keyword arguments for import statement.

        Returns:
            list: Lines required to complete the import.
 
        """
        if platform._is_win:  # pragma: windows
            kwargs['filename'] = kwargs['filename'].replace('\\', '\\\\')
        return super(JuliaModelDriver, cls).write_executable_import(**kwargs)
    
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
        out = super(JuliaModelDriver, cls).get_testing_options(**kwargs)
        out.setdefault('invalid_libraries', ['invalid_unicorn'])
        return out
