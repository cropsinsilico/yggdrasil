from yggdrasil.config import ygg_cfg
from yggdrasil.drivers.ModelDriver import ModelDriver


class InterpretedModelDriver(ModelDriver):
    r"""Base class for models written in interpreted languages.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. This driver will check to see if there is an interpreter
            included in the args provided. If not, one will be added unless
            skip_interpreter is True.
        skip_interpreter (bool, optional): If True, no interpreter will be
            added to the arguments. This should only be used for subclasses
            that will not be invoking the model via the command line.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _interpreter_flags = []

    def __init__(self, name, args, skip_interpreter=False, **kwargs):
        super(InterpretedModelDriver, self).__init__(name, args, **kwargs)
        if not skip_interpreter:
            ext = self._language_ext
            if not isinstance(ext, list):
                ext = [ext]
            if (((self._language not in self.args[0])
                 or any([self.args[0].endswith(e) for e in ext]))):
                self.args = list([self.interpreter()]
                                 + self._interpreter_flags + self.args)
        self.debug(self.args)

    @classmethod
    def interpreter(cls):
        r"""Command required to run a model written in this language from
        the command line.

        Returns:
            str: Name of (or path to) interpreter executable.

        """
        out = ygg_cfg.get(cls._language, 'interpreter',
                          getattr(cls, '_interpreter', cls._language))
        if out is None:
            raise NotImplementedError("Interpreter not set for language '%s'."
                                      % cls._language)

    @classmethod
    def language_executable(cls):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return cls.interpreter()
