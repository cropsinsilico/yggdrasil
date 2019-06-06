import os
import re
import copy
import shutil
import logging
import glob
from collections import OrderedDict
from yggdrasil import platform, backwards, components
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, LinkerBase)
from yggdrasil.drivers import CModelDriver, CPPModelDriver


logger = logging.getLogger(__name__)


class CMakeConfigure(CompilerBase):
    r"""CMake configuration tool."""
    toolname = 'cmake'
    languages = ['cmake', 'c', 'c++']
    is_linker = False
    default_flags = []  # '-H']
    flag_options = OrderedDict([('definitions', '-D%s'),
                                ('sourcedir', ''),  # '-S'
                                ('builddir', '-B%s'),
                                ('configuration', '-DCMAKE_BUILD_TYPE=%s')])
    output_key = None
    compile_only_flag = None
    default_builddir = '.'
    default_archiver = False
    add_libraries = False
    product_files = ['Makefile', 'CMakeCache.txt',
                     'cmake_install.cmake', 'CMakeFiles']
    remove_product_exts = ['CMakeFiles']

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilerBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            if platform._is_64bit:
                cls.default_flags.append('-DCMAKE_GENERATOR_PLATFORM=x64')
            cls.product_files += ['ALL_BUILD.vcxproj',
                                  'ALL_BUILD.vcxproj.filters',
                                  'Debug', 'Release', 'Win32', 'Win64', 'x64',
                                  'ZERO_CHECK.vcxproj',
                                  'ZERO_CHECK.vcxproj.filters']
            cls.remove_product_exts += ['Debug', 'Release', 'Win32', 'Win64',
                                        'x64', '.dir']
        
    @classmethod
    def append_product(cls, products, src, new, **kwargs):
        r"""Append a product to the specified list along with additional values
        indicated by cls.product_exts.

        Args:
            products (list): List of of existing products that new product
                should be appended to.
            src (list): Input arguments to compilation call that was used to
                generate the output file (usually one or more source files).
            new (str): New product that should be appended to the list.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        kwargs.setdefault('new_dir', new)
        kwargs.setdefault('dont_append_src', True)
        return super(CMakeConfigure, cls).append_product(products, src,
                                                         new, **kwargs)
        
    @classmethod
    def get_output_file(cls, src, dont_link=False, dont_build=None,
                        sourcedir=None, builddir=None, working_dir=None,
                        **kwargs):
        r"""Determine the appropriate output file or directory that will result
        when configuring/building a given source directory.

        Args:
            src (str): Directory containing source files being compiled.
            dont_link (bool, optional): If True, the result assumes that the
                source is just compiled and not linked. If False, the result
                will be the final result after linking.
            dont_build (bool, optional): Alias for dont_link. If not None, this
                keyword overrides the value of dont_link. Defaults to None.
            sourcedir (str, optional): Directory where sources files are located.
                Defaults to None. If None, src will be used to determine the
                value.
            builddir (str, optional): Directory where build tree should be
                created. Defaults to None. If None, sourcedir will be used.
            working_dir (str, optional): Working directory where output file
                should be located. Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are ignored unless dont_link
                is False; then they are passed to get_linker_output_file

        Returns:
            str: Full path to file that will be produced.

        """
        if dont_build is not None:
            dont_link = dont_build
        if isinstance(src, list):
            src = src[0]
        if sourcedir is None:
            if os.path.isfile(src) or os.path.splitext(src)[-1]:
                sourcedir = os.path.dirname(src)
            else:
                sourcedir = src
        if builddir is None:
            builddir = os.path.normpath(os.path.join(sourcedir,
                                                     cls.default_builddir))
        if dont_link:
            out = builddir
            if (not os.path.isabs(out)) and (working_dir is not None):
                out = os.path.normpath(os.path.join(working_dir, out))
        else:
            out = super(CMakeConfigure, cls).get_output_file(
                src, dont_link=dont_link, sourcedir=sourcedir,
                builddir=builddir, working_dir=working_dir, **kwargs)
        return out

    @classmethod
    def get_flags(cls, sourcedir='.', builddir=None, **kwargs):
        r"""Get a list of configuration/generation flags.

        Args:
            sourcedir (str, optional): Directory containing the source files to
                be compiled and the target CMakeLists.txt file. Defaults to '.'
                (the current working directory).
            builddir (str, optional): Directory that will contain the build tree.
                Defaults to '.' (this current working directory).
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Compiler flags.

        Raises:
            RuntimeError: If dont_link is True and the provide outfile and
                builddir keyword arguments point to conflicting paths.
            ValueError: If 'include_dirs' is set ('sourcedir' should be used
                for cmake to specify the location of the source).

        """
        if kwargs.get('dont_link', False):
            if builddir is None:
                outfile = kwargs.get('outfile', None)
                if outfile is None:
                    builddir = os.path.normpath(os.path.join(sourcedir,
                                                             cls.default_builddir))
                else:
                    builddir = outfile
        # Pop target (used for build stage file name, but not for any other
        # part of the build stage)
        kwargs.pop('target', None)
        # Add conda prefix
        # conda_prefix = cls.get_conda_prefix()
        # if conda_prefix:
        #     kwargs.setdefault('definitions', [])
        #     kwargs['definitions'].append('CMAKE_PREFIX_PATH=%s'
        #                                  % os.path.join(conda_prefix, 'lib'))
        #     kwargs['definitions'].append('CMAKE_LIBRARY_PATH=%s'
        #                                  % os.path.join(conda_prefix, 'lib'))
        out = super(CMakeConfigure, cls).get_flags(sourcedir=sourcedir,
                                                   builddir=builddir, **kwargs)
        return out

    @classmethod
    def get_executable_command(cls, args, **kwargs):
        r"""Determine the command required to run the tool using the specified
        arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool. If
                skip_flags is False, these are treated as input files that will
                be used by the tool.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        assert(len(args) == 1)
        if not kwargs.get('skip_flags', False):
            sourcedir = kwargs.get('sourcedir', args[0])
            if sourcedir != args[0]:  # pragma: debug
                raise RuntimeError(("The argument list "
                                    "contents (='%s') and 'sourcedir' (='%s') "
                                    "keyword specify the same thing, but those "
                                    "provided do not match.")
                                   % (args[0], sourcedir))
            kwargs['sourcedir'] = args[0]
        return super(CMakeConfigure, cls).get_executable_command([], **kwargs)
    
    @classmethod
    def write_wrappers(cls, target=None, sourcedir=None,
                       target_language=None, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are ignored (only included to
               allow cascade from child classes).

        Returns:
            list: Full paths to any created wrappers.

        """
        if sourcedir is None:  # pragma: debug
            sourcedir = '.'
        out = super(CMakeConfigure, cls).write_wrappers(**kwargs)
        if target is None:
            include_base = 'ygg_cmake.txt'
        else:
            include_base = 'ygg_cmake_%s.txt' % target
        include_file = os.path.join(sourcedir, include_base)
        # import pprint
        # print('kwargs')
        # pprint.pprint(kwargs)
        kwargs['verbose'] = True
        if (target_language is not None) and ('driver' not in kwargs):
            kwargs['driver'] = components.import_component('model',
                                                           target_language)
        cls.create_include(include_file, target, **kwargs)
        if os.path.isfile(include_file):
            os.remove(include_file)
        return out
        
    @classmethod
    def create_include(cls, fname, target, compile_flags=None, linker_flags=None,
                       driver=None, logging_level=None, configuration='Release',
                       verbose=False, **kwargs):
        r"""Create CMakeList include file with necessary includes,
        definitions, and linker flags.

        Args:
            fname (str): File where the include file should be saved.
            target (str): Target that links should be added to.
            compile_flags (list, optional): Additional compile flags that
                should be set. Defaults to [].
            linker_flags (list, optional): Additional linker flags that
                should be set. Defaults to [].
            driver (CompiledModelDriver, optional): The CompiledModelDriver that
                should be used to get compiler/linker flags. Defaults to
                CModelDriver.
            logging_level (int, optional): Logging level that should be passed
                as a definition to the C compiler. Defaults to None and will be
                ignored.
            configuration (str, optional): Build type/configuration that should
                be built. Defaults to 'Release'. Only used on Windows to
                determin the standard library.
            verbose (bool, optional): If True, the contents of the created file
                are displayed. Defaults to False.
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            ValueError: If a linker or compiler flag cannot be interpreted.

        """
        if target is None:
            target = '${PROJECT_NAME}'
        if compile_flags is None:
            compile_flags = []
        if linker_flags is None:
            linker_flags = []
        if driver is None:  # pragma: debug
            driver = CModelDriver.CModelDriver
        use_library_path = True  # platform._is_win
        library_flags = []
        external_library_flags = []
        internal_library_flags = []
        compile_flags = driver.get_compiler_flags(
            skip_defaults=True,
            flags=compile_flags, use_library_path=use_library_path,
            dont_link=True, for_model=True, dry_run=True,
            logging_level=logging_level)
        linker_flags = driver.get_linker_flags(
            skip_defaults=True,
            flags=linker_flags, for_model=True, dry_run=True,
            use_library_path='external_library_flags',
            external_library_flags=external_library_flags,
            use_library_path_internal='internal_library_flags',
            internal_library_flags=internal_library_flags,
            skip_library_libs=True, library_flags=library_flags)
        lines = []
        preamble_lines = []
        library_flags += internal_library_flags + external_library_flags
        # Suppress warnings on windows about the security of strcpy etc.
        # and target x64 if the current platform is 64bit
        if platform._is_win:  # pragma: windows
            new_flags = ["/W4", "/EHsc", '/TP', "/nologo",
                         "-D_CRT_SECURE_NO_WARNINGS"]
            if configuration.lower() == 'debug':  # pragma: debug
                new_flags.append("/MTd")
            else:
                new_flags.append("/MT")
            for x in new_flags:
                if x not in compile_flags:
                    compile_flags.append(x)
        # Compilation flags
        for x in compile_flags:
            if x.startswith('-D'):
                preamble_lines.append('ADD_DEFINITIONS(%s)' % x)
            elif x.startswith('-I'):
                xdir = x.split('-I', 1)[-1]
                if platform._is_win:  # pragma: windows
                    xdir = xdir.replace('\\', re.escape('\\'))
                new_dir = 'INCLUDE_DIRECTORIES(%s)' % xdir
                if new_dir not in preamble_lines:
                    preamble_lines.append(new_dir)
            elif x.startswith('-std=c++') or x.startswith('/std=c++'):
                new_def = 'SET(CMAKE_CXX_STANDARD %s)' % x.split('c++')[-1]
                if new_def not in preamble_lines:
                    preamble_lines.append(new_def)
            elif x.startswith('-') or x.startswith('/'):
                new_def = 'ADD_DEFINITIONS(%s)' % x
                if new_def not in preamble_lines:
                    preamble_lines.append(new_def)
            else:
                raise ValueError("Could not parse compiler flag '%s'." % x)
        # Linker flags
        for x in linker_flags:
            if x.startswith('-l'):
                lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
            elif x.startswith('-L'):
                libdir = x.split('-L')[-1]
                if platform._is_win:  # pragma: windows
                    libdir = libdir.replace('\\', re.escape('\\'))
                preamble_lines.append('LINK_DIRECTORIES(%s)' % libdir)
            elif x.startswith('/LIBPATH:'):  # pragma: windows
                libdir = x.split('/LIBPATH:')[-1]
                if '"' in libdir:
                    libdir = libdir.split('"')[1]
                if platform._is_win:
                    libdir = libdir.replace('\\', re.escape('\\'))
                preamble_lines.append('LINK_DIRECTORIES(%s)' % libdir)
            elif os.path.isfile(x):
                library_flags.append(x)
            elif x.startswith('-') or x.startswith('/'):
                raise ValueError("Could not parse linker flag '%s'." % x)
            else:
                lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
        # Libraries
        for x in library_flags:
            xorig = x
            xd, xf = os.path.split(x)
            xl, xe = os.path.splitext(xf)
            xl = driver.get_tool('linker').libpath2libname(xf)
            if platform._is_win:  # pragma: windows
                x = x.replace('\\', re.escape('\\'))
                xd = xd.replace('\\', re.escape('\\'))
            xn = os.path.splitext(xl)[0]
            new_dir = 'LINK_DIRECTORIES(%s)' % xd
            if new_dir not in preamble_lines:
                preamble_lines.append(new_dir)
            if cls.add_libraries or (xorig in internal_library_flags):
                # if cls.add_libraries:  # pragma: no cover
                # Version adding library
                lines.append('if (NOT TARGET %s)' % xl)
                if xe.lower() in ['.so', '.dll', '.dylib']:  # pragma: no cover
                    lines.append('    ADD_LIBRARY(%s SHARED IMPORTED)' % xl)
                else:
                    lines.append('    ADD_LIBRARY(%s STATIC IMPORTED)' % xl)
                lines += ['    SET_TARGET_PROPERTIES(',
                          '        %s PROPERTIES' % xl,
                          # '        LINKER_LANGUAGE CXX',
                          # '        CXX_STANDARD 11',
                          '        IMPORTED_LOCATION %s)' % x,
                          'endif()',
                          'TARGET_LINK_LIBRARIES(%s %s)' % (target, xl)]
            else:
                # Version finding library
                lines.append('FIND_LIBRARY(%s_LIBRARY NAMES %s %s HINTS %s)'
                             % (xn.upper(), xf, xn, xd))
                lines.append('TARGET_LINK_LIBRARIES(%s ${%s_LIBRARY})'
                             % (target, xn.upper()))
        lines = preamble_lines + lines
        if verbose:  # pragma: debug
            logger.info('CMake include file:\n\t' + '\n\t'.join(lines))
        else:
            logger.debug('CMake include file:\n\t' + '\n\t'.join(lines))
        if fname is None:
            return lines
        else:
            if os.path.isfile(fname):  # pragma: debug
                os.remove(fname)
            with open(fname, 'w') as fd:
                fd.write('\n'.join(lines))

    
class CMakeBuilder(LinkerBase):
    r"""CMake build tool."""
    toolname = 'cmake'
    languages = ['cmake', 'c', 'c++']
    default_flags = []  # '--clean-first']
    output_key = None
    flag_options = OrderedDict([('builddir', {'key': '--build',
                                              'position': 0}),
                                ('target', '--target'),
                                ('configuration', '--config')])
    executable_ext = ''

    @classmethod
    def extract_kwargs(cls, kwargs, **kwargs_ex):
        r"""Extract linker kwargs, leaving behind just compiler kwargs.

        Args:
            kwargs (dict): Keyword arguments passed to the compiler that should
                be sorted into kwargs used by either the compiler or linker or
                both. Keywords that are not used by the compiler will be removed
                from this dictionary.
            **kwargs_ex: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Keyword arguments that should be passed to the linker.

        """
        kwargs_ex['add_kws_both'] = (kwargs.get('add_kws_both', [])
                                     + ['builddir', 'target'])
        return super(CMakeBuilder, cls).extract_kwargs(kwargs, **kwargs_ex)
        
    @classmethod
    def get_output_file(cls, obj, target=None, builddir=None, **kwargs):
        r"""Determine the appropriate output file that will result when bulding
        a given directory.

        Args:
            obj (str): Directory being built or a file in the directory being
                built.
            target (str, optional): Target that will be used to create the
                output file. Defaults to None. Target is required in order
                to determine the name of the file that will be created.
            builddir (str, optional): Directory where build tree should be
                created. Defaults to None and obj will used (if its a directory)
                or the directory containing obj will be used (if its a file).
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Full path to file that will be produced.

        Raises:
            RuntimeError: If target is None.

        """
        if builddir is None:
            if os.path.isfile(obj) or os.path.splitext(obj)[-1]:
                builddir = os.path.dirname(obj)
            else:
                builddir = obj
        if target is None:
            if os.path.isfile(obj) or os.path.splitext(obj)[-1]:
                target = os.path.splitext(os.path.basename(obj))[0]
            else:
                raise RuntimeError("Target is required.")
        elif target == 'clean':
            return target
        out = super(CMakeBuilder, cls).get_output_file(
            os.path.join(builddir, target), **kwargs)
        return out

    @classmethod
    def get_flags(cls, target=None, builddir=None, **kwargs):
        r"""Get a list of build flags for building a project using cmake.

        Args:
            target (str, optional): Target that should be built. Defaults to
                to None and is ignored.
            builddir (str, optional): Directory containing the build tree.
                Defaults to None and is set based on outfile is provided or
                cls.default_builddir if not.
                Defaults to '.' (which will be the current working directory).
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Linker flags.

        """
        outfile = kwargs.get('outfile', None)
        if outfile is not None:
            if target is None:
                target = os.path.splitext(os.path.basename(outfile))[0]
            if builddir is None:
                builddir = os.path.dirname(outfile)
        if builddir is None:
            builddir = CMakeConfigure.default_builddir
        out = super(CMakeBuilder, cls).get_flags(target=target,
                                                 builddir=builddir, **kwargs)
        return out

    @classmethod
    def get_executable_command(cls, args, **kwargs):
        r"""Determine the command required to run the tool using the specified
        arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool. If
                skip_flags is False, these are treated as input files that will
                be used by the tool.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        assert(len(args) == 1)
        if not kwargs.get('skip_flags', False):
            builddir = kwargs.get('builddir', args[0])
            if not os.path.isabs(builddir) and os.path.isabs(args[0]):
                builddir = os.path.join(os.path.dirname(args[0]), builddir)
            if builddir != args[0]:  # pragma: debug
                raise RuntimeError(("The argument list "
                                    "contents (='%s') and 'builddir' (='%s') "
                                    "keyword specify the same thing, but those "
                                    "provided do not match.")
                                   % (args[0], builddir))
            kwargs['builddir'] = args[0]
        return super(CMakeBuilder, cls).get_executable_command([], **kwargs)
    

class CMakeModelDriver(CompiledModelDriver):
    r"""Class for running cmake compiled drivers. Before running the
    cmake command, the cmake commands for setting the necessary compiler & linker
    flags for the interface's C/C++ library are written to a file called
    'ygg_cmake.txt' that should be included in the CMakeLists.txt file (after
    the target executable has been added).

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (cmake target) and
            any arguments for the executable.
        sourcedir (str, optional): Source directory to call cmake on. If not
            provided it is set to working_dir. This should be the directory
            containing the CMakeLists.txt file. It can be relative to
            working_dir or absolute.
        builddir (str, optional): Directory where the build should be saved.
            Defaults to <sourcedir>/build. It can be relative to working_dir
            or absolute.
        target (str, optional): Make target that should be built to create the
            model executable. Defaults to None.
        target_language (str, optional): Language that the target is written in.
            Defaults to None and will be set based on the source files provided.
        configuration (str, optional): Build type/configuration that should be
            built. Defaults to 'Release'.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        sourcedir (str): Source directory to call cmake on.
        builddir (str): Directory where the build should be saved.
        target (str): Name of executable that should be created and called.
        add_libraries (bool): If True, interface libraries and dependency
            libraries are added using CMake's ADD_LIBRARY directive. If False,
            interface libraries are found using FIND_LIBRARY.
        target_language (str): Language that the target is written in.
        target_language_driver (ModelDriver): Language driver for the target
            language.
        configuration (str): Build type/configuration that should be built.
            This is only used on Windows.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'CMake build system.')
    _schema_properties = {'sourcedir': {'type': 'string'},
                          'builddir': {'type': 'string'},
                          'target': {'type': 'string'},
                          'target_language': {'type': 'string'},
                          'configuration': {'type': 'string',
                                            'default': 'Release'}}
    language = 'cmake'
    base_languages = ['c', 'c++']
    add_libraries = CMakeConfigure.add_libraries

    def parse_arguments(self, args):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.

        """
        if self.sourcedir is None:
            self.sourcedir = os.path.dirname(args[0])
        if not os.path.isabs(self.sourcedir):
            self.sourcedir = os.path.realpath(os.path.join(self.working_dir,
                                                           self.sourcedir))
        if self.builddir is None:
            if self.target is None:
                build_base = 'build'
            else:
                build_base = 'build_%s' % self.target
            self.builddir = os.path.join(self.sourcedir, build_base)
        if not os.path.isabs(self.builddir):
            self.builddir = os.path.realpath(os.path.join(self.working_dir,
                                                          self.builddir))
        self.source_files = [self.sourcedir]
        kwargs = dict(default_model_dir=self.builddir)
        super(CMakeModelDriver, self).parse_arguments(args, **kwargs)
        self.cmakelists = os.path.join(self.sourcedir, 'CMakeLists.txt')
        self.cmakelists_copy = os.path.join(self.sourcedir, 'CMakeLists_orig.txt')
        self.modified_files.append((self.cmakelists_copy, self.cmakelists))
        # Determine the underlying language
        if self.target_language is None:
            try_list = list(glob.glob(os.path.join(self.sourcedir, '*')))
            early_exit = False
            if self.model_src is not None:
                try_list = [self.model_src, try_list]
                early_exit = True
            languages = copy.deepcopy(self.get_tool_instance('compiler').languages)
            languages.remove('cmake')
            self.target_language = self.get_language_for_source(
                try_list, early_exit=early_exit, languages=languages)
            # Try to compile C as C++
            if self.target_language == 'c':
                self.target_language = 'c++'
        self.target_language_driver = components.import_component(
            'model', self.target_language)
        
    @classmethod
    def is_source_file(cls, fname):
        r"""Determine if the provided file name points to a source files for
        the associated programming language by checking the extension.

        Args:
            fname (str): Path to file.

        Returns:
            bool: True if the provided file is a source file, False otherwise.

        """
        return (CModelDriver.CModelDriver.is_source_file(fname)
                or CPPModelDriver.CPPModelDriver.is_source_file(fname))
        
    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            list: Full paths to any created wrappers.

        """
        out = super(CMakeModelDriver, self).write_wrappers(**kwargs)
        # Create cmake files that can be included
        if self.target is None:
            include_base = 'ygg_cmake.txt'
        else:
            include_base = 'ygg_cmake_%s.txt' % self.target
        include_file = os.path.join(self.sourcedir, include_base)
        self.get_tool_instance('compiler').create_include(
            include_file, self.target,
            driver=self.target_language_driver,
            logging_level=self.logger.getEffectiveLevel(),
            configuration=self.configuration)
        assert(os.path.isfile(include_file))
        out.append(include_file)
        # Create copy of cmakelists and modify
        if os.path.isfile(self.cmakelists):
            if not os.path.isfile(self.cmakelists_copy):
                shutil.copy2(self.cmakelists, self.cmakelists_copy)
            with open(self.cmakelists, 'rb') as fd:
                contents = fd.read()
            with open(self.cmakelists, 'wb') as fd:
                # Add conda prefix as first line
                conda_prefix = self.get_tool_instance('compiler').get_conda_prefix()
                if conda_prefix:
                    newline = backwards.as_bytes('LINK_DIRECTORIES(%s)\n'
                                                 % os.path.join(conda_prefix, 'lib'))
                    if newline not in contents:
                        fd.write(newline)
                # Explicitly set Release/Debug directories to builddir on windows
                if platform._is_win:  # pragma: windows
                    for artifact in ['runtime', 'library', 'archive']:
                        for conf in ['release', 'debug']:
                            newline = backwards.as_bytes(
                                'SET( CMAKE_%s_OUTPUT_DIRECTORY_%s '
                                % (artifact.upper(), conf.upper())
                                + '"${OUTPUT_DIRECTORY}")\n')
                            if newline not in contents:
                                fd.write(newline)
                fd.write(contents)
                # Add include if not already in the file
                newline = backwards.as_bytes('\nINCLUDE(%s)\n'
                                             % os.path.basename(include_file))
                if newline not in contents:
                    fd.write(newline)
        return out

    def compile_model(self, target=None, **kwargs):
        r"""Compile model executable(s) and appends any products produced by
        the compilation that should be removed after the run is complete.

        Args:
            target (str, optional): Target to build.
            **kwargs: Keyword arguments are passed on to the call_compiler
                method.

        """
        if target is None:
            target = self.target
        if target == 'clean':
            return self.call_linker(self.builddir, target=target, out=target,
                                    overwrite=True, working_dir=self.working_dir,
                                    allow_error=True, **kwargs)
        else:
            default_kwargs = dict(target=target,
                                  sourcedir=self.sourcedir,
                                  builddir=self.builddir,
                                  skip_interface_flags=True)
            default_kwargs['configuration'] = self.configuration
            for k, v in default_kwargs.items():
                kwargs.setdefault(k, v)
            return super(CMakeModelDriver, self).compile_model(**kwargs)

    def set_env(self, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CMakeModelDriver, self).set_env(**kwargs)
        out = CModelDriver.CModelDriver.update_ld_library_path(out)
        return out
    
    def cleanup(self):
        r"""Remove compiled executable."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model('clean')
        super(CMakeModelDriver, self).cleanup()
