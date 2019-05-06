import os
import re
import shutil
from collections import OrderedDict
from yggdrasil import platform
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, LinkerBase)
from yggdrasil.drivers import CModelDriver


class CMakeConfigure(CompilerBase):
    r"""CMake configuration tool."""
    name = 'cmake'
    languages = ['cmake']
    is_linker = False
    default_flags = []  # '-H']
    flag_options = OrderedDict([('definitions', '-D%s'),
                                ('sourcedir', ''),  # '-S'
                                ('builddir', '-B%s')])
    output_key = None
    compile_only_flag = None
    default_builddir = '.'
    default_archiver = False

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
        if sourcedir is None:
            if os.path.isfile(src):
                sourcedir = os.path.dirname(src)
            else:
                sourcedir = src
        if builddir is None:
            builddir = os.path.join(sourcedir, cls.default_builddir)
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
                    builddir = os.path.join(sourcedir, cls.default_builddir)
                else:
                    builddir = outfile
        # Pop target (used for build stage file name, but not for any other
        # part of the build stage)
        kwargs.pop('target', None)
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
            if sourcedir != args[0]:
                raise RuntimeError(("The argument list "
                                    "contents (='%s') and 'sourcedir' (='%s') "
                                    "keyword specify the same thing, but those "
                                    "provided do not match.")
                                   % (args[0], sourcedir))
            kwargs['sourcedir'] = args[0]
        return super(CMakeConfigure, cls).get_executable_command([], **kwargs)
    
    
