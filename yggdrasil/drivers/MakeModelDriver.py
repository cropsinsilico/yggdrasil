import os
import copy
from collections import OrderedDict
from yggdrasil import components, backwards, platform
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase)
from yggdrasil.drivers.CModelDriver import CModelDriver


class MakeCompiler(CompilerBase):
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
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Path to make file either relative to makedir or absolute.
        makedir (str): Directory where make should be invoked from.
        target (str): Name of executable that should be created and called.

    """
    _schema_properties = {
        'makefile': {'type': 'string', 'default': 'Makefile'},
        'makedir': {'type': 'string'},  # default will depend on makefile
        'target': {'type': 'string'}}
    toolname = 'make'
    languages = ['make', 'c', 'c++']
    platforms = ['MacOS', 'Linux']
    default_flags = ['--always-make']  # Always overwrite
    flag_options = OrderedDict([('makefile', {'key': '-f', 'position': 0})])
    output_key = ''
    no_separate_linking = True
    default_archiver = False
    linker_attributes = {'executable_ext': ''}
    
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilerBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            cls.linker_attributes['executable_ext'] = '.exe'
        
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
    def set_env(cls, logging_level=None, language=None, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            logging_level (int, optional): Logging level that should be passed
                to get flags.
            language (str, optional): Language that is being compiled. Defaults
                to the first language in cls.languages.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(MakeCompiler, cls).set_env(**kwargs)
        if language is None:
            language = 'c'
        drv = components.import_component('model', language)
        compile_flags = drv.get_compiler_flags(
            for_model=True, logging_level=logging_level, skip_defaults=True)
        linker_flags = drv.get_linker_flags(
            for_model=True, skip_defaults=True)
        # TODO: Put these in the default_flags_env?
        # TODO: Change these to be more generic?
        out['YGGCCFLAGS'] = backwards.as_str(' '.join(compile_flags))
        out['YGGLDFLAGS'] = backwards.as_str(' '.join(linker_flags))
        # Set default compiler executable
        # compiler = drv.get_tool('compiler')
        # linker = drv.get_tool('linker')
        # if (((compiler.default_executable_env is not None)
        #      and (compiler.default_executable_env not in out))):
        #     out[compiler.default_executable_env] = compiler.get_executable()
        # if (((linker.default_executable_env is not None)
        #      and (linker.default_executable_env not in out))):
        #     out[linker.default_executable_env] = linker.get_executable()
        return out
    

class NMakeCompiler(MakeCompiler):
    toolname = 'nmake'
    platforms = ['Windows']
    default_flags = ['/NOLOGO']
    flag_options = OrderedDict([('makefile', '/f')])
    default_executable = None
    default_linker = None  # Force linker to be initialized with the same name

    @classmethod
    def language_version(cls, **kwargs):  # pragma: windows
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
        return out.split('Copyright')[0]
    

class MakeModelDriver(CompiledModelDriver):
    r"""Class for running make file compiled drivers. Before running the
    make command, the necessary compiler & linker flags for the interface's
    C/C++ library are stored the environment variables YGGCCFLAGS and YGGLDFLAGS
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
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        makefile (str): Path to make file either relative to makedir or absolute.
        makedir (str): Directory where make should be invoked from.
        target (str): Name of executable that should be created and called.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'Makefile for compilation.')
    _schema_properties = copy.deepcopy(MakeCompiler._schema_properties)
    language = 'make'
    base_languages = ['c']

    def parse_arguments(self, args):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.

        """
        # Set makedir before passing to parent class so that makedir is used
        # to normalize the model file path rather than the working directory
        # which may be different.
        if not os.path.isabs(self.makefile):
            if self.makedir is not None:
                self.makefile = os.path.normpath(
                    os.path.join(self.makedir, self.makefile))
            else:
                src_dir = os.path.dirname(args[0])
                if not os.path.isabs(src_dir):
                    src_dir = os.path.join(self.working_dir, src_dir)
                for x in [self.working_dir, src_dir]:
                    y = os.path.normpath(os.path.join(x, self.makefile))
                    if os.path.isfile(y):
                        self.makefile = y
                        break
        if self.makedir is None:
            self.makedir = os.path.dirname(self.makefile)
        kwargs = dict(default_model_dir=self.makedir)
        super(MakeModelDriver, self).parse_arguments(args, **kwargs)
        
    @classmethod
    def is_source_file(cls, fname):
        r"""Determine if the provided file name points to a source files for
        the associated programming language by checking the extension.

        Args:
            fname (str): Path to file.

        Returns:
            bool: True if the provided file is a source file, False otherwise.

        """
        compiler = cls.get_tool('compiler')
        for lang in compiler.languages:
            if lang == cls.language:
                continue
            drv = components.import_component('model', lang)
            if drv.is_source_file(fname):
                return True
        return False
        
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
                                      makefile=self.makefile,
                                      working_dir=self.working_dir, **kwargs)
        else:
            default_kwargs = dict(skip_interface_flags=True,
                                  # source_files=[],  # Unknown source files, use target
                                  for_model=False,  # flags are in environment
                                  working_dir=self.makedir,
                                  makefile=self.makefile,
                                  env=self.set_env(for_compile=True))
            if target is not None:
                default_kwargs['target'] = target
            for k, v in default_kwargs.items():
                kwargs.setdefault(k, v)
            return super(MakeModelDriver, self).compile_model(**kwargs)
        
    def set_env(self, for_compile=False):
        r"""Get environment variables that should be set for the model process.

        Args:
            for_compile (bool, optional): If True, environment variables are set
                that are necessary for compiling. Defaults to False.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(MakeModelDriver, self).set_env(for_compile=for_compile)
        if not for_compile:
            # TODO: Pass language?
            out = CModelDriver.update_ld_library_path(out)
        return out
        
    def cleanup(self):
        r"""Remove compiled executable."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model(target='clean')
        super(MakeModelDriver, self).cleanup()
