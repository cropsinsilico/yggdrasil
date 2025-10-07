import os
import re
import shutil
import logging
import sysconfig
from collections import OrderedDict
from yggdrasil import platform, constants, tools
from yggdrasil.drivers.CompiledModelDriver import (
    ConfigurerBase, BuilderBase)
from yggdrasil.drivers.BuildModelDriver import BuildModelDriver
from yggdrasil.drivers import CModelDriver


logger = logging.getLogger(__name__)
_invalid_buildfile_comment = '# YGGDRASIL CMAKELISTS'


class CMakeConfigure(ConfigurerBase):
    r"""CMake configuration tool."""
    toolname = 'cmake'
    languages = ['cmake']
    default_flags = []
    flag_options = OrderedDict([
        ('definitions', '-D%s'),
        ('target_c_compiler_path', '-DCMAKE_C_COMPILER:FILEPATH=%s'),
        ('target_c++_compiler_path', '-DCMAKE_CXX_COMPILER:FILEPATH=%s'),
        ('target_fortran_compiler_path',
         '-DCMAKE_Fortran_COMPILER:FILEPATH=%s'),
        ('target_linker_path', '-DCMAKE_LINKER:FILEPATH=%s'),
        ('ignore_default_c_flags',
         ['-DCMAKE_C_FLAGS=',
          '-DCMAKE_C_FLAGS_DEBUG=',
          '-DCMAKE_C_FLAGS_RELEASE=']),
        ('ignore_default_c++_flags',
         ['-DCMAKE_CXX_FLAGS=',
          '-DCMAKE_CXX_FLAGS_DEBUG=',
          '-DCMAKE_CXX_FLAGS_RELEASE=']),
        ('ignore_default_fortran_flags',
         ['-DCMAKE_Fortran_FLAGS=',
          '-DCMAKE_Fortran_FLAGS_DEBUG=',
          '-DCMAKE_Fortran_FLAGS_RELEASE=']),
        ('osx_sysroot', '-DCMAKE_OSX_SYSROOT=%s'),
        ('osx_deployment_target', '-DCMAKE_OSX_DEPLOYMENT_TARGET=%s'),
        ('osx_arch', '-DCMAKE_OSX_ARCHITECTURES=%s'),
        ('sourcedir', '-S'),
        ('builddir', '-B'),
        ('configuration', '-DCMAKE_BUILD_TYPE=%s'),
        ('generator', '-G%s'),
        ('toolset', '-T%s'),
        ('platform', '-A%s'),
        ('verbose', '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON'),
    ])
    default_configfile = 'CMakeCache.txt'
    output_key = None
    no_additional_stages_flag = None
    default_builddir = '.'
    add_libraries = False
    product_files = ['Makefile', 'CMakeCache.txt',
                     'cmake_install.cmake', 'CMakeFiles']
    remove_product_exts = ['CMakeFiles']
    version_regex = r'(?P<version>cmake version \d+\.\d+(?:\.\d+)?)'

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        BuilderBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            cls.product_files += [
                'ALL_BUILD.vcxproj', 'ALL_BUILD.vcxproj.filters',
                'Debug', 'Release', 'Win32', 'Win64', 'x64',
                'ZERO_CHECK.vcxproj', 'ZERO_CHECK.vcxproj.filters',
            ]
            cls.remove_product_exts += [
                'Debug', 'Release', 'Win32', 'Win64', 'x64', '.dir',
            ]

    # The method generator and generator2toolset will only be called
    # if the VC 15 build tools are installed by MSVC 19+ which is not
    # currently supported by Appveyor CI.
    @classmethod
    def generator(cls, return_default=False, default=None, **kwargs):  # pragma: no cover
        r"""Determine the generator that should be used.

        Args:
            return_default (bool, optional): If True, the default generator will
                be returned even if the environment variable is set. Defaults to
                False.
            default (str, optional): Value that should be returned if a generator
                cannot be located. Defaults to None.
            **kwargs: Keyword arguments are passed to cls.call.

        Returns:
            str: Name of the generator.

        """
        out = default
        if not return_default:
            out = os.environ.get('CMAKE_GENERATOR', default)
        if not out:
            lines = cls.call(['--help'], skip_flags=True,
                             allow_error=True, **kwargs)[0]
            if 'Generators' not in lines:  # pragma: debug
                raise RuntimeError(f"Generator call failed:\n{lines}")
            gen_list = (lines.split('Generators')[-1]).splitlines()
            for x in gen_list:
                if x.startswith('*'):
                    out = (x.split('=')[0]).strip()
                    out = (out.strip('*')).strip()
                    break
        return out

    @classmethod
    def generator2toolset(cls, generator):  # pragma: no cover
        r"""Determine the toolset string option that corresponds to the provided
        generator name.

        Args:
            generator (str): Name of the generator.

        Returns:
            str: Name of the toolset.

        Raises:
            NotImplementedError: If the platform is not windows.
            ValueError: If the generator is not a flavor of Visual Studio.
            ValueError: If a tool set cannot be located for the specified generator.

        """
        if not platform._is_win:  # pragma: debug
            raise NotImplementedError("generator2toolset only available on Windows")
        if not generator.startswith("Visual Studio"):  # pragma: debug
            raise ValueError("Toolsets only available for Visual Studio generators.")
        if generator.endswith(('Win64', 'ARM', 'IA64')):
            generator = (generator.rsplit(' ', 1)[0]).strip()
        vs_generator_map = {'Visual Studio 16 2019': 'v142',
                            'Visual Studio 15 2017': 'v141',
                            'Visual Studio 14 2015': 'v140',
                            'Visual Studio 12 2013': 'v120',
                            'Visual Studio 11 2012': 'v110',
                            'Visual Studio 10 2010': 'v100',
                            'Visual Studio 9 2008': 'v90'}
        out = vs_generator_map.get(generator, None)
        if out is None:  # pragma: debug
            raise ValueError(
                f"Failed to locate toolset for generator: {generator}")
        return out
        
    @classmethod
    def append_product(cls, products, new, **kwargs):
        r"""Append a product to the specified list along with additional values
        indicated by cls.product_exts.

        Args:
            products (tools.ManagedFileSet): List of of existing products
                that new product should be appended to.
            new (str): New product that should be appended to the list.
            **kwargs: Additional keyword arguments are passed to
                ManagedFileSet.append_compilation_product

        """
        kwargs.setdefault('exclude_sources', True)
        return super(CMakeConfigure, cls).append_product(
            products, new, **kwargs)
        
    @classmethod
    def call(cls, args, **kwargs):
        r"""Call the tool with the provided arguments. If the first argument
        resembles the name of the tool executable, the executable will not be
        added.

        Args:
            args (list): The arguments that should be passed to the tool.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and the associated linker/archiver's call method
                if dont_link is False.

        Returns:
            str: Output to stdout from the command execution if skip_flags is
                True, produced file otherwise.

        """
        try:
            out = super(CMakeConfigure, cls).call(args, **kwargs)
        except RuntimeError as e:
            if platform._is_win:  # pragma: windows
                error_MSB4019 = (r'error MSB4019: The imported project '
                                 r'"C:\Microsoft.Cpp.Default.props" was not found.')
                error_NOVS = r'could not find any instance of Visual Studio.'
                # This will only be called if the VC 15 build tools
                # are installed by MSVC 19+ which is not currently
                # supported by Appveyor CI.
                if (error_MSB4019 in str(e)) or (error_NOVS in str(e)):  # pragma: debug
                    old_generator = os.environ.get('CMAKE_GENERATOR', None)
                    new_generator = cls.generator(return_default=True)
                    if old_generator and (old_generator != new_generator):
                        kwargs['generator'] = new_generator
                        kwargs['toolset'] = cls.generator2toolset(old_generator)
                        return super(CMakeConfigure, cls).call(args, **kwargs)
            raise
        return out

    @classmethod
    def get_flags(cls, sourcedir='.', builddir=None,
                  config=None, **kwargs):
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
        kwargs.setdefault('definitions', [])
        kwargs['definitions'].append('CMAKE_VERBOSE_MAKEFILE:BOOL=ON')
        # Add env prefix
        for iprefix in cls.get_env_prefixes():
            kwargs.setdefault('definitions', [])
            kwargs['definitions'].append(
                f"CMAKE_PREFIX_PATH={os.path.join(iprefix, 'lib')}")
            kwargs['definitions'].append(
                f"CMAKE_LIBRARY_PATH={os.path.join(iprefix, 'lib')}")
        out = super(CMakeConfigure, cls).get_flags(
            sourcedir=sourcedir, builddir=builddir, **kwargs)
        if platform._is_win and ('platform' not in kwargs):  # pragma: windows
            generator = kwargs.get('generator', None)
            if generator is None:
                generator = cls.generator()
            if (((generator is not None)
                 and generator.startswith('Visual')
                 and (not generator.endswith(('Win64', 'ARM')))
                 and platform._is_64bit)):
                out.append('-DCMAKE_GENERATOR_PLATFORM=x64')
        # elif platform._is_mac and ('osx_arch' not in kwargs):
        #     kwargs['osx_arch'] = platform._machine
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
        new_args = []
        if (args == cls.version_flags) or ('--help' in args):
            new_args = args
        if args and not kwargs.get('skip_flags', False):
            args_dir = cls.fix_path(os.path.dirname(args[0]),
                                    context='flag')
            sourcedir = kwargs.get('sourcedir', args_dir)
            if sourcedir != args_dir:  # pragma: debug
                raise RuntimeError(
                    f"The argument list contents (='{args_dir}') "
                    f"and 'sourcedir' (='{sourcedir}') keyword "
                    f"specify the same thing, but those provided do "
                    f"not match.")
            kwargs['sourcedir'] = args_dir
        return super(CMakeConfigure, cls).get_executable_command(
            new_args, **kwargs)
    
    @classmethod
    def fix_flags(cls, flags, **kwargs):
        r"""Update a string containing flags so that it can be used in
        the given context.

        Args:
            flags (str): String containing flags.
            **kwargs: Additional keyword arguments are passed to the
                 parent class.

        """
        # if ((isinstance(flags, str)  # and ' ' in flags
        #      and kwargs.get('context', None) == 'flag')):
        #     if '"' in flags:
        #         flags = flags.replace('"', '\\"')
        #     flags = f'"{flags}"'
        out = super(CMakeConfigure, cls).fix_flags(flags, **kwargs)
        if isinstance(flags, str) and ' ' in flags:
            logger.info(f"CMakeConfigure FIX_FLAGS: "
                        f"{type(flags)}, {flags}, {out}")
        # if ((isinstance(flags, str) and ' ' in flags
        #      and kwargs.get('context', None) == 'cmd')):
        #     out = cls.fix_path(out, actions=['doublequote'])
        #     logger.info(f"CMakeConfigure FIX_FLAGS OUT: {out}")
        return out
        
    @classmethod
    def fix_path(cls, path, **kwargs):
        r"""Update a path so it can be used in the given context. This
        function handles the presence of backslashes or spaces in the
        path.

        Args:
            path (str): Path that should be formatted.
            **kwargs: Additional keyword arguments are passed to the
                 parent class.

        Returns:
            str: Updated path.

        """
        kwargs.setdefault('for_gnu', True)  # cmake uses forward slashes
        if kwargs.get('context', None) == 'cmakelist':
            # Force lists to be quoted
            kwargs.setdefault(
                'actions', ['doublequote', 'forwardslash', 'escapespace'])
        elif kwargs.get('context', None) == 'flag':
            default_actions = ['forwardslash']
            if ' ' in path:
                default_actions += ['doublequote']
            kwargs.setdefault('actions', default_actions)
        # elif kwargs.get('context', None) == 'cmd':
        #     if ' ' in path:
        #         kwargs.setdefault('actions', ['doublequote'])
        return super(CMakeConfigure, cls).fix_path(path, **kwargs)


