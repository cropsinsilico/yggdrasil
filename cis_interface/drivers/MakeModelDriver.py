import os
from cis_interface import tools, platform
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.drivers import GCCModelDriver
from cis_interface.schema import register_component, inherit_schema


def setup_environ(compile_flags=[], linker_flags=[]):
    r"""Set environment variables CISCCFLAGS and CISLDFLAGS.

    Args:
        compile_flags (list, optional): Additional compile flags that
            should be set. Defaults to [].
        linker_flags (list, optional): Additional linker flags that
            should be set. Defaults to [].

    """
    _compile_flags, _linker_flags = GCCModelDriver.get_flags()
    os.environ['CISCCFLAGS'] = ' '.join(compile_flags + _compile_flags)
    os.environ['CISLDFLAGS'] = ' '.join(linker_flags + _linker_flags)


@register_component
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
            Defaults to 'make' on linux/osx and 'nmake' on windows.
        makefile (str, optional): Path to make file either relative to makedir
            or absolute. Defaults to Makefile.
        makedir (str, optional): Directory where make should be invoked from
            if it is not the same as the directory containing the makefile.
            Defaults to directory containing makefile if an absolute path is
            provided, otherwise self.working_dir.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        compiled (bool): True if the compilation was successful, False otherwise.
        target (str): Name of executable that should be created and called.
        make_command (str): Command that should be used for make.
        makedir (str): Directory where make should be invoked from.
        makefile (str): Path to make file either relative to makedir or absolute.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.

    """

    _language = 'make'
    _schema = inherit_schema(ModelDriver._schema, 'language', _language,
                             make_command={'type': 'string', 'required': False},
                             makefile={'type': 'string', 'required': False},
                             makedir={'type': 'string', 'required': False})

    def __init__(self, name, args, make_command=None, makedir=None,
                 makefile=None, **kwargs):
        super(MakeModelDriver, self).__init__(name, args, **kwargs)
        if not tools._c_library_avail:  # pragma: windows
            raise RuntimeError("No library available for models written in C/C++.")
        self.debug('')
        self.compiled = False
        if make_command is None:
            if platform._is_win:  # pragma: windows
                make_command = 'nmake'
            else:
                make_command = 'make'
        self.target = self.args[0]
        if makedir is None:
            if (makefile is not None) and os.path.isabs(makefile):
                makedir = os.path.dirname(makefile)
            else:
                makedir = self.working_dir
        if makefile is None:
            makefile = 'Makefile'
        self.make_command = make_command
        self.makedir = makedir
        self.makefile = makefile
        self.target_file = os.path.join(self.makedir, self.target)
        self.args[0] = self.target_file
        # Set environment variables
        self.debug("Setting environment variables.")
        compile_flags = ['-DCIS_DEBUG=%d' % self.logger.getEffectiveLevel()]
        setup_environ(compile_flags=compile_flags)
        # Compile in a new process
        self.debug("Making target.")
        self.make_target(self.target)

    def make_target(self, target):
        r"""Run the make command to make the target.

        Args:
            target (str): Target that should be made.

        Raises:
            RuntimeError: If there is an error in running the make.
        
        """
        curdir = os.getcwd()
        os.chdir(self.makedir)
        if self.make_command == 'nmake':  # pragma: windows
            make_opts = ['/NOLOGO', '/F']
        else:
            make_opts = ['-f']
        make_args = [self.make_command] + make_opts + [self.makefile, target]
        self.debug(' '.join(make_args))
        if not os.path.isfile(self.makefile):
            os.chdir(curdir)
            raise IOError("Makefile %s not found" % self.makefile)
        comp_process = tools.popen_nobuffer(make_args)
        output, err = comp_process.communicate()
        exit_code = comp_process.returncode
        os.chdir(curdir)
        if exit_code != 0:
            self.error(output)
            raise RuntimeError("Make failed with code %d." % exit_code)
        self.debug('Make complete')

    def cleanup(self):
        r"""Remove compile executable."""
        if (self.target_file is not None) and os.path.isfile(self.target_file):
            self.make_target('clean')
        super(MakeModelDriver, self).cleanup()