class CMakeBuilder(LinkerBase):
    r"""CMake build tool."""
    name = 'cmake'
    languages = ['cmake']
    default_flags = ['--clean-first']
    output_key = None
    flag_options = OrderedDict([('builddir', {'key': '--build',
                                              'position': 0}),
                                ('target', '--target')])

    @classmethod
    def extract_kwargs(cls, kwargs):
        r"""Extract linker kwargs, leaving behind just compiler kwargs.

        Args:
            kwargs (dict): Keyword arguments passed to the compiler that should
                be sorted into kwargs used by either the compiler or linker or
                both. Keywords that are not used by the compiler will be removed
                from this dictionary.

        Returns:
            dict: Keyword arguments that should be passed to the linker.

        """
        kws_link = []
        kws_both = ['builddir', 'target']
        kwargs_link = super(CMakeBuilder, cls).extract_kwargs(kwargs)
        # Move kwargs unique to linker
        for k in kws_link:
            if k in kwargs:
                kwargs_link[k] = kwargs.pop(k)
        # Copy kwargs that should be passed to both compiler & linker
        for k in kws_both:
            if k in kwargs:
                kwargs_link[k] = kwargs[k]
        return kwargs_link
        
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
            if os.path.isdir(obj):
                builddir = obj
            else:
                builddir = os.path.dirname(obj)
        if target is None:
            if os.path.isdir(obj):
                raise RuntimeError("Target is required.")
            else:
                target = os.path.splitext(os.path.basename(obj))[0]
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
            builddir = cls.default_builddir
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
            if builddir != args[0]:
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
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        sourcedir (str): Source directory to call cmake on.
        builddir (str): Directory where the build should be saved.
        target (str): Name of executable that should be created and called.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'CMake build system.')
    _schema_properties = {'sourcedir': {'type': 'string'},
                          'builddir': {'type': 'string'},
                          'target': {'type': 'string'}}
    language = 'cmake'
    base_languages = ['c']
    cmake_products = ['Makefile', 'CMakeCache.txt', 'cmake_install.cmake',
                      'CMakeFiles']

    def parse_arguments(self, args):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.

        """
        if self.sourcedir is None:
            self.sourcedir = self.working_dir
        elif not os.path.isabs(self.sourcedir):
            self.sourcedir = os.path.realpath(os.path.join(self.working_dir,
                                                           self.sourcedir))
        if self.builddir is None:
            # self.builddir = self.sourcedir
            self.builddir = os.path.join(self.sourcedir, 'build')
        elif not os.path.isabs(self.builddir):
            self.builddir = os.path.realpath(os.path.join(self.working_dir,
                                                          self.builddir))
        self.source_files = [self.sourcedir]
        kwargs = dict(default_model_dir=self.builddir)
        super(CMakeModelDriver, self).parse_arguments(args, **kwargs)
        for x in self.cmake_products:
            self.products.append(os.path.join(self.builddir, x))
        
    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            list: Full paths to any created wrappers.

        """
        out = super(CMakeModelDriver, self).write_wrappers(**kwargs)
        # Create cmake files that can be included
        include_file = os.path.join(self.sourcedir, 'ygg_cmake.txt')
        self.create_include(include_file, self.target,
                            logging_level=self.logger.getEffectiveLevel())
        assert(os.path.isfile(include_file))
        out.append(include_file)
        return out

    @classmethod
    def create_include(cls, fname, target, compile_flags=None, linker_flags=None,
                       logging_level=None):
        r"""Create CMakeList include file with necessary includes,
        definitions, and linker flags.

        Args:
            fname (str): File where the include file should be saved.
            target (str): Target that links should be added to.
            compile_flags (list, optional): Additional compile flags that
                should be set. Defaults to [].
            linker_flags (list, optional): Additional linker flags that
                should be set. Defaults to [].
            logging_level (int, optional): Logging level that should be passed
                as a definition to the C compiler. Defaults to None and will be
                ignored.

        Raises:
            ValueError: If a linker or compiler flag cannot be interpreted.

        """
        if target is None:
            target = '${PROJECT_NAME}'
        if compile_flags is None:
            compile_flags = []
        if linker_flags is None:
            linker_flags = []
        use_library_path = True  # platform._is_win
        compile_flags = CModelDriver.CModelDriver.get_compiler_flags(
            flags=compile_flags, use_library_path=use_library_path, dont_link=True,
            for_model=True, skip_defaults=True, logging_level=logging_level)
        linker_flags = CModelDriver.CModelDriver.get_linker_flags(
            flags=linker_flags, use_library_path=use_library_path, for_model=True,
            skip_defaults=True, use_library_path_internal=True)
        lines = []
        var_count = 0
        for x in compile_flags:
            if x.startswith('-D'):
                lines.append('ADD_DEFINITIONS(%s)' % x)
            elif x.startswith('-I'):
                xdir = x.split('-I', 1)[-1]
                if platform._is_win:  # pragma: windows
                    xdir = xdir.replace('\\', re.escape('\\'))
                lines.append('INCLUDE_DIRECTORIES(%s)' % xdir)
            elif x.startswith('-') or x.startswith('/'):
                lines.append('ADD_DEFINITIONS(%s)' % x)
            else:
                raise ValueError("Could not parse compiler flag '%s'." % x)
        for x in linker_flags:
            if x.startswith('-l'):
                lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
            elif x.startswith('-L'):
                libdir = x.split('-L')[-1]
                if platform._is_win:  # pragma: windows
                    libdir = libdir.replace('\\', re.escape('\\'))
                lines.append('LINK_DIRECTORIES(%s)' % libdir)
            elif x.startswith('/LIBPATH:'):  # pragma: windows
                libdir = x.split('/LIBPATH:')[-1]
                if '"' in libdir:
                    libdir = libdir.split('"')[1]
                if platform._is_win:
                    libdir = libdir.replace('\\', re.escape('\\'))
                lines.append('LINK_DIRECTORIES(%s)' % libdir)
            elif os.path.isfile(x):
                xd, xf = os.path.split(x)
                xl, xe = os.path.splitext(xf)
                if xe.lower() in ['.so', '.dll', '.dylib']:
                    lines.append('ADD_LIBRARY(%s SHARED IMPORTED)' % xl)
                else:
                    lines.append('ADD_LIBRARY(%s STATIC IMPORTED)' % xl)
                lines.append('SET_TARGET_PROPERTIES(')
                lines.append('    %s PROPERTIES' % xl)
                # lines.append('    PROPERTIES LINKER_LANGUAGE CXX')
                if platform._is_win:  # pragma: windows
                    lines.append('    IMPORTED_LOCATION %s)' %
                                 x.replace('\\', re.escape('\\')))
                else:
                    lines.append('    IMPORTED_LOCATION %s)' % x)
                lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, xl))
                # lines.append('FIND_LIBRARY(VAR%d %s HINTS %s)' % (var_count, xf, xd))
                # lines.append('TARGET_LINK_LIBRARIES(%s ${VAR%s})' % (target, var_count))
                var_count += 1
            elif x.startswith('-') or x.startswith('/'):
                raise ValueError("Could not parse linker flag '%s'." % x)
            else:
                lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
        import pprint
        pprint.pprint(lines)
        if fname is None:
            return lines
        else:
            if os.path.isfile(fname):  # pragma: debug
                os.remove(fname)
            with open(fname, 'w') as fd:
                fd.write('\n'.join(lines))

    @classmethod
    def call_compiler(cls, src, dont_build=None, **kwargs):
        r"""Compile a source file into an executable or linkable object file,
        checking for errors.

        Args:
            src (str): Full path to the directory containing the source files.
            dont_build (bool, optional): If True, cmake configuration/generation
                will be run, but the project will not be built. Defaults to
                False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        # Remove files created by cmake in overwrite so that directory should
        # be empty (and therefore removable by the parent method).
        if kwargs.get('overwrite', False):
            builddir = kwargs.get('builddir', None)
            working_dir = kwargs.get('working_dir', None)
            rm_files = cls.cmake_products
            out = kwargs.get('out', None)
            if out is not None:
                rm_files.append(out)
            for x in rm_files:
                xfile = x
                if (not os.path.isabs(xfile)) and (builddir is not None):
                    xfile = os.path.join(builddir, xfile)
                if (not os.path.isabs(xfile)) and (working_dir is not None):
                    xfile = os.path.join(working_dir, xfile)
                if os.path.isfile(xfile):
                    os.remove(xfile)
                elif os.path.isdir(xfile) and xfile.endswith('CMakeFiles'):
                    shutil.rmtree(xfile)
        # Set keyword arguments based on cmake mappings/aliases
        if dont_build is not None:
            kwargs['dont_link'] = dont_build
        return super(CMakeModelDriver, cls).call_compiler(src, **kwargs)

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
                                    **kwargs)
        else:
            default_kwargs = dict(target=target,
                                  sourcedir=self.sourcedir,
                                  builddir=self.builddir,
                                  skip_interface_flags=True)
            for k, v in default_kwargs.items():
                kwargs.setdefault(k, v)
            return super(CMakeModelDriver, self).compile_model(**kwargs)

    def set_env(self):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CMakeModelDriver, self).set_env()
        out = CModelDriver.CModelDriver.update_ld_library_path(out)
        return out
    
    def remove_products(self):
        r"""Delete products produced during the compilation process."""
        if (self.model_file is not None) and os.path.isfile(self.model_file):
            self.compile_model('clean')
        super(CMakeModelDriver, self).remove_products()
        if os.path.isdir(self.builddir) and (not os.listdir(self.builddir)):
            os.rmdir(self.builddir)
