from collections import OrderedDict
from yggdrasil import platform, constants
from yggdrasil.drivers.CompiledModelDriver import BuilderBase
from yggdrasil.drivers.BuildModelDriver import BuildModelDriver


class MakeBuilder(BuilderBase):
    r"""Make configuration tool.

    Args:
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    toolname = 'make'
    languages = ['make']
    platforms = ['MacOS', 'Linux', 'Windows']
    default_flags = ['--always-make']  # Always overwrite
    flag_options = OrderedDict(
        [('buildfile', {'key': '-f', 'position': 0})])
    output_key = None
    build_params = ['target']
    version_regex = [r'(?P<version>GNU Make \d+\.\d+(?:\.\d+)?)']
    aliases = ['mingw32-make'] if platform._is_win else []
    toolset = 'gnu'
    compatible_toolsets = ['llvm', 'msvc']
        
    @classmethod
    def get_flags(cls, target=None, **kwargs):
        r"""Get compilation flags, replacing outfile with target.

        Args:
            target (str, optional): Target that should be built. Defaults
                to None and is ignored.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Compiler flags.

        """
        return super(MakeBuilder, cls).get_flags(**kwargs)

    @classmethod
    def get_executable_command(cls, args, target=None, **kwargs):
        r"""Determine the command required to run the tool using the
        specified arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool.
                If skip_flags is False, these are treated as input files
                that will be used by the tool.
            target (str, optional): Target that should be built. Defaults
                to None and is set to the base name of first element in
                the provided arguments.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        if not kwargs.get('skip_flags', False):
            if len(args) == 1:
                if target is None:
                    target = cls.file2base(args[0])
                else:
                    if target != cls.file2base(args[0]):
                        raise RuntimeError(
                            f"The argument list contents (='{args[0]}') "
                            f"and 'target' (='{target}') keyword "
                            f"argument specify the same thing, but those "
                            f"provided do not match.")
            args = [target]
        return super(MakeBuilder, cls).get_executable_command(args,
                                                              **kwargs)


class NMakeBuilder(MakeBuilder):
    toolname = 'nmake'
    platforms = ['Windows']
    default_flags = ['/NOLOGO']
    flag_options = OrderedDict([('buildfile', '/f')])
    default_executable = None
    version_regex = [
        r'(?P<version>Microsoft \(R\) Program Maintenance Utility '
        r'Version \d+\.\d+(?:\.\d+)*)']
    is_gnu = False
    toolset = 'msvc'
    compatible_toolsets = []


class MakeModelDriver(BuildModelDriver):
    r"""Class for running make file compiled drivers. Before running the
    make command, the necessary compiler & linker flags for the
    interface's C/C++ library are stored the environment variables CFLAGS
    and LDFLAGS respectively. These should be used in the make file to
    correctly compile with the interface's C/C++ libraries.

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (make target)
            and any arguments for the executable.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Absolute path to make file.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = (
        'Model is written in a compiled language and has a '
        'Makefile for performing compilation.')
    language = 'make'
    buildfile_base = 'Makefile'
    builddir_base = '.'
    default_builder = 'nmake' if platform._is_win else 'make'
    default_target = []
    default_in_source_build = True

    @classmethod
    def get_language_for_buildfile(cls, buildfile, target=None):
        r"""Determine the target language based on the contents of a build
        file.

        Args:
            buildfile (str): Full path to the build configuration file.
            target (str, optional): Target that will be built. Defaults
                to None and the default target in the build file will be
                used.

        """
        with open(buildfile, 'r') as fd:
            lines = fd.read()
        ext_present = []
        for lang, info in constants.COMPILER_ENV_VARS.items():
            if info['exec'] and info['exec'] in lines:
                ext_present.append(lang)
        if ('c' in ext_present) and ('c++' in ext_present):  # pragma: debug
            ext_present.remove('c')
        if len(ext_present) == 1:
            return ext_present[0]
        elif len(ext_present) > 1:  # pragma: debug
            raise RuntimeError(f"More than one extension found in "
                               f"'{buildfile}': {ext_present}")
        return super(MakeModelDriver, cls).get_language_for_buildfile(
            buildfile)  # pragma: debug