class CMakeBuilder(BuilderBase):
    r"""CMake build tool."""
    toolname = 'cmake'
    languages = CMakeConfigure.languages
    basetooltype = CMakeConfigure.tooltype
    basetool = CMakeConfigure.toolname
    version_regex = CMakeConfigure.version_regex
    default_flags = []
    output_key = None
    flag_options = OrderedDict([('builddir', {'key': '--build',
                                              'position': 0}),
                                ('target', '--target'),
                                ('configuration', '--config')])
    tool_suffix_format = ''
    local_kws = BuilderBase.local_kws + ['target']
    input_filetypes = ['configfile']

    @classmethod
    def call(cls, *args, **kwargs):
        r"""Print contents of CMakeCache.txt before raising error."""
        try:
            return super(CMakeBuilder, cls).call(*args, **kwargs)
        except BaseException:  # pragma: debug
            cache = 'CMakeCache.txt'
            if ((isinstance(kwargs.get('builddir', None), str)
                 and os.path.isdir(kwargs['builddir']))):
                cache = os.path.join(kwargs['builddir'], cache)
            if kwargs.get('working_dir', None):
                cache = os.path.join(kwargs['working_dir'], cache)
            if os.path.isfile(cache):
                with open(cache, 'r') as fd:
                    logger.debug(f'CMakeCache.txt:\n{fd.read()}')
            else:
                logger.error(f'Cache file does not exist: {cache}')
            raise

    @classmethod
    def get_executable_command(cls, args, **kwargs):
        r"""Determine the command required to run the tool using the
        specified arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool.
                If skip_flags is False, these are treated as input files
                that will be used by the tool.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            str: Output to stdout from the command execution.

        """
        new_args = []
        if (args == cls.version_flags) or ('--help' in args):
            new_args = args
        if not kwargs.get('skip_flags', False):
            if os.path.isdir(args[0]):
                args_builddir = args[0]
            else:
                args_builddir = os.path.dirname(args[0])
            builddir = kwargs.get('builddir', args_builddir)
            if (((not os.path.isabs(builddir))
                 and os.path.isabs(args_builddir))):
                builddir = os.path.join(
                    os.path.dirname(args_builddir), builddir)
            if builddir != args_builddir:  # pragma: debug
                raise RuntimeError(
                    f"The argument list contents (='{args_builddir}') "
                    f"and 'builddir' (='{builddir}') keyword should "
                    f"specify the same thing, but those  provided do "
                    f"not match.")
            kwargs['builddir'] = args_builddir
        return super(CMakeBuilder, cls).get_executable_command(
            new_args, **kwargs)


