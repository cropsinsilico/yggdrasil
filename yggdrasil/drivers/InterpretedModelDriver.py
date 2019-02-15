from yggdrasil.drivers.ModelDriver import ModelDriver


class InterpretedModelDriver(ModelDriver):
    r"""Base class for models written in interpreted languages."""

    def __init__(self, name, args, skip_interpreter=False, **kwargs):
        super(InterpretedModelDriver, self).__init__(name, args, **kwargs)
        if not skip_interpreter:
            if (((self._language not in self.args[0])
                 or (self.args[0].endswith(self._language_ext)))):
                self.args = self.language_interpreter() + self.args
        self.debug(self.args)

    @classmethod
    def language_interpreter(cls):
        r"""Command/arguments required to run a model written in this language
        from the command line.

        Returns:
            list: Name of (or path to) interpreter executable and any flags
                required to run the interpreter from the command line.

        """
        raise NotImplementedError("Language interpreter not set.")

    @classmethod
    def language_executable(cls):
        r"""Command/arguments required to compile/run a model written in this
        language from the command line.

        Returns:
            list: Name of (or path to) compiler/interpreter executable and any
                flags required to run the compiler/interpreter from the command
                line.

        """
        return cls.language_interpreter()
