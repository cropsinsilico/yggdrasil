import os
import shutil
from cis_interface import tools, backwards
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.drivers import GCCModelDriver


def create_include(fname, target, compile_flags=[], linker_flags=[]):
    r"""Create CMakeList include file with necessary includes,
    definitions, and linker flags.

    Args:
        fname (str): File where the include file should be saved.
        target (str): Target that links should be added to.
        compile_flags (list, optional): Additional compile flags that
            should be set. Defaults to [].
        linker_flags (list, optional): Additional linker flags that
            should be set. Defaults to [].

    """
    _compile_flags, _linker_flags = GCCModelDriver.get_flags()
    compile_flags += _compile_flags
    linker_flags += _linker_flags
    lines = []
    for x in compile_flags:
        if x.startswith('-D'):
            lines.append('ADD_DEFINITIONS(%s)' % x)
        elif x.startswith('-I'):
            lines.append('INCLUDE_DIRECTORIES(%s)' % x.split('-I', 1)[-1])
        elif x.startswith('-') or x.startswith('/'):
            lines.append('ADD_DEFINITIONS(%s)' % x)
        else:
            raise ValueError("Could not parse compiler flag '%s'." % x)
    for x in linker_flags:
        if x.startswith('-l'):
            lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
        elif x.startswith('-L'):
            libdir = x.split('-L')[-1]
            lines.append('LINK_DIRECTORIES(%s)' % libdir)
        elif x.startswith('/LIBPATH:'):  # pragma: windows
            libdir = x.split('/LIBPATH:')[-1]
            if '"' in libdir:
                libdir = libdir.split('"')[1]
            lines.append('LINK_DIRECTORIES(%s)' % libdir)
        elif x.startswith('-') or x.startswith('/'):
            raise ValueError("Could not parse linker flag '%s'." % x)
        else:
            lines.append('TARGET_LINK_LIBRARIES(%s %s)' % (target, x))
    if fname is None:
        return lines
    else:
        with open(fname, 'w') as fd:
            fd.write('\n'.join(lines))


class CMakeModelDriver(ModelDriver):
    r"""Class for running cmake compiled drivers. Before running the
    cmake command, the cmake commands for setting the necessary compiler & linker
    flags for the interface's C/C++ library are written to a file called
    'cis_cmake.txt' that should be included in the CMakeLists.txt file (after
    the target executable has been added).

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (cmake target) and
            any arguments for the executable.
        sourcedir (str, optional): Source directory to call cmake on. If not
            provided it is set to self.workingDir. This should be the directory
            containing the CMakeLists.txt file. It can be relative to
            self.workingDir or absolute.
        builddir (str, optional): Directory where the build should be saved.
            Defaults to <sourcedir>/build. It can be relative to self.workingDir
            or absolute.
        cmakeargs (list, optional): Arguments that should be passed to cmake.
            Defaults to [].
        preserve_cache (bool, optional): If True the cmake cache will be kept
            following the run, otherwise all files created by cmake will be
            cleaned up. Defaults to False.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        compiled (bool): True if the compilation was successful, False otherwise.
        target (str): Name of executable that should be created and called.
        sourcedir (str): Source directory to call cmake on.
        builddir (str): Directory where the build should be saved.
        cmakeargs (list): Arguments that should be passed to cmake.
        preserve_cache (bool): If True the cmake cache will be kept following the
            run, otherwise all files created by cmake will be cleaned up.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """
    def __init__(self, name, args, sourcedir=None, builddir=None,
                 cmakeargs=None, preserve_cache=False, **kwargs):
        super(CMakeModelDriver, self).__init__(name, args, **kwargs)
        if not tools._c_library_avail:  # pragma: windows
            raise RuntimeError("No library available for models written in C/C++.")
        self.debug('')
        self.compiled = False
        self.target = self.args[0]
        if sourcedir is None:
            sourcedir = self.workingDir
        elif not os.path.isabs(sourcedir):
            sourcedir = os.path.join(self.workingDir, sourcedir)
        self.sourcedir = sourcedir
        if builddir is None:
            builddir = os.path.join(sourcedir, 'build')
        elif not os.path.isabs(builddir):
            builddir = os.path.join(self.workingDir, builddir)
        self.builddir = builddir
        if cmakeargs is None:
            cmakeargs = []
        elif isinstance(cmakeargs, backwards.string_types):
            cmakeargs = [cmakeargs]
        self.cmakeargs = cmakeargs
        self.preserve_cache = preserve_cache
        self.target_file = os.path.join(self.builddir, self.target)
        self.include_file = os.path.join(self.sourcedir, 'cis_cmake.txt')
        self.args[0] = self.target_file
        # Set environment variables
        self.debug("Setting environment variables.")
        create_include(self.include_file, self.target)
        # Compile in a new process
        self.debug("Making target.")
        self.run_cmake(self.target)

    def run_cmake(self, target=None):
        r"""Run the cmake command on the source.

        Args:
            target (str, optional): Target to build.

        Raises:
            RuntimeError: If there is an error in running cmake.
        
        """
        curdir = os.getcwd()
        os.chdir(self.sourcedir)
        if not os.path.isfile('CMakeLists.txt'):
            os.chdir(curdir)
            self.cleanup()
            raise IOError('No CMakeLists.txt file found in %s.' % self.sourcedir)
        # Configuration
        if target != 'clean':
            config_cmd = ['cmake'] + self.cmakeargs
            config_cmd += ['-H.', self.sourcedir, '-B%s' % self.builddir]
            self.debug(' '.join(config_cmd))
            comp_process = tools.popen_nobuffer(config_cmd)
            output, err = comp_process.communicate()
            exit_code = comp_process.returncode
            if exit_code != 0:
                os.chdir(curdir)
                self.cleanup()
                self.error(output)
                raise RuntimeError("CMake config failed with code %d." % exit_code)
            self.debug('Config output: \n%s' % output)
        # Build
        build_cmd = ['cmake', '--build', self.builddir, '--clean-first']
        if self.target is not None:
            build_cmd += ['--target', self.target]
        self.debug(' '.join(build_cmd))
        comp_process = tools.popen_nobuffer(build_cmd)
        output, err = comp_process.communicate()
        exit_code = comp_process.returncode
        if exit_code != 0:
            os.chdir(curdir)
            self.error(output)
            self.cleanup()
            raise RuntimeError("CMake build failed with code %d." % exit_code)
        self.debug('Build output: \n%s' % output)
        self.debug('Make complete')
        os.chdir(curdir)

    def cleanup(self):
        r"""Remove compile executable."""
        # self.run_cmake('clean')
        if not self.preserve_cache:
            rmfiles = [self.include_file,
                       self.target_file,
                       os.path.join(self.builddir, 'Makefile'),
                       os.path.join(self.builddir, 'CMakeCache.txt'),
                       os.path.join(self.builddir, 'cmake_install.cmake'),
                       os.path.join(self.builddir, 'CMakeFiles')]
            for f in rmfiles:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                elif os.path.isfile(f):
                    os.remove(f)
            if os.path.isdir(self.builddir) and (not os.listdir(self.builddir)):
                os.rmdir(self.builddir)
        super(CMakeModelDriver, self).cleanup()
