import os
from cis_interface import tools, platform
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.drivers import GCCModelDriver
from cis_interface.schema import register_component, inherit_schema
if platform._is_win:  # pragma: windows
    _default_make_command = 'nmake'
else:
    _default_make_command = 'make'
_default_makefile = 'Makefile'


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
            Defaults to 'make' on Linux/MacOS and 'nmake' on windows.
        makefile (str, optional): Path to make file either absolute, relative to
            makedir (if provided), or relative to working_dir. Defaults to
            Makefile.
        makedir (str, optional): Directory where make should be invoked from
            if it is not the same as the directory containing the makefile.
            Defaults to directory containing makefile if provided, otherwise
            self.working_dir.
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
    _schema_properties = inherit_schema(
        ModelDriver._schema_properties,
        {'make_command': {'type': 'string', 'default': _default_make_command},
         'makefile': {'type': 'string', 'default': _default_makefile},
         'makedir': {'type': 'string'}})  # default will depend on makefile

    def __init__(self, name, args, **kwargs):
        super(MakeModelDriver, self).__init__(name, args, **kwargs)
        if not self.is_installed():  # pragma: windows
            raise RuntimeError("No library available for models written in C/C++.")
        self.debug('')
        self.compiled = False
        self.target = self.args[0]
        if not os.path.isabs(self.makefile):
            if self.makedir is not None:
                self.makefile = os.path.normpath(
                    os.path.join(self.makedir, self.makefile))
            else:
                self.makefile = os.path.normpath(
                    os.path.join(self.working_dir, self.makefile))
        if self.makedir is None:
            self.makedir = os.path.dirname(self.makefile)
        self.target_file = os.path.join(self.makedir, self.target)
        self.args[0] = self.target_file
        # Set environment variables
        self.debug("Setting environment variables.")
        compile_flags = ['-DCIS_DEBUG=%d' % self.logger.getEffectiveLevel()]
        setup_environ(compile_flags=compile_flags)
        # Compile in a new process
        self.debug("Making target.")
        self.make_target(self.target)

    @classmethod
    def is_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        return (len(tools.get_installed_comm(language='c')) > 0)

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
