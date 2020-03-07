import os
import copy
import glob
from yggdrasil import components
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
        build_language = cls.build_language
        for x in cls.languages:
            if x != build_language:
                return x
        raise ValueError("Could not determine a default target language "
                         "for build tool '%s'" % cls.toolname)  # pragma: debug

    @classmethod
    def set_env(cls, language=None, language_driver=None, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
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
        out = super(BuildToolBase, cls).set_env(**kwargs)
        if language_driver is None:
            if language is None:
                language = cls.get_default_target_language()
            language_driver = components.import_component('model', language)
        compiler = language_driver.get_tool('compiler')
        out = compiler.set_env(existing=out)
        return out


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

    Class Attributes:
        built_where_called (bool): If True, it is assumed that compilation
            output will be saved in the same directory from which the
            compilation command is issued.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    base_languages = ['c', 'c++']
    built_where_called = False
    sourcedir_as_sourcefile = False

    def __init__(self, *args, **kwargs):
        self.target_language_driver = None
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
        if self.sourcedir_as_sourcefile:
            self.source_files = [self.sourcedir]
        super(BuildModelDriver, self).parse_arguments(args, **kwargs)

    def set_target_language(self):
        r"""Set the language of the target being compiled (usually the same
        as the language associated with this driver.

        Returns:
            str: Name of language.

        """
        source_dir = self.sourcedir
        if self.target_language is None:
            # Get file form cmakelists files
            try_list = sorted(list(glob.glob(os.path.join(source_dir, '*'))))
            early_exit = False
            if self.model_src is not None:
                try_list = [self.model_src, try_list]
                early_exit = True
            languages = copy.deepcopy(self.get_tool_instance('compiler').languages)
            languages.remove(self.language)
            try:
                self.target_language = self.get_language_for_source(
                    try_list, early_exit=early_exit, languages=languages)
            except ValueError:
                pass
            # Try to compile C as C++
            # if self.target_language == 'c':
            #     self.target_language = 'c++'
        if (((self.target_language_driver is None)
             and (self.target_language is not None))):
            self.target_language_driver = components.import_component(
                'model', self.target_language)
        return self.target_language
        
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
        
    def compile_model(self, **kwargs):
        r"""Compile model executable(s).

        Args:
            **kwargs: Keyword arguments are passed on to the parent class's
                method.

        """
        if self.target_language_driver is not None:
            self.target_language_driver.compile_dependencies()
        kwargs['working_dir'] = self.compile_working_dir
        return super(BuildModelDriver, self).compile_model(**kwargs)
        
    def cleanup(self):
        r"""Remove compiled executable."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model(target='clean')
        super(BuildModelDriver, self).cleanup()

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
            kwargs['compile_kwargs']['language'] = self.target_language
            kwargs['compile_kwargs']['language_driver'] = self.target_language_driver
        out = super(BuildModelDriver, self).set_env(**kwargs)
        if not kwargs.get('for_compile', False):
            if hasattr(self.target_language_driver, 'update_ld_library_path'):
                self.target_language_driver.update_ld_library_path(out)
        return out
