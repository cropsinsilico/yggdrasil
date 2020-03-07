import copy
from collections import OrderedDict
from yggdrasil import components, platform
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
        target (str, optional): Make target that should be built to create the
            model executable. Defaults to None.
        target_language (str, optional): Language that the target is written in.
            Defaults to None and will be set based on the source files provided.
        env_compiler (str, optional): Environment variable where the compiler
            executable should be stored for use within the Makefile. Defaults
            to 'CC'.
        env_compiler_flags (str, optional): Environment variable where the
            compiler flags should be stored (including those required to compile
            against the |yggdrasil| interface). Defaults to 'CFLAGS'.
        env_linker (str, optional): Environment variable where the linker
            executable should be stored for use within the Makefile. Defaults
            to 'CC'. If the same variable is provided for both env_compiler and
            env_linker, this indicates that the same program should be used for
            both compiling and linking (e.g. gcc). In such cases, the compiler
            will be stored there and it is assumed that it will be appropriate
            for linking as well.
        env_linker_flags (str, optional): Environment variable where the
            linker flags should be stored (including those required to link
            against the |yggdrasil| interface). Defaults to 'LDFLAGS'.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Path to make file either relative to makedir or absolute.
        makedir (str): Directory where make should be invoked from.
        target (str): Name of executable that should be created and called.
        target_language (str): Language that the target is written in.
        target_language_driver (ModelDriver): Language driver for the target
            language.
        env_compiler (str): Compiler environment variable.
        env_compiler_flags (str): Compiler flags environment variable.
        env_linker (str): Linker environment variable.
        env_linker_flags (str): Linker flags environment variable.

    """
    _schema_properties = {
        'makefile': {'type': 'string', 'default': 'Makefile'},
        'makedir': {'type': 'string'},  # default will depend on makefile
        'target': {'type': 'string'},
        'target_language': {'type': 'string'},
        'env_compiler': {'type': 'string', 'default': 'CC'},
        'env_compiler_flags': {'type': 'string', 'default': 'CFLAGS'},
        'env_linker': {'type': 'string', 'default': 'CC'},
        'env_linker_flags': {'type': 'string', 'default': 'LDFLAGS'}}
    toolname = 'make'
    languages = ['make', 'c', 'c++']
    platforms = ['MacOS', 'Linux']
    default_flags = ['--always-make']  # Always overwrite
    flag_options = OrderedDict([('makefile', {'key': '-f', 'position': 0})])
    output_key = ''
    no_separate_linking = True
    default_archiver = False
    linker_attributes = {'executable_ext': ''}
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
    def language_version(cls, **kwargs):
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
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Linker flags.

        """
        link_kws = ['linker_flags']
        for k in link_kws:
            kwargs.pop(k, None)
        kwargs.pop('outfile', None)
        # if (target is None) and (outfile is not None):
        #     target = cls.file2base(outfile)
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

    @classmethod
    def set_env(cls, logging_level=None, language=None, language_driver=None,
                **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            logging_level (int, optional): Logging level that should be passed
                to get flags.
            language (str, optional): Language that is being compiled. Defaults
                to the first language in cls.languages that isn't toolname.
            language_driver (ModelDriver, optional): Driver for language that
                should be used. Defaults to None and will be imported based
                on language.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        if language_driver is None:
            if language is None:
                language = cls.get_default_target_language()
            language_driver = components.import_component('model', language)
        kwargs['language_driver'] = language_driver
        out = super(MakeCompiler, cls).set_env(**kwargs)
        compiler = language_driver.get_tool('compiler')
        compile_flags = language_driver.get_compiler_flags(
            for_model=True, skip_defaults=True, dont_skip_env_defaults=True,
            logging_level=logging_level, dont_link=True)
        linker = language_driver.get_tool('linker')
        linker_flags = language_driver.get_linker_flags(
            for_model=True, skip_defaults=True, dont_skip_env_defaults=True)
        for k in ['env_compiler', 'env_compiler_flags',
                  'env_linker', 'env_linker_flags']:
            kwargs.setdefault(k, cls._schema_properties[k]['default'])
        out[kwargs['env_compiler']] = compiler.get_executable()
        out[kwargs['env_compiler_flags']] = ' '.join(compile_flags)
        # yggdrasil requires that linking be done in C++
        if (((compiler.languages[0].lower() == 'c')
             and ('-lstdc++' not in linker_flags))):
            linker_flags.append('-lstdc++')
        out[kwargs['env_linker_flags']] = ' '.join(linker_flags)
        if kwargs['env_compiler'] != kwargs['env_linker']:  # pragma: debug
            out[kwargs['env_linker']] = linker.get_executable()
            raise NotImplementedError("Functionality allowing linker to be specified "
                                      "in a separate environment variable from the "
                                      "compiler is untested.")
        return out
    

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
        target (str, optional): Make target that should be built to create the
            model executable. Defaults to None.
        target_language (str, optional): Language that the target is written in.
            Defaults to None and will be set based on the source files provided.
        env_compiler (str, optional): Environment variable where the compiler
            executable should be stored for use within the Makefile. Defaults
            to 'CC'.
        env_compiler_flags (str, optional): Environment variable where the
            compiler flags should be stored (including those required to compile
            against the |yggdrasil| interface). Defaults to 'CFLAGS'.
        env_linker (str, optional): Environment variable where the linker
            executable should be stored for use within the Makefile. Defaults
            to 'CC'.
        env_linker_flags (str, optional): Environment variable where the
            linker flags should be stored (including those required to link
            against the |yggdrasil| interface). Defaults to 'LDFLAGS'.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Path to make file either relative to makedir or absolute.
        makedir (str): Directory where make should be invoked from.
        target (str): Name of executable that should be created and called.
        target_language (str): Language that the target is written in.
        target_language_driver (ModelDriver): Language driver for the target
            language.
        env_compiler (str): Compiler environment variable.
        env_compiler_flags (str): Compiler flags environment variable.
        env_linker (str): Linker environment variable.
        env_linker_flags (str): Linker flags environment variable.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'Makefile for compilation.')
    _schema_properties = copy.deepcopy(MakeCompiler._schema_properties)
    language = 'make'
    base_languages = ['c', 'c++']
    built_where_called = True

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        BuildModelDriver.before_registration(cls)
        if platform._is_win:  # pragma: windows
            cls.default_compiler = 'nmake'
        
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
            return self.call_compiler([], target=target,
                                      out=target, overwrite=True,
                                      makefile=self.buildfile,
                                      working_dir=self.working_dir, **kwargs)
        else:
            default_kwargs = dict(skip_interface_flags=True,
                                  # source_files=[],  # Unknown source files, use target
                                  for_model=False,  # flags are in environment
                                  working_dir=self.makedir,
                                  makefile=self.buildfile)
            if target is not None:
                default_kwargs['target'] = target
            for k, v in default_kwargs.items():
                kwargs.setdefault(k, v)
            return super(MakeModelDriver, self).compile_model(**kwargs)
        
    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        if kwargs.get('for_compile', False):
            kwargs.setdefault('compile_kwargs', {})
            for k in ['env_compiler', 'env_compiler_flags',
                      'env_linker', 'env_linker_flags']:
                kwargs['compile_kwargs'][k] = getattr(self, k)
        out = super(MakeModelDriver, self).set_env(**kwargs)
        return out
