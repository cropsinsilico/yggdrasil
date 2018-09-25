import os
import logging
from cis_interface import platform, tools
from cis_interface.config import cis_cfg
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface.schema import register_component, inherit_schema


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')
_incl_seri = os.path.join(_top_dir, 'serialize')
_incl_comm = os.path.join(_top_dir, 'communication')
_incl_regex = os.path.join(_top_dir, 'regex')
_regex_win32_lib = os.path.join(_incl_regex, 'regex_win32.lib')


def get_zmq_flags(for_cmake=False):
    r"""Get the necessary flags for compiling & linking with zmq libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    _compile_flags = []
    _linker_flags = []
    if tools._zmq_installed_c:
        if platform._is_win:  # pragma: windows
            for l in ["libzmq", "czmq"]:
                plib = cis_cfg.get('windows', '%s_static' % l, False)
                pinc = cis_cfg.get('windows', '%s_include' % l, False)
                if not (plib and pinc):  # pragma: debug
                    raise Exception("Could not locate %s .lib and .h files." % l)
                pinc_d = os.path.dirname(pinc)
                plib_d, plib_f = os.path.split(plib)
                _compile_flags.append("-I%s" % pinc_d)
                if for_cmake:
                    _linker_flags.append(plib)
                else:
                    _linker_flags += [plib_f, '/LIBPATH:"%s"' % plib_d]
        else:
            _linker_flags += ["-lczmq", "-lzmq"]
        _compile_flags += ["-DZMQINSTALLED"]
    return _compile_flags, _linker_flags


def get_ipc_flags(for_cmake=False):
    r"""Get the necessary flags for compiling & linking with ipc libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    _compile_flags = []
    _linker_flags = []
    if tools._ipc_installed:
        _compile_flags += ["-DIPCINSTALLED"]
    return _compile_flags, _linker_flags


