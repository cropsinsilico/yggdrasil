import os
from yggdrasil import tools
from yggdrasil.drivers.ModelDriver import ModelDriver


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))


class InterpretedModelDriver(ModelDriver):
    r"""Base class for models written in interpreted languages.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. This driver will check to see if there is an interpreter
            included in the args provided. If not, one will be added unless
            skip_interpreter is True.
        interpreter (str, optional): Name or path of interpreter executable that
            should be used to run the model. If not provided, the interpreter
            will be determined based on configuration options for the language
            (if present) and the default_interpreter class attribute.
        interpreter_flags (list, optional): Flags that should be passed to the
            interpreter when running the model. If not provided, the flags are
            determined based on configuration options for the language (if
            present) and the default_interpreter_flags class attribute.
        skip_interpreter (bool, optional): If True, no interpreter will be
            added to the arguments. This should only be used for subclasses
            that will not be invoking the model via the command line.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Class Attributes:
        default_interpreter (str): Name of interpreter that will be used if not
            set explicitly by instance or config file. Defaults to the language
            name if not set.
        default_interpreter_flags (list): Flags that will be passed to the
            interpreter when running the model by default if not set explicitly
            by instance or config file.

    Attributes:
        interpreter (str): Name or path to the interpreter that will be used.
        interpreter_flags (list): Flags that will be passed to the interpreter
            when running a model.
        path_env_variable (str): Name of the environment variable containing
            path information for the interpreter for this language.
        paths_to_add (list): Paths that should be added to the path_env_variable
            for this language on the process the model is run in.
        comm_atexit (function): Function taking a comm instance as input that
            performs any necessary operations during exit. If None, no additional
            actions are taken.
        comm_linger (bool): If True, interface comms will linger during close.
            This should only be required if the language will disreguard Python
            threads at exit (e.g. when using a Matlab engine).
        decode_format (function: Function decoding format string created in this
            language. If None, no additional actions are taken.
        recv_converters (dict): Mapping between the names of message types (e.g.
            'array', 'pandas') and functions that should be used to prepare such
            objects for return when they are received.
        send_converters (dict): Mapping between the names of message types (e.g.
            'array', 'pandas') and functions that should be used to prepare such
            objects for sending.

    """

    _schema_properties = {
        'interpreter': {'type': 'string'},
        'interpreter_flags': {'type': 'array', 'items': {'type': 'string'},
                              'default': []},
        'skip_interpreter': {'type': 'boolean', 'default': False}}
    executable_type = 'interpreter'
    default_interpreter = None
    default_interpreter_flags = []
    path_env_variable = None
    paths_to_add = [_top_dir]
    comm_atexit = None
    comm_linger = False
    decode_format = None
    recv_converters = {}
    send_converters = {}
    _config_attr_map = [{'attr': 'default_interpreter',
                         'key': 'interpreter'},
                        {'attr': 'default_interpreter_flags',
                         'key': 'interpreter_flags',
                         'type': list}]

    def __init__(self, name, args, **kwargs):
        super(InterpretedModelDriver, self).__init__(name, args, **kwargs)
        # Set defaults from attributes
        for k0 in ['interpreter']:
            for k in [k0, '%s_flags' % k0]:
                v = getattr(self, k, None)
                if v is None:
                    setattr(self, k, getattr(self, 'default_%s' % k))

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        ModelDriver.after_registration(cls, **kwargs)
        if kwargs.get('second_pass', False):
            return
        if cls.language is not None:
            # Set default interpreter based on language
            if cls.default_interpreter is None:
                cls.default_interpreter = cls.language
            # Add directory containing the interface
            cls.paths_to_add.append(cls.get_language_dir())
                    
    def parse_arguments(self, *args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            *args: Arguments are passed to the parent class's method.
            **kwargs: Keyword arguments are passed to the parent class's method.

        """
        super(InterpretedModelDriver, self).parse_arguments(*args, **kwargs)
        self.model_src = self.model_file
        
    @classmethod
    def get_interpreter(cls):
        r"""Command required to run a model written in this language from
        the command line.

        Returns:
            str: Name of (or path to) interpreter executable.

        """
        out = getattr(cls, 'interpreter', getattr(cls, 'default_interpreter'))
        if out is None:
            raise NotImplementedError("Interpreter not set for language '%s'."
                                      % cls.language)
        return out

    @classmethod
    def get_interpreter_flags(cls):
        r"""Get the flags that should be passed to the interpreter when using it
        to run a model on the command line.

        Returns:
            list: Flags that should be passed to the interpreter on the command
                line.

        """
        out = getattr(cls, 'interpreter_flags',
                      getattr(cls, 'default_interpreter_flags'))
        return out

    @classmethod
    def language_executable(cls):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return cls.get_interpreter()

    @classmethod
    def executable_command(cls, args, exec_type='interpreter', unused_kwargs={},
                           skip_interpreter_flags=False, **kwargs):
        r"""Compose a command for running a program in this language with the
        provied arguments. If not already present, the interpreter command and
        interpreter flags are prepended to the provided arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it.
            exec_type (str, optional): Type of executable command that will be
                returned. If 'interpreter', a command using the interpreter is
                returned and if 'direct', the raw args being provided are
                returned. Defaults to 'interpreter'.
            skip_interpreter_flags (bool, optional): If True, interpreter flags
                will not be added to the command after the interpreter. Defaults
                to False. Interpreter flags will not be added, reguardless of
                this keyword, if the first element of args is already an
                interpreter.
            unused_kwargs (dict, optional): Existing dictionary that unused
                keyword arguments should be added to. Defaults to {}.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the interpreter for this language.

        Raises:
            ValueError: If exec_type is not 'interpreter' or 'direct'.

        """
        ext = cls.language_ext
        assert(isinstance(ext, (tuple, list)))
        if exec_type == 'interpreter':
            if not cls.is_interpreter(args[0]):
                new_args = [cls.get_interpreter()]
                if not skip_interpreter_flags:
                    new_args += cls.get_interpreter_flags()
                args = new_args + args
        elif exec_type != 'direct':
            raise ValueError("Invalid exec_type '%s'" % exec_type)
        unused_kwargs.update(kwargs)
        return args

    @classmethod
    def is_interpreter(cls, cmd):
        r"""Determine if a command line argument is an interpreter.

        Args:
            cmd (str): Command that should be checked.

        Returns:
            bool: True if the command is an interpreter, False otherwise.

        """
        # (cls.language not in cmd)
        out = ((tools.which(cmd) is not None)
               and (not any([cmd.endswith(e) for e in cls.language_ext])))
        return out

    def set_env(self):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(InterpretedModelDriver, self).set_env()
        if self.path_env_variable is not None:  # pragma: debug
            if self.language != 'matlab':
                raise NotImplementedError(
                    ("Language %s sets path_env_variable. "
                     "Move part of MatlabModelDriver set_env method "
                     "to InterpretedModelDriver in place of this "
                     "warning message.") % self.language)
        return out

    # Methods for handling type conversions
    @classmethod
    def python2language(cls, pyobj):
        r"""Prepare a python object for transformation in target
        language.

        Args:
            pyobj (object): Python object.

        Returns:
            object: Python object in a form that is friendly to the
                target language.

        """
        return pyobj

    @classmethod
    def language2python(cls, pyobj):
        r"""Prepare an object from the target language for receipt
        in Python.

        Args:
            pyobj (object): Python object transformed from the target
                language.

        Returns:
            object: Python object in a form that conforms with the
                expected Python type.

        """
        return pyobj
