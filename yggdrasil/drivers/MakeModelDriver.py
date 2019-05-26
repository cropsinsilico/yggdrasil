import os
from collections import OrderedDict
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase)
from yggdrasil.drivers.CModelDriver import CModelDriver


_default_makefile = 'Makefile'


class MakeCompiler(CompilerBase):
    r"""Make configuration tool."""
    name = 'make'
    languages = ['make']
    platforms = ['MacOS', 'Linux']
    default_flags = ['--always-make']  # Always overwrite
    flag_options = OrderedDict([('makefile', {'key': '-f', 'position': 0})])
    output_key = ''
    no_separate_linking = True
    default_archiver = False

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
    

class NMakeCompiler(MakeCompiler):
    name = 'nmake'
    platforms = ['Windows']
    default_flags = ['/NOLOGO']
    flag_options = OrderedDict([('makefile', '/f')])
    default_linker = None  # Force linker to be initialized with the same name


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
    _schema_properties = {
        'makefile': {'type': 'string', 'default': _default_makefile},
        'makedir': {'type': 'string'},  # default will depend on makefile
        'target': {'type': 'string'}}
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
                self.makefile = os.path.normpath(
                    os.path.join(self.working_dir, self.makefile))
        if self.makedir is None:
            self.makedir = os.path.dirname(self.makefile)
        kwargs = dict(default_model_dir=self.makedir)
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
                                      makefile=self.makefile,
                                      working_dir=self.working_dir, **kwargs)
        else:
            default_kwargs = dict(source_files=[],  # Unknown source files, use target
                                  skip_interface_flags=True,
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
        out = super(MakeModelDriver, self).set_env()
        if for_compile:
            # TODO: Special flags for C++?
            compile_flags = CModelDriver.get_compiler_flags(
                for_model=True, logging_level=self.logger.getEffectiveLevel(),
                skip_defaults=True)
            linker_flags = CModelDriver.get_linker_flags(
                for_model=True, skip_defaults=True)
            out['YGGCCFLAGS'] = ' '.join(compile_flags)
            out['YGGLDFLAGS'] = ' '.join(linker_flags)
        else:
            out = CModelDriver.update_ld_library_path(out)
        return out
        
    def remove_products(self):
        r"""Delete products produced during the compilation process."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model(target='clean')
        super(MakeModelDriver, self).remove_products()
