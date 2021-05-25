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
    interface_dependencies = ['PyCall']
    type_map = {
        'int': 'Int',
        'float': 'Float',
        'string': 'String',
        'array': 'Array{Any}',
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
    function_param = {
        'import_nofile': 'using {function}',
        'import': 'using {filename}: {function}',
        'istype': '{variable} isa {type}',
        'len': 'length({variable})',
        'index': '{variable}[{index}]',
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
        'assign': '{name} = {value}',
        'function_def_begin': 'function {function_name}({input_var})',
        'return': 'return {output_var}',
        'function_def_regex': (
            r'\n?( *)function +{function_name}'
            r'(?P<outtype>\:\:.+)?'
            r' *\((?P<inputs>(?:.|\n)*?)\) *'
            r'(?P<body>(?:\1(?:    )+(?!return).*\n)|(?: *\n))*'
            r'(?:\1(?:    )+(?:return )?(?P<outputs>.*)\n)?'),
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
                cls.run_executable(['-e', 'using %s' % lib])
                # cls.run_executable(['-e', 'haskey(Pkg.installed(), "%s")'])
                cls._library_cache[lib] = True
            except RuntimeError:
                cls._library_cache[lib] = False
        return cls._library_cache[lib]

    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(JuliaModelDriver, self).set_env(**kwargs)
        out['PYTHON'] = PythonModelDriver.get_interpreter()
        return out