def get_flags(for_cmake=False):
    r"""Get the necessary flags for compiling & linking with CiS libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    _compile_flags = []
    _linker_flags = []
    if not tools._c_library_avail:  # pragma: windows
        logging.warning("No library installed for models written in C")
        return _compile_flags, _linker_flags
    if platform._is_win:  # pragma: windows
        assert(os.path.isfile(_regex_win32_lib))
        _compile_flags += ["/nologo", "-D_CRT_SECURE_NO_WARNINGS"]
        _compile_flags += ['-I' + _top_dir]
        if not for_cmake:
            _regex_win32 = os.path.split(_regex_win32_lib)
            _linker_flags += [_regex_win32[1], '/LIBPATH:"%s"' % _regex_win32[0]]
    if tools._zmq_installed_c:
        zmq_flags = get_zmq_flags(for_cmake=for_cmake)
        _compile_flags += zmq_flags[0]
        _linker_flags += zmq_flags[1]
    if tools._ipc_installed:
        ipc_flags = get_ipc_flags(for_cmake=for_cmake)
        _compile_flags += ipc_flags[0]
        _linker_flags += ipc_flags[1]
    for x in [_incl_interface, _incl_io, _incl_comm, _incl_seri, _incl_regex]:
        _compile_flags += ["-I" + x]
    if tools.get_default_comm() == 'IPCComm':
        _compile_flags += ["-DIPCDEF"]
    return _compile_flags, _linker_flags


def build_regex_win32(using_cmake=False):  # pragma: windows
    r"""Build the regex_win32 library."""
    _regex_win32_dir = os.path.dirname(_regex_win32_lib)
    _regex_win32_cpp = os.path.join(_regex_win32_dir, 'regex_win32.cpp')
    _regex_win32_obj = os.path.join(_regex_win32_dir, 'regex_win32.obj')
    # Compile object
    cmd = ['cl', '/c', '/Zi', '/EHsc',
           '/I', '%s' % _regex_win32_dir, _regex_win32_cpp]
    # '/out:%s' % _regex_win32_obj,
    comp_process = tools.popen_nobuffer(cmd, cwd=_regex_win32_dir)
    output, err = comp_process.communicate()
    exit_code = comp_process.returncode
    if exit_code != 0:  # pragma: debug
        print(' '.join(cmd))
        tools.print_encoded(output, end="")
        raise RuntimeError("Could not create regex_win32.obj")
    assert(os.path.isfile(_regex_win32_obj))
    # Create library
    cmd = ['lib', '/out:%s' % _regex_win32_lib, _regex_win32_obj]
    comp_process = tools.popen_nobuffer(cmd, cwd=_regex_win32_dir)
    output, err = comp_process.communicate()
    exit_code = comp_process.returncode
    if exit_code != 0:  # pragma: debug
        print(' '.join(cmd))
        tools.print_encoded(output, end="")
        raise RuntimeError("Could not build regex_win32.lib")
    assert(os.path.isfile(_regex_win32_lib))


if platform._is_win and (not os.path.isfile(_regex_win32_lib)):  # pragma: windows
    build_regex_win32()


def do_compile(src, out=None, cc=None, ccflags=None, ldflags=None,
               working_dir=None):
    r"""Compile a C/C++ program with necessary interface libraries.

    Args:
        src (list): List of source files.
        out (str, optional): Path where compile executable should be saved.
            Defaults to name of source file without extension on linux/osx and
            with .exe extension on windows.
        cc (str, optional): Compiler command. Defaults to gcc/g++ on linux/osx
            and cl on windows.
        ccflags (list, optional): Compiler flags. Defaults to [].
        ldflags (list, optional): Linker flags. Defaults to [].
        working_dir (str, optional): Working directory that input file paths are
            relative to. Defaults to current working directory.

    Returns:
        str: Full path to the compiled executable.

    """
    if working_dir is None:  # pragma: no cover
        working_dir = os.getcwd()
    if ccflags is None:  # pragma: no cover
        ccflags = []
    if ldflags is None:  # pragma: no cover
        ldflags = []
    _compile_flags, _linker_flags = get_flags()
    ldflags0 = _linker_flags
    if platform._is_win:  # pragma: windows
        ccflags0 = ['/W4', '/Zi', "/EHsc"]
    else:
        ccflags0 = ['-g', '-Wall']
    ccflags0 += _compile_flags
    # Change format for path (windows compat of examples)
    if platform._is_win:  # pragma: windows
        for i in range(len(src)):
            src[i] = os.path.join(*(src[i].split('/')))
    # Get primary file
    cfile = src[0]
    src_base, src_ext = os.path.splitext(cfile)
    # Select compiler
    if cc is None:
        if platform._is_win:  # pragma: windows
            cc = 'cl'
        else:
            if src_ext in ['.c']:
                cc = 'gcc'
            else:
                cc = 'g++'
    # Create/fix executable
    if out is None:
        if platform._is_win:  # pragma: windows
            osuffix = '_%s.exe' % src_ext[1:]
        else:
            osuffix = '_%s.out' % src_ext[1:]
        out = src_base + osuffix
    if not os.path.isabs(out):
        out = os.path.normpath(os.path.join(working_dir, out))
    # Get flag specifying standard library
    if '++' in cc and (not platform._is_win):
        std_flag = None
        for a in ccflags:
            if a.startswith('-std='):
                std_flag = a
                break
        if std_flag is None:
            ccflags.append('-std=c++11')
    # Construct compile arguments
    compile_args = [cc]
    if not platform._is_win:
        compile_args += ["-o", out]
    compile_args += src + ccflags0 + ccflags
    if platform._is_win:  # pragma: windows
        compile_args += ['/link', '/out:%s' % out]
    compile_args += ldflags0 + ldflags
    if os.path.isfile(out):
        os.remove(out)
    # Compile
    comp_process = tools.popen_nobuffer(compile_args)
    output, err = comp_process.communicate()
    exit_code = comp_process.returncode
    if exit_code != 0:  # pragma: debug
        print(' '.join(compile_args))
        tools.print_encoded(output, end="")
        raise RuntimeError("Compilation failed with code %d." % exit_code)
    assert(os.path.isfile(out))
    return out


@register_component
class GCCModelDriver(ModelDriver):
    r"""Class for running gcc compiled drivers.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. If the first element ends with '.c', the driver attempts to
            compile the code with the necessary interface include directories.
            Additional arguments that start with '-I' are included in the
            compile command. Others are assumed to be runtime arguments.
        cc (str, optional): C/C++ Compiler that should be used. Defaults to
            gcc for '.c' files, and g++ for '.cpp' or '.cc' files on Linux or
            OSX. Defaults to cl on Windows.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes (in additon to parent class's):
        compiled (bool): True if the compilation was succesful. False otherwise.
        cfile (str): Source file.
        cc (str): C/C++ Compiler that should be used.
        flags (list): List of compiler flags.
        efile (str): Compiled executable file.

    Raises:
        RuntimeError: If neither the IPC or ZMQ C libraries are available.
        RuntimeError: If the compilation fails.

    """

    _language = ['c', 'c++', 'cpp']
    _schema = inherit_schema(ModelDriver._schema, 'language', _language,
                             cc={'type': 'string', 'required': False})

    def __init__(self, name, args, cc=None, **kwargs):
        super(GCCModelDriver, self).__init__(name, args, **kwargs)
        if not tools._c_library_avail:  # pragma: windows
            raise RuntimeError("No library available for models written in C/C++.")
        self.debug('')
        self.cc = cc
        # Prepare arguments to compile the file
        self.parse_arguments(self.args)
        self.debug("Compiling")
        self.efile = do_compile(self.src, out=self.efile, cc=self.cc,
                                ccflags=self.ccflags, ldflags=self.ldflags,
                                working_dir=self.working_dir)
        assert(os.path.isfile(self.efile))
        self.debug("Compiled %s", self.efile)
        if platform._is_win:  # pragma: windows
            self.args = [os.path.splitext(self.efile)[0]]
        else:
            self.args = [os.path.join(".", self.efile)]
        self.args += self.run_args
        self.debug('Compiled executable with %s', self.cc)

    def parse_arguments(self, args):
        r"""Sort arguments based on their syntax. Arguments ending with '.c' or
        '.cpp' are considered source and the first one will be compiled to an
        executable. Arguments starting with '-L' or '-l' are treated as linker
        flags. Arguments starting with '-' are treated as compiler flags. Any
        arguments that do not fall into one of the categories will be treated
        as command line arguments for the compiled executable.

        Args:
            args (list): List of arguments provided.

        Raises:
            RuntimeError: If there is not a valid source file in the argument
                list.

        """
        self.src = []
        self.ldflags = []
        self.ccflags = []
        self.ccflags.append('-DCIS_DEBUG=%d' % self.logger.getEffectiveLevel())
        self.run_args = []
        self.efile = None
        is_object = False
        is_link = False
        for a in args:
            if a.endswith('.c') or a.endswith('.cpp') or a.endswith('.cc'):
                self.src.append(a)
            elif a.lower().startswith('-l') or is_link:
                if a.lower().startswith('/out:'):  # pragma: windows
                    self.efile = a[5:]
                elif a.lower().startswith('-l') and platform._is_win:  # pragma: windows
                    a1 = '/LIBPATH:"%s"' % a[2:]
                    if a1 not in self.ldflags:
                        self.ldflags.append(a1)
                elif a not in self.ldflags:
                    self.ldflags.append(a)
            elif a == '-o':
                # Next argument should be the name of the executable
                is_object = True
            elif a.lower() == '/link':  # pragma: windows
                # Following arguments should be linker options
                is_link = True
            elif a.startswith('-') or (platform._is_win and a.startswith('/')):
                if a not in self.ccflags:
                    self.ccflags.append(a)
            else:
                if is_object:
                    # Previous argument was -o flag
                    self.efile = a
                    is_object = False
                else:
                    self.run_args.append(a)
        # Check source file
        if len(self.src) == 0:
            raise RuntimeError("Could not locate a source file in the " +
                               "provided arguments.")
        
    def remove_products(self):
        r"""Delete products produced during the compilation process."""
        if self.efile is None:  # pragma: debug
            return
        products = [self.efile]
        if platform._is_win:  # pragma: windows
            base = os.path.splitext(self.efile)[0]
            products = [base + ext for ext in ['.ilk', '.pdb', '.obj']]
        for p in products:
            if os.path.isfile(p):
                os.remove(p)

    def cleanup(self):
        r"""Remove compile executable."""
        self.remove_products()
        super(GCCModelDriver, self).cleanup()
