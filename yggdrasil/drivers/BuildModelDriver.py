import os
import glob
from yggdrasil import components, constants
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase)


class BuildToolBase(CompilerBase):
    r"""Base class for build tools."""

    is_build_tool = True
    build_language = None

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilerBase.before_registration(cls)
        if cls.build_language is None:
            cls.build_language = cls.toolname
        
    @classmethod
    def get_default_target_language(cls):
        r"""Determine the default target language for the build tool.
        Unless otherwise specified, this will be the first language in
        the 'languages' attribute that is not the build tool.

        Returns:
            str: Name of the default target language.

        """
        return 'c'

    @classmethod
    def get_tool_suffix(cls):
        r"""Get the string that should be added to tool products based on the
        tool used.

        Returns:
            str: Suffix that should be added to tool products to indicate the
                tool used.

        """
        return ""


class BuildModelDriver(CompiledModelDriver):
    r"""Class for running build file compiled drivers.

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (make target) and
            any arguments for the executable.
        target (str, optional): Make target that should be built to create the
            model executable. Defaults to None.
        target_language (str, optional): Language that the target is written in.
            Defaults to None and will be set based on the source files provided.
        target_compiler (str, optional): Compilation tool that should be used
            to compile the target language. Defaults to None and will be set
            based on the selected language driver.
        target_linker (str, optional): Compilation tool that should be used
            to link the target language. Defaults to None and will be set
            based on the selected language driver.
        target_compiler_flags (list, optional): Compilation flags that should
            be passed to the target language compiler. Defaults to [].
        target_linker_flags (list, optional): Linking flags that should
            be passed to the target language linker. Defaults to [].
        env_compiler (str, optional): Environment variable where the compiler
            executable should be stored for use within the Makefile. If not
            provided, this will be determined by the target language driver.
        env_compiler_flags (str, optional): Environment variable where the
            compiler flags should be stored (including those required to compile
            against the |yggdrasil| interface). If not provided, this will
            be determined by the target language driver.
        env_linker (str, optional): Environment variable where the linker
            executable should be stored for use within the Makefile. If not
            provided, this will be determined by the target language driver.
        env_linker_flags (str, optional): Environment variable where the
            linker flags should be stored (including those required to link
            against the |yggdrasil| interface). If not provided, this will
            be determined by the target language driver.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        buildfile (str): Path to file containing build instructions.
        builddir (str): Path to directory where build products will be saved.
        sourcedir (str): Path to directory where source files are located.
        compiledir (str): Path to directory where compilation call should be
            made from. Defaults to working_dir.
        target (str): Name of executable that should be created and called.
        target_language (str): Language that the target is written in.
        target_language_driver (ModelDriver): Language driver for the target
            language.
        target_compiler (str): Compilation tool that should be used to
            compile the target language.
        target_linker (str): Compilation tool that should be used to
            link the target language.
        target_compiler_flags (list): Compilation flags that should be
            passed to the target language compiler.
        target_linker_flags (list): Linking flags that should be passed
            to the target language linker.
        env_compiler (str): Compiler environment variable.
        env_compiler_flags (str): Compiler flags environment variable.
        env_linker (str): Linker environment variable.
        env_linker_flags (str): Linker flags environment variable.

    Class Attributes:
        built_where_called (bool): If True, it is assumed that compilation
            output will be saved in the same directory from which the
            compilation command is issued.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """
    _schema_properties = {
        'buildfile': {'type': 'string'},
        'builddir': {'type': 'string'},
        'target': {'type': 'string'},
        'target_language': {'type': 'string'},
        'target_compiler': {'type': 'string'},
        'target_linker': {'type': 'string'},
        'target_compiler_flags': {'type': 'array',
                                  'items': {'type': 'string'}},
        'target_linker_flags': {'type': 'array',
                                'items': {'type': 'string'}},
        'env_compiler': {'type': 'string'},
        'env_compiler_flags': {'type': 'string'},
        'env_linker': {'type': 'string'},
        'env_linker_flags': {'type': 'string'}}
    base_languages = ['c']
    built_where_called = False
    sourcedir_as_sourcefile = False
    full_language = False
    is_build_tool = True
    use_env_vars = True
    isolate_library_flags = False

    def __init__(self, *args, **kwargs):
        self.target_language_driver = None
        self._target_language_info = None
        super(BuildModelDriver, self).__init__(*args, **kwargs)

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        for k in ['linker', 'archiver']:
            if k in cls._config_keys:
                cls._config_keys.remove(k)
        if getattr(cls, 'default_compiler', None) is None:
            cls.default_compiler = cls.language
        CompiledModelDriver.after_registration(cls, **kwargs)
        
    def parse_arguments(self, args, **kwargs):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        # Set builddir before passing to parent class so that builddir is used
        # to normalize the model file path rather than the working directory
        # which may be different.
        default_attr = [('target_language_driver', None),
                        ('target_compiler', None),
                        ('buildfile', None),
                        ('builddir', None),
                        ('sourcedir', None),
                        ('compile_working_dir', None),
                        ('builddir_base', '.'),
                        ('buildfile_base', None)]
        for k, v in default_attr:
            if not hasattr(self, k):
                setattr(self, k, v)
        # Directory that compilation should be called from
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
        if self.sourcedir_as_sourcefile:
            self.source_files = [self.sourcedir]
        # Build file
        if self.buildfile is None:
            self.buildfile = self.buildfile_base
        if not os.path.isabs(self.buildfile):
            for x in set([self.working_dir, self.sourcedir,
                          self.builddir, self.compile_working_dir]):
                if x is not None:
                    y = os.path.normpath(os.path.join(x, self.buildfile))
                    if os.path.isfile(y):
                        self.buildfile = y
                        break
        # Compilation directory
        if self.compile_working_dir is None:
            self.compile_working_dir = os.path.dirname(self.buildfile)
        if not os.path.isabs(self.compile_working_dir):
            self.compile_working_dir = os.path.realpath(
                os.path.join(self.working_dir, self.compile_working_dir))
        # Build directory
        if self.builddir is None:
            if self.built_where_called:
                self.builddir = self.compile_working_dir
            else:
                self.builddir = os.path.join(self.sourcedir, self.builddir_base)
        if not os.path.isabs(self.builddir):
            self.builddir = os.path.realpath(os.path.join(self.working_dir,
                                                          self.builddir))
        kwargs.setdefault('default_model_dir', self.builddir)
        super(BuildModelDriver, self).parse_arguments(args, **kwargs)

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
    def get_language_for_source(cls, fname=None, languages=None,
                                early_exit=False, call_base=False, **kwargs):
                                
        r"""Determine the language that can be used with the provided source
        file(s). If more than one language applies to a set of multiple files,
        the language that applies to the most files is returned.

        Args:
            fname (str, list): The full path to one or more files. If more than
                one is provided, they are iterated over.
            languages (list, optional): The list of languages that are acceptable.
                Defaults to None and any language will be acceptable.
            early_exit (bool, optional): If True, the first language identified
                will be returned if fname is a list of files. Defaults to False.
            source_dir (str, optional): Full path to the directory containing
                the source files. Defaults to None and is determiend from
                fname.
            buildfile (str, optional): Full path to the CMakeLists.txt file.
                Defaults to None and will be searched for.
            target (str, optional): The build target. Defaults to None.
            call_base (bool, optional): If True, the base class's method is
                called directly. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: The language that can operate on the specified file.

        """
        if not (call_base or isinstance(fname, list)):
            source_dir = cls.get_source_dir(
                fname, source_dir=kwargs.get('source_dir', None))
            if source_dir == fname:
                fname = None
            try_list = sorted(list(glob.glob(os.path.join(source_dir, '*'))))
            if fname is not None:
                try_list = [fname, try_list]
                early_exit = True
            call_base = True
        else:
            try_list = fname
        if languages is None:
            languages = constants.LANGUAGES['compiled']
        return super(BuildModelDriver, cls).get_language_for_source(
            try_list, early_exit=early_exit, languages=languages,
            call_base=call_base, **kwargs)

    def set_target_language(self):
        r"""Set the language of the target being compiled (usually the same
        as the language associated with this driver.

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
                self.target_language_driver = components.import_component(
                    'model', self.target_language)
            if self.target_compiler is None:
                self.target_compiler = self.target_language_driver.get_tool(
                    'compiler', return_prop='name')
        return self.target_language

    @classmethod
    def get_target_language_info(cls, target_language_driver=None,
                                 target_language='c',
                                 target_compiler=None, target_compiler_flags=None,
                                 target_linker=None, target_linker_flags=None,
                                 logging_level=None, **kwargs):
        r"""Get a dictionary of information about language compilation tools.

        Args:
            target_language_driver (ModelDriver, optional): Driver associated
                with the target language. If not provided, one will be created
                based on 'target_language'.
            target_language (str, optional): Language to get info for.
                Defaults to 'c'.
            **kwargs: Additional keyword arguments are added to the output
                dictionary.

        Returns:
            dict: Information about language compilers and linkers.

        """
        if target_language_driver is None:
            target_language_driver = components.import_component(
                'model', target_language)
        compiler = target_language_driver.get_tool(
            'compiler', toolname=target_compiler)
        if target_linker is None:
            linker = compiler.linker()
        else:
            linker = target_language_driver.get_tool(
                'linker', toolname=target_linker)
        out = {
            'compiler': compiler,
            'compiler_executable': compiler.get_executable(),
            'compiler_env': compiler.default_executable_env,
            'compiler_flags_env': compiler.default_flags_env,
            'linker': linker,
            'linker_executable': linker.get_executable(),
            'linker_env': linker.default_executable_env,
            'linker_flags_env': linker.default_flags_env,
        }
        compiler_kws = dict(
            toolname=compiler.toolname, skip_defaults=True,
            flags=target_compiler_flags,
            dont_skip_env_defaults=True, for_model=True, dry_run=True,
            dont_link=True, logging_level=logging_level)
        linker_kws = dict(
            # TODO: Linker cannot be passed directly as toolname or
            # get_linker_flags fails when it tries to find a compiler
            # with the provided toolname (dosn't work for windows where
            # the compiler has a different name than the linker)
            toolname=linker.toolname, skip_defaults=True,
            # toolname=compiler.toolname, skip_defaults=True,
            flags=target_linker_flags,
            dont_skip_env_defaults=True, for_model=True, dry_run=True)
        if cls.isolate_library_flags:
            out.update(library_flags=[],
                       external_library_flags=[],
                       internal_library_flags=[])
            compiler_kws.update(skip_sysroot=True,
                                dont_skip_env_defaults=False,
                                use_library_path=True)
            linker_kws.update(
                skip_library_libs=True,
                library_flags=out['library_flags'],
                dont_skip_env_defaults=False,
                use_library_path='external_library_flags',
                use_library_path_internal='internal_library_flags',
                external_library_flags=out['external_library_flags'],
                internal_library_flags=out['internal_library_flags'])
        out.update(
            compiler_flags=target_language_driver.get_compiler_flags(**compiler_kws),
            linker_flags=target_language_driver.get_linker_flags(**linker_kws))
        # yggdrasil requires that linking be done in C++
        if (((compiler.languages[0].lower() == 'c')
             and ('-lstdc++' not in out['linker_flags']))):
            out['linker_flags'].append('-lstdc++')
        if cls.isolate_library_flags:
            out['library_flags'] += (out['external_library_flags']
                                     + out['internal_library_flags'])
        out.update(**kwargs)
        return out
        
    @property
    def target_language_info(self):
        r"""dict: Information about the underlying language."""
        if self._target_language_info is None:
            kws = dict(
                target_language_driver=self.target_language_driver,
                target_compiler=self.target_compiler,
                target_compiler_flags=self.target_compiler_flags,
                target_linker=self.target_linker,
                target_linker_flags=self.target_linker_flags,
                logging_level=self.numeric_logging_level)
            for x in ['compiler', 'linker']:
                if getattr(self, 'env_%s' % x):
                    kws['%s_env' % x] = (
                        getattr(self, 'env_%s' % x))
                if getattr(self, 'env_%s_flags' % x):
                    kws['%s_flags_env' % x] = (
                        getattr(self, 'env_%s_flags' % x))
            self._target_language_info = self.get_target_language_info(**kws)
        return self._target_language_info
        
    @classmethod
    def is_source_file(cls, fname):
        r"""Determine if the provided file name points to a source files for
        the associated programming language by checking the extension.

        Args:
            fname (str): Path to file.

        Returns:
            bool: True if the provided file is a source file, False otherwise.

        """
        for lang in constants.LANGUAGES['compiled']:
            drv = components.import_component('model', lang)
            if drv.is_source_file(fname):
                return True
        return False

    def compile_model(self, **kwargs):
        r"""Compile model executable(s).

        Args:
            **kwargs: Keyword arguments are passed on to the parent class's
                method.

        """
        if (((self.target_language_driver is not None)
             and (not kwargs.get('dry_run', False)))):
            self.target_language_driver.compile_dependencies(
                toolname=self.target_compiler)
        kwargs['working_dir'] = self.compile_working_dir
        kwargs['target_compiler'] = self.target_compiler
        return super(BuildModelDriver, self).compile_model(**kwargs)
        
    def cleanup(self):
        r"""Remove compiled executable."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model(target='clean')
        super(BuildModelDriver, self).cleanup()

    @classmethod
    def call_compiler(cls, src, **kwargs):
        r"""Compile a source file into an executable or linkable object file,
        checking for errors.

        Args:
            src (str): Full path to source file.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Full path to compiled source.

        """
        if ('env' not in kwargs) and (not kwargs.get('dry_run', False)):
            kws = {}
            for k in ['target_language_driver', 'target_language',
                      'target_compiler', 'target_compiler_flags',
                      'target_linker', 'target_linker_flags', 'logging_level']:
                if k in kwargs:
                    kws[k] = kwargs[k]
            if not (('target_language_driver' in kws) or ('target_language' in kws)):
                if src:
                    kws['target_language'] = cls.get_language_for_source(src)
            language_info = cls.get_target_language_info(**kws)
            kwargs['env'] = cls.set_env_compiler(language_info=language_info)
        return super(BuildModelDriver, cls).call_compiler(src, **kwargs)
        
    @classmethod
    def set_env_compiler(cls, language_info=None, **kwargs):
        r"""Get environment variables that should be set for the compilation
        process.

        Args:
            language_info (dict): Language compilation tool information.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        assert(language_info is not None)
        kwargs['compiler'] = language_info['compiler']
        out = super(BuildModelDriver, cls).set_env_compiler(**kwargs)
        if language_info['compiler_env'] and language_info['compiler_executable']:
            out[language_info['compiler_env']] = language_info['compiler_executable']
        if language_info['linker_env'] and language_info['linker_executable']:
            out[language_info['linker_env']] = language_info['linker_executable']
        if cls.use_env_vars:
            if language_info['compiler_flags_env']:
                out[language_info['compiler_flags_env']] = ' '.join(
                    language_info['compiler_flags'])
            if language_info['linker_flags_env']:
                out[language_info['linker_flags_env']] = ' '.join(
                    language_info['linker_flags'])
        return out
    
    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        if kwargs.get('for_compile', False) and (self.target_language is not None):
            kwargs.setdefault('compile_kwargs', {})
            kwargs['compile_kwargs']['language_info'] = self.target_language_info
        out = super(BuildModelDriver, self).set_env(**kwargs)
        if not kwargs.get('for_compile', False):
            kwargs['existing'] = out
            if hasattr(self.target_language_driver, 'set_env_class'):
                out = self.target_language_driver.set_env_class(**kwargs)
        return out