class CMakeModelDriver(BuildModelDriver):
    r"""Class for running cmake compiled drivers. Before running the
    cmake command, the cmake commands for setting the necessary compiler
    & linker flags for the interface's C/C++ library are written to a
    file called 'ygg_cmake.txt' that should be included in the
    CMakeLists.txt file (after the target executable has been added).

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (cmake
            target) and any arguments for the executable.
        configuration (str, optional): Build type/configuration that
            should be built. Defaults to 'Release'.
        yggdrasil_option (str, optional): Build option that can be set
            to build against the yggdrasil library. If provided, the
            cmake file will not be modified.
        **kwargs: Additional keyword arguments are passed to parent
            class.

    Attributes:
        add_libraries (bool): If True, interface libraries and dependency
            libraries are added using CMake's ADD_LIBRARY directive. If
            False, interface libraries are found using FIND_LIBRARY.
        configuration (str): Build type/configuration that should be
            built. This is only used on Windows.
        yggdrasil_option (str): Build option that can be set to build
            against the yggdrasil library. If provided, the cmake file
            will not be modified.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are
            available.

    """

    _schema_subtype_description = ('Model is written in C/C++ and has a '
                                   'CMake build system.')
    _schema_properties = {
        'configuration': {
            'type': 'string',
            'default': 'Release'
        },
        'yggdrasil_option': {'type': 'string'},
    }
    language = 'cmake'
    add_libraries = CMakeConfigure.add_libraries
    target_flags_in_env = False
    buildfile_base = 'CMakeLists.txt'
    basetool = 'configurer'

    def parse_arguments(self, args, **kwargs):
        r"""Sort arguments based on their syntax to determine if an
        argument is a source file, compilation flag, or runtime
        option/flag that should be passed to the model executable.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        """
        if self.yggdrasil_option:
            if not self.definitions:
                self.definitions = []
            self.definitions.append(self.yggdrasil_option)
        if self.target is None:
            self.builddir_base = 'yggbuild'
        else:
            self.builddir_base = f'yggbuild_{self.target}'
        super(CMakeModelDriver, self).parse_arguments(args, **kwargs)

    @classmethod
    def is_valid_buildfile(cls, fname):
        r"""Determine if a file is a valid build file.

        Args:
            fname (str): File to check.

        Returns:
            bool: True if fname is valid, False otherwise.

        """
        if not super(CMakeModelDriver, cls).is_valid_buildfile(fname):
            return False
        with open(fname, 'r') as fd:
            contents = fd.read()
        return (not contents.startswith(_invalid_buildfile_comment))
        
    @classmethod
    def get_language_for_buildfile(cls, buildfile, target=None):
        r"""Determine the target language based on the contents of a
        build file.

        Args:
            buildfile (str): Full path to the build configuration file.
            target (str, optional): Target that will be built. Defaults
                to None and the default target in the build file will be
                used.

        """
        with open(buildfile, 'r') as fd:
            lines = fd.readlines()
        for x in lines:
            if not x.strip().upper().startswith('ADD_EXECUTABLE'):
                continue
            varlist = x.split('(', 1)[-1].rsplit(')', 1)[0].split()
            if (target is None) or (target == varlist[0]):
                try:
                    return cls.get_language_for_source(
                        varlist[1:], early_exit=True, call_base=True)
                except ValueError:  # pragma: debug
                    pass
        return super(CMakeModelDriver, cls).get_language_for_buildfile(
            buildfile)  # pragma: debug

    @classmethod
    def create_imports(cls, dep, imp, **kwargs):
        r"""Modify the build file to import the provided library.

        Args:
            dep (CompilationDependency): Dependency to add imports to in
                its build file.
            imp (object): Information about the library that should be
                imported as output by create_exports.
            **kwargs: Additional keyword arguments are passed to the
                appropriate create_imports_* method.

        """
        target = dep.get('target', None)
        if target is None:
            return cls.create_imports_replace(dep, imp, **kwargs)
        return cls.create_imports_replace(dep, imp, **kwargs)
        # return cls.create_imports_preserve(dep, imp, **kwargs)
        
    @classmethod
    def create_imports_replace(cls, dep, imp, products=None,
                               overwrite=False, verbose=False, **kwargs):
        r"""Modify the build file to import the provided library.

        Args:
            dep (CompilationDependency): Dependency to add imports to in
                its build file.
            imp (object): Information about the library that should be
                imported as output by create_exports.
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products should be appended to.
            overwrite (bool, optional): If True, any existing exports
                file with the same name will be overwritten.
            verbose (bool, optional): If True, info level log messages
                will be created when the file is generated/destroyed.
            **kwargs: Additional keyword arguments are ignored.

        """
        # TODO: temp
        if platform._is_win:
            verbose = True
        logger.info(f"CREATE_IMPORTS_REPLACE {dep} {imp}")
        buildfile = dep['buildfile']
        if not os.path.isabs(buildfile):
            buildfile = dep._relative_to_directory(
                buildfile, directory=dep.get('working_dir', None))
        logger.debug(f"CREATE_IMPORTS {dep}: {buildfile}\n"
                     f"source_dir: {dep.get('source_dir', None)}")
        target = dep.get('target', '${PROJECT_NAME}')
        if products is None:
            products = tools.IntegrationPathSet(overwrite=overwrite)
        products.append_generated(buildfile, [], replaces=True,
                                  tag='build_time', verbose=verbose)
        regex_link_scope = (
            r'target_link_libraries\(\s*' + target
            + r'(?P<scope>\s+(?:PRIVATE)|(?:PUBLIC))?'
            + r'(?:\s+[^\) \t]+)+\s*\)'
        )
        regex_link_scope_match = None
        build_product = products.last
        orig_buildfile = build_product.name
        if os.path.isfile(build_product.replaces):
            orig_buildfile = build_product.replaces
        link_scope = ''
        if os.path.isfile(orig_buildfile):
            with open(orig_buildfile, 'r') as fd:
                contents = fd.read()
                regex_link_scope_match = re.search(
                    regex_link_scope, contents)
            if contents.startswith(_invalid_buildfile_comment):
                return
            if ((regex_link_scope_match
                 and regex_link_scope_match.group('scope'))):
                link_scope = 'PRIVATE '
            prefix_lines = [
                # Prevent error when cross compiling by building static
                #   lib as test
                'set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")',
            ]
            suffix_lines = [
                f'include({imp[1]})',
                f'target_link_libraries({target} {link_scope}{imp[0]})',
            ]
            build_product.lines = (
                prefix_lines + contents.splitlines() + suffix_lines)

    @classmethod
    def create_imports_preserve(cls, dep, imp, products=None,
                                overwrite=False, verbose=False, **kwargs):
        r"""Modify the build file to import the provided library.

        Args:
            dep (CompilationDependency): Dependency to add imports to in
                its build file.
            imp (object): Information about the library that should be
                imported as output by create_exports.
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products should be appended to.
            overwrite (bool, optional): If True, any existing exports
                file with the same name will be overwritten.
            verbose (bool, optional): If True, info level log messages
                will be created when the file is generated/destroyed.
            **kwargs: Additional keyword arguments are ignored.

        """
        # TODO: temp
        verbose = True
        # if platform._is_win:
        #     verbose = True
        logger.debug(f"CREATE_IMPORTS_PRESERVE {dep} {imp}")
        target = dep['target']
        buildfile = dep.get('buildfile_wrapped', None)
        if buildfile is None:
            buildfile = dep['buildfile']
            sourcedir = dep.get('source_dir', os.path.dirname(buildfile))
            if not sourcedir:
                sourcedir = dep.get('working_dir', os.getcwd())
            dep.set('source_dir_wrapped', sourcedir)
            dep.set('buildfile_wrapped', buildfile)
            dep.set('source_dir', os.path.join(sourcedir, 'yggsource'))
            dep.set('buildfile', os.path.join(
                dep['source_dir'], cls.buildfile_base))
        sourcedir = dep['source_dir']
        wrapper = dep['buildfile']
        if not os.path.isabs(buildfile):
            buildfile = dep._relative_to_directory(
                buildfile, directory=dep.get('working_dir', None))
        # buildfile_wrap = os.path.join(dep.builddir)
        logger.info(f"CREATE_IMPORTS {dep}: {buildfile}\n"
                    f"wrapper: {wrapper}\n"
                    f"source_dir: {dep.get('source_dir', None)}")
        result = CMakeConfigure.fix_path(dep.result, context='cmakevar')
        if products is None:
            products = tools.IntegrationPathSet(overwrite=overwrite)
        products.append_generated(wrapper, [],
                                  tag='build_time', verbose=verbose,
                                  create_parent_dir=True)
        build_product = products.last
        build_product.lines = [
            'cmake_minimum_required(VERSION 3.25)',
            # Prevent error when cross compiling by building static
            #   lib as test
            'set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")',
            f'set(TARGET_NAME {target})'
            f'include({imp[1]})',
            f'link_libraries({imp[0]})',
            f'add_subdirectory({os.path.dirname(dep.buildfile)} wrapped)',
            f'set(TARGET_FILENAME {result})',
            'add_custom_command(',
            '      OUTPUT ${TARGET_FILENAME}',
            '      COMMAND ${CMAKE_COMMAND} -E copy',
            '      $<TARGET_FILE:${TARGET_NAME}> ${TARGET_FILENAME}',
            '      DEPENDS ${TARGET_NAME}',
            '    )',
            'add_custom_target(',
            '      copy_files ALL',
            '      DEPENDS ${TARGET_FILENAME}',
            '    )',
        ]

    @classmethod
    def create_exports(cls, dep, products=None, overwrite=False,
                       dry_run=False, verbose=False, **kwargs):
        r"""Create an exports file for the provided dependency.

        Args:
            dep (CompilationDependency): Dependency to create exports
                file for.
                Defaults to False.
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products should be appended to.
            overwrite (bool, optional): If True, any existing exports
                file with the same name will be overwritten.
            dry_run (bool, optional): If True, the file won't be created,
                but the products will be updated. Defautls to False.
            verbose (bool, optional): If True, info level log messages
                will be created when the file is generated/destroyed.
            **kwargs: Additional keyword arguments are passed to
                dep.tool_kwargs.

        """
        # TODO: temp
        if platform._is_win:
            verbose = True
        logger.debug(f"CREATE_EXPORTS {dep}")
        suffix = dep.suffix + dep.suffix_tools(dep['libtype'])
        target = f"{dep.name}::{dep.name}{suffix}"
        fname = dep._relative_to_directory(
            f'{dep.name}{suffix}Targets.cmake')
        dependencies = dep.dependency_order()
        dep_kws = {'dry_run': True}
        dependencies.getall('dep_kwargs', to_update=dep_kws)
        if dep.result in dep_kws.get('libraries', []):
            dep_kws['libraries'].remove(dep.result)
        lines = [
            f"add_library({target} {dep['libtype'].upper()} IMPORTED)"
        ]
        properties = OrderedDict([
            ('IMPORTED_LOCATION',
             CMakeConfigure.fix_path(dep.result, context='cmakevar')),
        ])
        kw2prop = OrderedDict([
            ('include_dirs', 'INTERFACE_INCLUDE_DIRECTORIES'),
            ('definitions', 'INTERFACE_COMPILE_DEFINITIONS'),
            ('libraries', 'INTERFACE_LINK_LIBRARIES'),
        ])
        for k, v in kw2prop.items():
            if dep_kws.get(k, None):
                properties[v] = CMakeConfigure.fix_path(
                    ';'.join(dep_kws[k]), context='cmakelist')
        if properties:
            lines += [f"set_target_properties({target} PROPERTIES"]
            lines += [f"  {k} {v}" for k, v in properties.items()]
            lines += [")"]
        if products is None:
            products = tools.IntegrationPathSet(overwrite=overwrite)
        if dry_run:
            products.append(fname)
        else:
            products.append_generated(fname, lines, verbose=verbose)
        products.last.setup()
        return (target, CMakeConfigure.fix_path(fname, context='cmakevar'))

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
        if platform._is_mac:
            kwargs.setdefault('target_linker_flags', [])
            kwargs['target_linker_flags'] += ['-L/usr/lib',
                                              '-L/usr/local/lib']
        if CModelDriver._osx_sysroot is not None:
            kwargs.setdefault('osx_sysroot', CModelDriver._osx_sysroot)
            if os.environ.get('MACOSX_DEPLOYMENT_TARGET', None):
                kwargs.setdefault('osx_deployment_target',
                                  os.environ['MACOSX_DEPLOYMENT_TARGET'])
        for k in constants.LANGUAGES['compiled']:
            kwargs.setdefault(f'ignore_default_{k}_flags', True)
        out = super(CMakeModelDriver, cls).create_dep(
            without_wrapper=without_wrapper, **kwargs)
        if out['target_dep'].tool('compiler').env_matches_tool(
                use_sysconfig=True):
            python_flags = sysconfig.get_config_var('LIBS')
            if python_flags:
                flags = out['target_dep'].parameters.get(
                    'linker_flags', [])
                flags += [
                    x for x in python_flags.split()
                    if x.startswith(('-L', '-l')) and x not in flags]
                out['target_dep'].parameters['linker_flags'] = flags
        if platform._is_win and out['target_dep'].tool('compiler').is_gnu:
            gcc = out['target_dep'].tool('compiler').get_executable(
                full_path=True)
            env = out.get('builder_env', for_build=True)
            if env.get('PATH', ''):
                path = cls.prune_sh_gcc(env.get('PATH', ''), gcc)
                env['PATH'] = path
                out.set('builder_env', env)
            if not shutil.which('sh', path=path):  # pragma: appveyor
                # This will not be run on Github actions where
                # the shell is always set
                out.parameters.setdefault('generator', 'MinGW Makefiles')
                out.set('generator', 'MinGW Makefiles')
            elif shutil.which('make', path=path):
                out.parameters.setdefault('generator', 'Unix Makefiles')
                out.set('generator', 'Unix Makefiles')
            # This is not currently tested
            # else:
            #     out.parameters.setdefault('generator', 'MSYS Makefiles')
            #     out.set('generator', 'MSYS Makefiles')
        return out
        
    @classmethod
    def prune_sh_gcc(cls, path, gcc):  # pragma: appveyor
        r"""Remove instances of sh.exe from the path that are not
        associated with the selected gcc compiler. This can happen
        on windows when rtools or git install a version of sh.exe
        that is added to the path before the compiler.

        Args:
            path (str): Contents of the path variable.
            gcc (str): Full path to the gcc executable.

        Returns:
            str: Modified path that removes the extra instances
                of sh.exe.

        """
        # This method is not covered because it is not called on
        # github actions where bash is always present
        sh_path = shutil.which('sh', path=path)
        while sh_path:
            for k in ['rtools', 'git']:
                if k in sh_path.lower():
                    break
            else:  # pragma: debug
                break
            if k not in gcc.lower():
                paths = path.split(os.pathsep)
                paths.remove(os.path.dirname(sh_path))
                path = os.pathsep.join(paths)
                sh_path = shutil.which('sh', path=path)
            else:  # pragma: debug
                break
        return path
