from yggdrasil import platform, tools
from yggdrasil.drivers.ModelDriver import ModelDriver


if platform._is_win:  # pragma: windows
    _os_version_flags = ['winver']
else:
    _os_version_flags = ['uname', '-r']
    # _os_version_flags = ['echo $0']


class ExecutableModelDriver(ModelDriver):
    r"""Class for running executable based models."""

    language = 'executable'
    version_flags = _os_version_flags

    @classmethod
    def language_executable(cls):
        r"""Command/arguments required to compile/run a model written in this
        language from the command line.

        Returns:
            list: Name of (or path to) compiler/interpreter executable and any
                flags required to run the compiler/interpreter from the command
                line.

        """
        return None

    @classmethod
    def executable_command(cls, args, unused_kwargs=None, **kwargs):
        r"""Compose a command for running a program using the exectuable for
        this language (compiler/interpreter) with the provided arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it.
            unused_kwargs (dict, optional): Existing dictionary that unused
                keyword arguments should be added to. Defaults to None and is
                ignored.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the executable for this language.

        """
        if isinstance(unused_kwargs, dict):
            unused_kwargs.update(kwargs)
        return args
        
    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        return []
        
    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        return True

    @classmethod
    def is_library_installed(cls, lib):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        return (tools.which(lib) is not None)
        
    @classmethod
    def is_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        return True

    @classmethod
    def is_comm_installed(self, **kwargs):
        r"""Determine if a comm is installed for the associated programming
        language.

        Returns:
            bool: True if a comm is installed for this language.

        """
        return True  # executables presumed include comms
