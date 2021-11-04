from collections import OrderedDict
from yggdrasil import platform, constants
from yggdrasil.drivers.BuildModelDriver import (
    BuildModelDriver, BuildToolBase)


class MakeCompiler(BuildToolBase):
    r"""Make configuration tool.

    Args:
        makefile (str, optional): Path to make file either absolute, relative to
            makedir (if provided), or relative to working_dir. Defaults to
            Makefile.
        makedir (str, optional): Directory where make should be invoked from
            if it is not the same as the directory containing the makefile.
            Defaults to directory containing makefile if provided, otherwise
            working_dir.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    toolname = 'make'
    languages = ['make']
    platforms = ['MacOS', 'Linux']
    default_flags = ['--always-make']  # Always overwrite
    flag_options = OrderedDict([('makefile', {'key': '-f', 'position': 0})])
    output_key = ''
    no_separate_linking = True
    default_archiver = False
    linker_attributes = {'executable_ext': '', 'tool_suffix_format': ''}
    build_language = 'make'
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        BuildToolBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            cls.linker_attributes['executable_ext'] = '.exe'

    @classmethod
    def tool_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.call.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        out = cls.call(cls.version_flags, skip_flags=True,
                       allow_error=True, **kwargs)
        if 'Copyright' not in out:  # pragma: debug
            raise RuntimeError("Version call failed: %s" % out)
        for x in (out.split('Copyright')[0]).splitlines():
            if x.strip():
                return x.strip()
        else:  # pragma: debug
            raise Exception("Could not extract version from string:\n%s" % out)
        
    @classmethod
    def get_output_file(cls, src, target=None, **kwargs):
        r"""Determine the appropriate output file that will result when
        compiling a target.

        Args:
            src (str): Make target or source file being compiled that will be
                used to determine the path to the output file.
            target (str, optional): Target that will be used to create the
                output file instead of src if provided. Defaults to None and
                is ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Full path to file that will be produced.

        """
        if target is not None:
            src = target
        if src == 'clean':
            # Abort early so that working_dir not prepended
            return src
        out = super(MakeCompiler, cls).get_output_file(src, **kwargs)
        return out

    @classmethod
    def get_flags(cls, target=None, **kwargs):
        r"""Get compilation flags, replacing outfile with target.

        Args:
            target (str, optional): Target that should be built. Defaults to
                to None and is ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Compiler flags.

        """
        kwargs.pop('linker_flags', None)
        kwargs.pop('outfile', None)
        out = super(MakeCompiler, cls).get_flags(outfile=target, **kwargs)
        return out

    @classmethod
    def get_executable_command(cls, args, target=None, **kwargs):
        r"""Determine the command required to run the tool using the specified
        arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool. If
                skip_flags is False, these are treated as input files that will
                be used by the tool.
            target (str, optional): Target that should be built. Defaults to
                to None and is set to the base name of first element in the
                provided arguments.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        if not kwargs.get('skip_flags', False):
            assert(len(args) <= 1)
            if len(args) == 1:
                if target is None:
                    target = cls.file2base(args[0])
                else:
                    if target != cls.file2base(args[0]):
                        raise RuntimeError(("The argument list contents (='%s') "
                                            "and 'target' (='%s') keyword argument "
                                            "specify the same thing, but those "
                                            "provided do not match.")
                                           % (args[0], target))
            args = []
        if target is not None:
            kwargs['target'] = target
        return super(MakeCompiler, cls).get_executable_command(args, **kwargs)


class NMakeCompiler(MakeCompiler):
    toolname = 'nmake'
    platforms = ['Windows']
    default_flags = ['/NOLOGO']
    flag_options = OrderedDict([('makefile', '/f')])
    default_executable = None
    default_linker = None  # Force linker to be initialized with the same name
    

