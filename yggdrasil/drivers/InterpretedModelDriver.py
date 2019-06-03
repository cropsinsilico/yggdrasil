from yggdrasil import tools
from yggdrasil.config import ygg_cfg, locate_file
from yggdrasil.drivers.ModelDriver import ModelDriver


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

    """

    _schema_properties = {
        'interpreter': {'type': 'string'},
        'interpreter_flags': {'type': 'array', 'items': {'type': 'string'},
                              'default': []},
        'skip_interpreter': {'type': 'boolean', 'default': False}}
    executable_type = 'interpreter'
    default_interpreter = None
    default_interpreter_flags = []

    def __init__(self, name, args, **kwargs):
        super(InterpretedModelDriver, self).__init__(name, args, **kwargs)
        # Set defaults from attributes
        for k0 in ['interpreter']:
            for k in [k0, '%s_flags' % k0]:
                v = getattr(self, k, None)
                if v is None:
                    setattr(self, k, getattr(self, 'default_%s' % k))

    @staticmethod
    def after_registration(cls):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        ModelDriver.after_registration(cls)
        if cls.language is not None:
            for k in ['interpreter']:
                # Set attribute defaults based on config options
                for k0 in [k, '%s_flags' % k]:
                    ka = 'default_%s' % k0
                    if k0.endswith('_flags'):
                        old_val = getattr(cls, ka)
                        old_val += ygg_cfg.get(cls.language, k0, '').split()
                    else:
                        setattr(cls, ka, ygg_cfg.get(cls.language, k0,
                                                     getattr(cls, ka)))
            # Set default interpreter based on language
            if cls.default_interpreter is None:
                cls.default_interpreter = cls.language
                    
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
        # out = None
        # if cls.language is not None:
        #     out = ygg_cfg.get(cls.language, 'interpreter',
        #                       getattr(cls, '_interpreter', cls.language))
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
                           **kwargs):
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
            # if (((cls.language not in args[0])
            if (((tools.which(args[0]) is None)
                 or any([args[0].endswith(e) for e in ext]))):
                args = [cls.get_interpreter()] + cls.get_interpreter_flags() + args
        elif exec_type != 'direct':
            raise ValueError("Invalid exec_type '%s'" % exec_type)
        unused_kwargs.update(kwargs)
        return args

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
        out = super(InterpretedModelDriver, cls).configure(cfg)
        # Locate executable
        if not cls.is_language_installed():  # pragma: debug
            fpath = locate_file(cls.language_executable())
            if fpath:
                cfg.set(cls.language, 'interpreter', fpath)
        return out
