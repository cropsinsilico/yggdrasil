import subprocess
import os
from cis_interface.communication import _default_comm
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.drivers import GCCModelDriver
from cis_interface.config import cis_cfg


def setup_environ(compile_flags=[], linker_flags=[]):
    r"""Set environment variables CISCCFLAGS and CISLDFLAGS.

    Args:
        compile_flags (list, optional): Additional compile flags that
            should be set. Defaults to [].
        linker_flags (list, optional): Additional linker flags that
            should be set. Defaults to [].

    """
    os.environ['CISCCFLAGS'] = ' '.join(
        compile_flags + GCCModelDriver._compile_flags)
    os.environ['CISLDFLAGS'] = ' '.join(
        linker_flags + GCCModelDriver._linker_flags)


class MakeModelDriver(ModelDriver):
    r"""Class for running make file compiled drivers. Before running the
    make command, the necessary compiler & linker flags for the interface's
    C/C++ library are stored the environment variables CISCCFLAGS and CISLDFLAGS
    respectively. These should be used in the make file to correctly compile
    with the interface's C/C++ libraries.

    Args:
        name (str): Driver name.
        args (str, list): Executable that should be created (make target) and
            any arguments for the executable.
        make_command (str, optional): Command that should be used for make.
            Defaults to 'make'
        makedir (str, optional): Directory where make should be invoked from.
            Defaults to self.workingDir.
        makefile (str, optional): Path to make file either relative to makedir
            or absolute. Defaults to Makefile.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        compiled (bool): True if the compilation was successful, False otherwise.
        target (str): Name of executable that should be created and called.
        make_command (str): Command that should be used for make.
        makedir (str): Directory where make should be invoked from.
        makefile (str): Path to make file either relative to makedir or absolute.

    """
    def __init__(self, name, args, make_command='make', makedir=None,
                 makefile=None, **kwargs):
        super(MakeModelDriver, self).__init__(name, args, **kwargs)
        self.debug()
        self.compiled = False
        self.target = self.args[0]
        if makedir is None:
            makedir = self.workingDir
        if makefile is None:
            makefile = 'Makefile'
        self.make_command = make_command
        self.makedir = makedir
        self.makefile = makefile
        # TODO: Handle absolute path
        self.args[0] = os.path.join(self.makedir, self.target)
        # Set environment variables
        self.debug("Setting environment variables.")
        compile_flags = ['-DCIS_DEBUG=%d' % self.logger.getEffectiveLevel()]
        setup_environ(compile_flags=compile_flags)
        # Compile in a new process
        self.debug("Making target.")
        self.make_target(self.target)
        self.compiled = True

    def make_target(self, target):
        r"""Run the make command to make the target.

        Args:
            target (str): Target that should be made.

        Raises:
            RuntimeError: If there is an error in running the make.
        
        """
        curdir = os.getcwd()
        os.chdir(self.makedir)
        make_args = [self.make_command, '-f', self.makefile, target]
        self.debug(' '.join(make_args))
        comp_process = subprocess.Popen(['stdbuf', '-o0'] + make_args,
                                        bufsize=0, stdin=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE)
        output, err = comp_process.communicate()
        exit_code = comp_process.returncode
        os.chdir(curdir)
        if exit_code != 0:  # pragma: debug
            self.error(output)
            self.make_target('clean')
            raise RuntimeError("Make failed with code %d." % exit_code)
        self.debug('Make complete')

    def run(self):
        r"""Run the compiled executable if it exists."""
        if self.compiled:
            super(MakeModelDriver, self).run()
        else:  # pragma: debug
            self.error("Error compiling.")

    def cleanup(self):
        r"""Remove compile executable."""
        self.make_target('clean')
        super(MakeModelDriver, self).cleanup()


