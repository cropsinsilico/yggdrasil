import os
import glob
import copy
from yggdrasil import components, constants
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, _tool_registry)


class BuildModelDriver(CompiledModelDriver):
    r"""Class for running build file compiled drivers.

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (make target)
            and any arguments for the executable or source files that
            the model will be built from.
        buildfile (str, optional): Path to the file containing build
            instructions. Can be absolute or relative to working_dir,
            compile_working_dir (if provided), builddir (if provided),
            or the source directory containing the model source files
            that will be built.
        builddir (str, optional): Path to the directory that will contain
            build products. Can be absolute or relative to the directory
            containing buildfile. Defaults to builddir_base. If builddir
            is not provided to the build tool as a command line flag,
            compile_working_dir will be set to builddir.
        sourcedir (str, optional0: Path to the directory that contains
            source files. Can be absolute or relative to working_dir.
            If not provided, it will be determined from args.
        target (str, optional): Target that should be built to create the
            model executable. Defaults to None.
        target_language (str, optional): Language that the target is
            written in. Defaults to None and will be set based on the
            source files provided.
        target_compiler (str, optional): Compilation tool that should be
            used to compile the target language. Defaults to None and
            will be set based on the selected language driver.
        target_linker (str, optional): Compilation tool that should be
            used to link the target language. Defaults to None and will
            be set based on the selected language driver.
        target_archiver (str, optional): Compilation tool that should be
            used to link the target language. Defaults to None and will
            be set based on the selected language driver.
        target_compiler_flags (list, optional): Compilation flags that
            should be passed to the target language compiler. Defaults
            to [].
        target_linker_flags (list, optional): Linking flags that should
            be passed to the target language linker. Defaults to [].
        target_archiver_flags (list, optional): Linking flags that should
            be passed to the target language archiver. Defaults to [].
        env_compiler (str, optional): Environment variable where the
            compiler executable should be stored for use within the
            Makefile. If not provided, this will be determined by the
            target language driver.
        env_compiler_flags (str, optional): Environment variable where
            the compiler flags should be stored (including those required
            to compile against the |yggdrasil| interface). If not
            provided, this will be determined by the target language
            driver.
        env_linker (str, optional): Environment variable where the linker
            executable should be stored for use within the Makefile. If
            not provided, this will be determined by the target language
            driver.
        env_linker_flags (str, optional): Environment variable where the
            linker flags should be stored (including those required to
            link against the |yggdrasil| interface). If not provided,
            this will be determined by the target language driver.
        env_archiver (str, optional): Environment variable where the
            archiver executable should be stored for use within the
            Makefile. If not provided, this will be determined by the
            target language driver.
        env_archiver_flags (str, optional): Environment variable where
            the archiver flags should be stored (including those required
            to link against the |yggdrasil| interface). If not provided,
            this will be determined by the target language driver.
        **kwargs: Additional keyword arguments are passed to parent
            class.

    Attributes:
        buildfile (str): Path to file containing build instructions.
        builddir (str): Path to directory where build products will be
            saved.
        sourcedir (str): Path to directory where source files are
            located.
        target (str): Name of executable that should be created and
            called.
        target_language (str): Language that the target is written in.
        target_language_driver (ModelDriver): Language driver for the
            target language.
        target_compiler (str): Compilation tool that should be used to
            compile the target language.
        target_linker (str): Compilation tool that should be used to
            link the target language.
        target_archiver (str): Compilation tool that should be used to
            archive the target language.
        target_compiler_flags (list): Compilation flags that should be
            passed to the target language compiler.
        target_linker_flags (list): Linking flags that should be passed
            to the target language linker.
        target_archiver_flags (list): Archiving flags that should be
            passed to the target language archiver.
        env_compiler (str): Compiler environment variable.
        env_compiler_flags (str): Compiler flags environment variable.
        env_linker (str): Linker environment variable.
        env_linker_flags (str): Linker flags environment variable.
        env_archiver (str): Archiver environment variable.
        env_archiver_flags (str): Archiver flags environment variable.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are
            available.

    """
    _schema_properties = {
        'buildfile': {'type': 'string'},
        'builddir': {'type': 'string'},
        'target': {'type': 'string'},
        'target_language': {'type': 'string'},
        'sourcedir': {'type': 'string'}}
    executable_type = 'build'
    supported_comms = ['ipc', 'zmq']
    full_language = False
    is_build_tool = True
    buildfile_base = None
    builddir_base = 'build'
    allow_parallel_build = False
    basetool = 'builder'
    default_model_libtype = 'build'
    target_basetool = 'compiler'
    target_flags_in_env = True
    comms_implicit = True
    default_target = None

    def __init__(self, *args, **kwargs):
        self.target_dep = None
        self.target_language_driver = None
        super(BuildModelDriver, self).__init__(*args, **kwargs)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class
        attributes prior to registration including things like platform
        dependent properties and checking environment variables for
        default settings.
        """
        CompiledModelDriver.before_registration(cls)
        cls.target_tooltypes = _tool_registry.tooltypes(
            cls.target_basetool)
        if 'disassembler' in cls.target_tooltypes:
            cls.target_tooltypes.remove('disassembler')
        cls._schema_properties = copy.deepcopy(cls._schema_properties)
        for k in cls.target_tooltypes:
            cls._schema_properties[f'target_{k}'] = {
                'type': 'string',
                'description': (f'Name of {k} that should be used to '
                                f'build the model')
            }
            cls._schema_properties[f'target_{k}_flags'] = {
                'type': 'array', 'items': {'type': 'string'},
                'default': [],
                'description': (f'Flags that should be passed to the '
                                f'{k} when building the model')
            }
            cls._schema_properties[f'env_{k}'] = {
                'type': 'string',
                'description': (f'Environment variable that the {k} '
                                f'executable path should be stored in '
                                f'when building the model')
            }
            cls._schema_properties[f'env_{k}_flags'] = {
                'type': 'string',
                'description': (f'Environment variable that the {k} '
                                f'flags should be stored in when '
                                f'building the model')
            }
        
    def parse_arguments(self, args, **kwargs):
        r"""Sort arguments based on their syntax to determine if an
        argument is a source file, compilation flag, or runtime
        option/flag that should be passed to the model executable.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        """
        # Set builddir before passing to parent class so that builddir is
        # used to normalize the model file path rather than the working
        # directory which may be different.
        if isinstance(args, (str, bytes)):
            args = args.split()
        default_attr = [('target_language_driver', None),
                        ('target_compiler', None)]
        for k, v in default_attr:
            if not hasattr(self, k):
                setattr(self, k, v)
        # Directory that compilation should be called from
        # Needs to be called before used for buildfile search
        if ((isinstance(self.compile_working_dir, str)
             and not os.path.isabs(self.compile_working_dir))):
            self.compile_working_dir = os.path.realpath(
                os.path.join(self.working_dir, self.compile_working_dir))
        # Source directory
        if self.sourcedir is None:
            self.sourcedir = os.path.dirname(args[0])
        if not os.path.isabs(self.sourcedir):
            self.sourcedir = os.path.normpath(
                os.path.realpath(os.path.join(self.working_dir,
                                              self.sourcedir)))
        model_is_source = self.is_source_file(args[0])
        if not model_is_source:
            if os.path.dirname(args[0]):
                self.builddir = os.path.dirname(args[0])
            elif self.target is None:
                self.target = args[0]
        # Target
        if self.target is None:
            self.target = self.default_target
        # Build file
        if self.buildfile is None:
            self.buildfile = self.buildfile_base
        if not os.path.isabs(self.buildfile):
            for x in set([self.working_dir, self.sourcedir,
                          self.builddir, self.compile_working_dir]):
                if x is not None:
                    y = os.path.normpath(os.path.join(x, self.buildfile))
                    if self.is_valid_buildfile(y):
                        self.buildfile = y
                        break
        # Build directory
        if self.builddir is None:
            self.builddir = self.builddir_base
        if not os.path.isabs(self.builddir):
            self.builddir = os.path.realpath(
                os.path.join(os.path.dirname(self.buildfile),
                             self.builddir))
        # Compilation directory
        if 'buildir' not in self.get_tool_instance('basetool').flag_options:
            self.compile_working_dir = self.builddir
        elif self.compile_working_dir is None:
            self.compile_working_dir = os.path.dirname(self.buildfile)
        if not os.path.isabs(self.compile_working_dir):
            self.compile_working_dir = os.path.realpath(
                os.path.join(self.working_dir, self.compile_working_dir))
        if not model_is_source:
            kwargs.setdefault('default_model_dir', self.builddir)
        super(BuildModelDriver, self).parse_arguments(args, **kwargs)

    @classmethod
    def is_valid_buildfile(cls, fname):
        r"""Determine if a file is a valid build file.

        Args:
            fname (str): File to check.

        Returns:
            bool: True if fname is valid, False otherwise.

        """
        return os.path.isfile(fname)

    @classmethod
    def get_buildfile_lock(cls, **kwargs):
        r"""Get a lock for a buildfile to prevent simultaneous access,
        creating one as necessary."""
        if kwargs.get('instance', None):
            kwargs.setdefault('fname', kwargs['instance'].buildfile)
        return super(BuildModelDriver, cls).get_buildfile_lock(**kwargs)
    
    @classmethod
    def get_source_dir(cls, fname=None, source_dir=None):
        if source_dir is None:
            if isinstance(fname, str):
                if os.path.isdir(fname):
                    source_dir = fname
                else:
                    source_dir = os.path.dirname(fname)
            else:  # pragma: debug
                raise RuntimeError("No source file/dir provided")
        return source_dir

    @classmethod
    def get_language_for_buildfile(cls, buildfile, target=None):  # pragma: debug
        r"""Determine the target language based on the contents of a
        build file.

        Args:
            buildfile (str): Full path to the build configuration file.
            target (str, optional): Target that will be built. Defaults
                to None and the default target in the build file will be
                used.

        """
        raise ValueError("Could not determine source from the buildfile")

    @classmethod
    def get_language_for_source(cls, fname=None, buildfile=None,
                                languages=None, early_exit=False,
                                call_base=False, **kwargs):
        r"""Determine the language that can be used with the provided
        source file(s). If more than one language applies to a set of
        multiple files, the language that applies to the most files is
        returned.

        Args:
            fname (str, list): The full path to one or more files. If
                more than one is provided, they are iterated over.
            buildfile (str, optional): Full path to the build
                configuration file. Defaults to None and will be
                searched for.
            languages (list, optional): The list of languages that are
                acceptable. Defaults to None and any language will be
                acceptable.
            early_exit (bool, optional): If True, the first language
                identified will be returned if fname is a list of files.
                Defaults to False.
            source_dir (str, optional): Full path to the directory
                containing the source files. Defaults to None and is
                determiend from fname.
            buildfile (str, optional): Full path to the build
                configuration file. Defaults to None and will be
                searched for.
            target (str, optional): The build target. Defaults to None.
            call_base (bool, optional): If True, the base class's method
                is called directly. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            str: The language that can operate on the specified file.

        """
        if not fname:
            fname = None
        try_list = []
        if not (call_base or isinstance(fname, list)):
            source_dir = kwargs.get('source_dir', None)
            if fname:
                source_dir = cls.get_source_dir(
                    fname, source_dir=source_dir)
            if source_dir == fname:
                fname = None
            if (buildfile is None) and source_dir and cls.buildfile_base:
                buildfile = os.path.join(source_dir, cls.buildfile_base)
            if isinstance(buildfile, str) and os.path.isfile(buildfile):
                try:
                    return cls.get_language_for_buildfile(
                        buildfile, target=kwargs.get('target', None))
                except ValueError:  # pragma: debug
                    pass
                if source_dir is None:
                    source_dir = os.path.dirname(buildfile)
            if source_dir:
                try_list += sorted(
                    list(glob.glob(os.path.join(source_dir, '*'))))
            if fname is not None:
                try_list = [fname, try_list]
                early_exit = True
            call_base = True
        else:
            try_list = fname
        if languages is None:
            languages = constants.LANGUAGES['compiled']
        return super(BuildModelDriver, cls).get_language_for_source(
            try_list, early_exit=early_exit, buildfile=buildfile,
            languages=languages, call_base=call_base, **kwargs)

    def init_model_dep(self, **kwargs):
        r"""Set the language of the target being compiled (usually the
        same as the language associated with this driver.

        Returns:
            str: Name of language.

        """
        if self.target_language is None:
            try:
                self.target_language = self.get_language_for_source(
                    fname=self.model_src, source_dir=self.sourcedir,
                    buildfile=self.buildfile, target=self.target)
            except ValueError:
                self.target_language = 'c'
        if self.target_language is not None:
            if self.target_language_driver is None:
                self.target_language_driver = (
                    components.import_component(
                        'model', self.target_language))
        if self.target_compiler is None:
            self.target_compiler = self.target_language_driver.get_tool(
                'compiler', return_prop='name')
        if (((not self.model_src)
             and self.target_language_driver.language_ext)):
            self.model_src = (
                os.path.splitext(self.model_file)[0]
                + self.target_language_driver.language_ext[0])
        super(BuildModelDriver, self).init_model_dep(**kwargs)
        return self.target_language

    @classmethod
    def compile_dependencies(cls, dep=None, **kwargs):
        r"""Compile any required internal libraries, including the interface."""
        if dep is None:
            for k in constants.LANGUAGES['compiled']:
                drv = components.import_component('model', k)
                drv.compile_dependencies(build_driver=cls, **kwargs)
        super(BuildModelDriver, cls).compile_dependencies(
            dep=dep, **kwargs)
        
    @classmethod
    def create_dep(cls, without_wrapper=False, **kwargs):
        r"""Get a CompilationDependency instance associated with the
        driver.

        Args:
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency.create_target

        Returns:
            CompilationDependency: New compilation target.

        """
        kwargs.update(
            target_flags_in_env=(without_wrapper
                                 or cls.target_flags_in_env),
            target_build_driver=cls)
        if kwargs.get('dont_build', kwargs.get('dont_link', False)):
            kwargs['target_flags_in_env'] = False
        return super(BuildModelDriver, cls).create_dep(**kwargs)
        
    def create_model_dep(self, attr_param=None, **kwargs):
        r"""Get a CompilationDependency instance associated with the
        model.

        Args:
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency.create_target with defaults set
                based on the model's parameters.

        Returns:
            CompilationDependency: New compilation target for the model.

        """
        if attr_param is None:
            attr_param = []
        attr_param += ['target_language', 'buildfile']
        kwargs.setdefault('working_dir', self.compile_working_dir)
        kwargs.setdefault('suffix', '')
        kwargs.setdefault('no_suffix', True)
        kwargs.setdefault('target_driver', self.target_language_driver)
        if self.model_src:
            kwargs.setdefault('target_source', self.model_src)
        if kwargs.get('out', False):
            kwargs.setdefault('target_output', kwargs.pop('out'))
        elif self.model_file:
            kwargs.setdefault('target_output', self.model_file)
        elif self.builddir:
            kwargs.setdefault('target_builddir', self.builddir)
        if kwargs.get('target_output', False):
            kwargs.setdefault('output', kwargs['target_output'])
            assert kwargs['target_output'] == kwargs['output']
        elif kwargs.get('output', False):
            kwargs.setdefault('target_output', kwargs['output'])
            assert kwargs['target_output'] == kwargs['output']
        for k in self.target_tooltypes:
            kwargs.setdefault(f'target_{k}',
                              getattr(self, f'target_{k}'))
            flags = getattr(self, f'target_{k}_flags', None)
            if flags:
                kwargs.setdefault(f'target_{k}_flags', flags)
            for kk in [f'env_{k}', f'env_{k}_flags']:
                x = getattr(self, kk, None)
                if x:
                    kwargs.setdefault(f'target_{kk}', x)
        return super(BuildModelDriver, self).create_model_dep(
            attr_param=attr_param, **kwargs)
        
    @classmethod
    def is_source_file(cls, fname):
        r"""Determine if the provided file name points to a source files
        for the associated programming language by checking the
        extension.

        Args:
            fname (str): Path to file.

        Returns:
            bool: True if the provided file is a source file, False
                otherwise.

        """
        for lang in constants.LANGUAGES['compiled']:
            drv = components.import_component('model', lang)
            if drv.is_source_file(fname):
                return True
        return False

    @classmethod
    def create_imports(cls, dep, imp, **kwargs):
        r"""Modify the build file to import the provided library.

        Args:
             dep (CompilationDependency): Dependency to add imports to in
                 its build file.
             imp (object): Information about the library that should be
                 imported as output by create_exports.
             **kwargs: Additional keyword arguments are ignored.

        """
        pass

    @classmethod
    def create_exports(cls, dep, **kwargs):
        r"""Create an exports file for the provided dependency.

        Args:
            dep (CompilationDependency): Dependency to create exports
                file for.
            **kwargs: Additional keyword arguments are passed to
                dep.tool_kwargs.

        """
        pass

    def cleanup(self):
        r"""Remove compiled executable."""
        if ((self.remove_products and self.model_file is not None
             and os.path.isfile(self.model_file))):
            self.build_model(target='clean')
        super(BuildModelDriver, self).cleanup()

    @classmethod
    def fix_path(cls, path, for_env=False, is_gnu=False):
        r"""Update a path.

        Args:
            path (str): Path that should be formatted.
            for_env (bool, optional): If True, the path is formatted for
                use in an environment variable. Defaults to False.
            is_gnu (bool, optional): If True, the tool is a GNU tool.

        Returns:
            str: Updated path.

        """
        return path