class MakeModelDriver(BuildModelDriver):
    r"""Class for running make file compiled drivers. Before running the
    make command, the necessary compiler & linker flags for the interface's
    C/C++ library are stored the environment variables CFLAGS and LDFLAGS
    respectively. These should be used in the make file to correctly compile
    with the interface's C/C++ libraries.

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (make target) and
            any arguments for the executable.
        makefile (str, optional): Path to make file either absolute, relative to
            makedir (if provided), or relative to working_dir. Defaults to
            Makefile.
        makedir (str, optional): Directory where make should be invoked from
            if it is not the same as the directory containing the makefile.
            Defaults to directory containing makefile if provided, otherwise
            working_dir.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Path to make file either relative to makedir or absolute.
        makedir (str): Directory where make should be invoked from.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'Makefile for compilation.')
    _schema_properties = {
        'makefile': {'type': 'string', 'default': 'Makefile'},
        'makedir': {'type': 'string'}}  # default will depend on makefile
    language = 'make'
    built_where_called = True
    buildfile_base = 'Makefile'

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        BuildModelDriver.before_registration(cls)
        if platform._is_win:  # pragma: windows
            cls.default_compiler = 'nmake'
        
    @classmethod
    def get_buildfile_lock(cls, **kwargs):
        r"""Get a lock for a buildfile to prevent simultaneous access,
        creating one as necessary."""
        kwargs.setdefault('when_to_lock', 'cleanup')
        return super(MakeModelDriver, cls).get_buildfile_lock(**kwargs)
        
    def parse_arguments(self, args, **kwargs):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        self.buildfile = self.makefile
        self.compile_working_dir = self.makedir
        super(MakeModelDriver, self).parse_arguments(args, **kwargs)

    @classmethod
    def get_language_for_buildfile(cls, buildfile, target=None):
        r"""Determine the target language based on the contents of a build
        file.

        Args:
            buildfile (str): Full path to the build configuration file.
            target (str, optional): Target that will be built. Defaults to None
                and the default target in the build file will be used.

        """
        with open(buildfile, 'r') as fd:
            lines = fd.read()
        ext_present = []
        for lang, info in constants.COMPILER_ENV_VARS.items():
            if info['exec'] in lines:
                ext_present.append(lang)
        if ('c' in ext_present) and ('c++' in ext_present):  # pragma: debug
            ext_present.remove('c')
        if len(ext_present) == 1:
            return ext_present[0]
        elif len(ext_present) > 1:  # pragma: debug
            raise RuntimeError("More than one extension found in "
                               "'%s': %s" % (buildfile, ext_present))
        return super(MakeModelDriver, cls).get_language_for_buildfile(
            buildfile)  # pragma: debug
        
    def compile_model(self, target=None, **kwargs):
        r"""Compile model executable(s).

        Args:
            target (str, optional): Target to build.
            **kwargs: Keyword arguments are passed on to the parent class's
                method.

        """
        if target is None:
            target = self.target
        if target == 'clean':
            with self.buildfile_locked(dry_run=kwargs.get('dry_run', False)):
                return self.call_compiler([], target=target,
                                          out=target, overwrite=True,
                                          makefile=self.buildfile,
                                          working_dir=self.working_dir,
                                          **kwargs)
        else:
            default_kwargs = dict(skip_interface_flags=True,
                                  # source_files=[],  # Unknown source files, use target
                                  for_model=False,  # flags are in environment
                                  working_dir=self.makedir,
                                  makefile=self.buildfile,
                                  dont_lock_buildfile=True)
            if target is not None:
                default_kwargs['target'] = target
            for k, v in default_kwargs.items():
                kwargs.setdefault(k, v)
            return super(MakeModelDriver, self).compile_model(**kwargs)

    @classmethod
    def fix_path(cls, path, for_env=False, **kwargs):
        r"""Update a path.

        Args:
            path (str): Path that should be formatted.
            for_env (bool, optional): If True, the path is formatted for use in
                and environment variable. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Updated path.

        """
        out = super(MakeModelDriver, cls).fix_path(path, for_env=for_env,
                                                   **kwargs)
        if platform._is_win and for_env:
            out = '"%s"' % out
        return out

    @classmethod
    def get_target_language_info(cls, *args, **kwargs):
        r"""Get a dictionary of information about language compilation tools.

        Args:
            *args: Arguments are passed to the parent class's method.
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            dict: Information about language compilers and linkers.

        """
        out = super(MakeModelDriver, cls).get_target_language_info(*args, **kwargs)
        if (((cls.get_tool('compiler', return_prop='name') == 'nmake')
             and platform._is_win and ('-lstdc++' in out['linker_flags']))):
            out['linker_flags'].remove('-lstdc++')
            out['linker_env'] = ''
        return out
