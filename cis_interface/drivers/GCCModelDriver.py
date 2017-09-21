#
# This should not be used directly by modelers
#
import subprocess
import os
from cis_interface.drivers.ModelDriver import ModelDriver


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


class GCCModelDriver(ModelDriver):
    r"""Class from running gcc compiled driveres.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. If the first element ends with '.c', the driver attempts to
            compile the code with the necessary interface include directories.
            Additional arguments that start with '-I' are included in the
            compile command. Others are assumed to be runtime arguments.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):
        compiled (bool): True if the compilation was succesful. False otherwise.
        cfile (str): Source file.
        gcc (str): Compiler that should be used.
        flags (list): List of compiler flags.
        efile (str): Compiled executable file.

    """

    def __init__(self, name, args, **kwargs):
        super(GCCModelDriver, self).__init__(name, args, **kwargs)
        self.debug()
        # Prepare arguments to compile the file
        # TODO: Allow user to provide a makefile
        self.compile_setup(self.args.pop(0))
        compile_args = [self.gcc, "-g", "-Wall"] + self.flags
        for x in [_incl_interface, _incl_io]:
            compile_args += ["-I" + x]
        run_args = [os.path.join(".", self.efile)]
        for arg in self.args:
            if arg.startswith("-I"):
                compile_args.append(arg)
            else:
                run_args.append(arg)
        compile_args += ["-o", self.efile, self.cfile]
        # Compile in a new process
        self.args = run_args
        self.compiled = True
        self.debug("::compiling")
        comp_process = subprocess.Popen(['stdbuf', '-o0'] + compile_args,
                                        bufsize=0, stdin=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE)
        output, err = comp_process.communicate()
        exit_code = comp_process.returncode
        if exit_code != 0:  # pragma: debug
            self.error(output)
            raise RuntimeError("Compilation failed with code %d." % exit_code)
        self.debug('::compiled executable with gcc')

    def compile_setup(self, cfile):
        r"""Perform setup based on source file.

        Args:
            cfile (str): Full path to source file.

        Raises:
            ValueError: If the source file suffix is not .c or .cpp.

        """
        self.cfile = cfile
        if cfile.endswith('.c'):
            gcc = 'gcc'
            osuffix = '_c.out'
            flags = []
        elif cfile.endswith('.cpp'):
            gcc = 'g++'
            osuffix = '_cpp.out'
            flags = ['-std=c++11']
        else:
            raise ValueError("Supplied file is not C or C++ code.")
        self.gcc = gcc
        self.flags = flags
        self.efile = os.path.splitext(cfile)[0] + osuffix

    def run(self):
        r"""Run the compiled executable if it exists."""
        if self.compiled:
            super(GCCModelDriver, self).run()
        else:  # pragma: debug
            self.error("Error compiling.")

    def cleanup(self):
        r"""Remove compile executable."""
        if os.path.isfile(self.efile):
            os.remove(self.efile)
        super(GCCModelDriver, self).cleanup()
