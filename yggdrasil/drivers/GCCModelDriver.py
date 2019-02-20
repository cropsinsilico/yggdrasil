import os
import copy
import logging
from yggdrasil import platform, tools
from yggdrasil.config import ygg_cfg
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.schema import register_component, inherit_schema


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')
_incl_seri = os.path.join(_top_dir, 'serialize')
_incl_comm = os.path.join(_top_dir, 'communication')
_incl_regex = os.path.join(_top_dir, 'regex')
_incl_dtype = os.path.join(_top_dir, 'metaschema', 'datatypes')
_regex_win32_lib = os.path.join(_incl_regex, 'regex_win32.lib')
if platform._is_win:  # pragma: windows
    _prefix = ''
    _static_ext = '.lib'
    _shared_ext = '.dll'
else:
    _prefix = 'lib'
    _static_ext = '.a'
    if platform._is_mac:
        _shared_ext = '.dylib'
    else:
        _shared_ext = '.so'
_datatypes_static_lib = os.path.join(_incl_dtype, _prefix + 'datatypes' + _static_ext)
_api_static_c = os.path.join(_incl_interface, _prefix + 'ygg' + _static_ext)
_api_static_cpp = os.path.join(_incl_interface, _prefix + 'ygg++' + _static_ext)
_datatypes_shared_lib = os.path.join(_incl_dtype, _prefix + 'datatypes' + _shared_ext)
_api_shared_c = os.path.join(_incl_interface, _prefix + 'ygg' + _shared_ext)
_api_shared_cpp = os.path.join(_incl_interface, _prefix + 'ygg++' + _shared_ext)
_c_installed = ((len(tools.get_installed_comm(language='c')) > 0)
                and (ygg_cfg.get('c', 'rapidjson_include', None) is not None))


def get_zmq_flags(for_cmake=False, for_api=False):
    r"""Get the necessary flags for compiling & linking with zmq libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.
        for_api (bool, optional): If True, the returned flags will match those
            required for compiling the API static library. Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    _compile_flags = []
    _linker_flags = []
    # ZMQ library
    if tools.is_comm_installed('ZMQComm', language='c'):
        if platform._is_win:  # pragma: windows
            for l in ["libzmq", "czmq"]:
                plib = ygg_cfg.get('windows', '%s_static' % l, False)
                pinc = ygg_cfg.get('windows', '%s_include' % l, False)
                if not (plib and pinc):  # pragma: debug
                    raise Exception("Could not locate %s .lib and .h files." % l)
                pinc_d = os.path.dirname(pinc)
                plib_d, plib_f = os.path.split(plib)
                _compile_flags.append("-I%s" % pinc_d)
                if for_cmake:
                    _linker_flags.append(plib)
                else:
                    _linker_flags += ['/LIBPATH:%s' % plib_d, plib_f]
        else:
            _linker_flags += ["-lczmq", "-lzmq"]
        _compile_flags += ["-DZMQINSTALLED"]
    return _compile_flags, _linker_flags


def get_ipc_flags(for_cmake=False, for_api=False):
    r"""Get the necessary flags for compiling & linking with ipc libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.
        for_api (bool, optional): If True, the returned flags will match those
            required for compiling the API static library. Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    _compile_flags = []
    _linker_flags = []
    if tools.is_comm_installed('IPCComm', language='c'):
        _compile_flags += ["-DIPCINSTALLED"]
    return _compile_flags, _linker_flags


def get_flags(for_cmake=False, for_api=False, cpp=False):
    r"""Get the necessary flags for compiling & linking with Ygg libraries.

    Args:
        for_cmake (bool, optional): If True, the returned flags will match the
            format required by cmake. Defaults to False.
        for_api (bool, optional): If True, the returned flags will match those
            required for compiling the API static library. Defaults to False.
        cpp (bool, optional): If True, flags for compiling a C++ model are
            returned. Otherwise, flags for compiling a C model are returned.
            Defaults to False.

    Returns:
        tuple(list, list): compile and linker flags.

    """
    if cpp:
        _compile_flags = os.environ.get('CXXFLAGS', '').split()
    else:
        _compile_flags = os.environ.get('CFLAGS', '').split()
    _linker_flags = os.environ.get('LDFLAGS', '').split()
    if not _c_installed:  # pragma: windows
        logging.warning("No library installed for models written in C")
        return _compile_flags, _linker_flags
    if platform._is_win:  # pragma: windows
        _compile_flags += ["/nologo", "-D_CRT_SECURE_NO_WARNINGS"]
        _compile_flags += ['-I' + _top_dir]
        _compile_flags += ['-I' + _incl_interface]
        if not for_cmake:
            _regex_win32 = os.path.split(_regex_win32_lib)
            _compile_flags += ['-I' + _regex_win32[0]]
    if tools.is_comm_installed('ZMQComm', language='c'):
        zmq_flags = get_zmq_flags(for_cmake=for_cmake, for_api=for_api)
        _compile_flags += zmq_flags[0]
        _linker_flags += zmq_flags[1]
    if tools.is_comm_installed('IPCComm', language='c'):
        ipc_flags = get_ipc_flags(for_cmake=for_cmake, for_api=for_api)
        _compile_flags += ipc_flags[0]
        _linker_flags += ipc_flags[1]
    # Include dir
    for x in [_incl_interface, _incl_io, _incl_comm, _incl_seri, _incl_regex,
              _incl_dtype]:
        _compile_flags += ["-I" + x]
    # Interface library
    if not for_api:
        if cpp:
            plib = _api_static_cpp
        else:
            plib = _api_static_c
        plib_d, plib_f = os.path.split(plib)
        if for_cmake:
            _linker_flags.append(plib)
            # _linker_flags += [_api_static_c, _api_static_cpp]
        elif platform._is_win:  # pragma: windows
            _linker_flags += ['/LIBPATH:%s' % plib_d, plib_f]
        else:
            _linker_flags += ["-L" + plib_d]
            _linker_flags += ["-l" + os.path.splitext(plib_f)[0].split(_prefix)[-1]]
    if tools.get_default_comm() == 'IPCComm':
        _compile_flags += ["-DIPCDEF"]
    return _compile_flags, _linker_flags


def get_cc(cpp=False, shared=False, static=False, linking=False):
    r"""Get command line compiler utility.

    Args:
        cpp (bool, optional): If True, value is returned assuming the source
            is written in C++. Defaults to False.
        shared (bool, optional): If True, the command line utility will be used
            to combine object files into a shared library. Defaults to False.
        static (bool, optional): If True, the command line utility will be used
            to combine object files into a static library. Defaults to False.
        linking (bool, optional): If True, the command line utility will be used
            for linking. Defaults to False.

    Returns:
        str: Command line compiler.

    """
    if cpp:
        cc_env = 'CXX'
    else:
        cc_env = 'CC'
    if platform._is_win:  # pragma: windows
        if shared:
            cc = 'LINK'
        elif static:
            cc = 'LIB'
        elif linking:
            cc = 'LINK'
        else:
            cc = os.environ.get(cc_env, 'cl')
    elif platform._is_mac:
        if static:
            cc = os.environ.get('LIBTOOL', 'libtool')
        elif cpp:
            cc = os.environ.get(cc_env, 'clang++')
        else:
            cc = os.environ.get(cc_env, 'clang')
    else:
        if static:
            cc = os.environ.get('AR', 'ar')
        elif cpp:
            cc = os.environ.get(cc_env, 'g++')
        else:
            cc = os.environ.get(cc_env, 'gcc')
    return cc


def call_compile(src, out=None, flags=[], overwrite=False, verbose=False,
                 cpp=None, working_dir=None):
    r"""Compile a source file, checking for errors.

    Args:
        src (str): Full path to source file.
        out (str, optional): Full path to the output object file that should
            be created. Defaults to None and is created from the provided source
            file.
        flags (list, optional): Compilation flags. Defaults to [].
        overwrite (bool, optional): If True, the existing compile file will be
            overwritten. Otherwise, it will be kept and this function will
            return without recompiling the source file.
        verbose (bool, optional): If True, the compilation command and any output
            produced by the command will be displayed on success. Defaults to
            False.
        cpp (bool, optional): If True, value is returned assuming the source
            is written in C++. Defaults to False.
        working_dir (str, optional): Working directory that input file paths are
            relative to. Defaults to current working directory.

    Returns:
        str: Full path to compiled source.

    """
    # Set defaults
    if working_dir is None:
        working_dir = os.getcwd()
    flags = copy.deepcopy(flags)
    if platform._is_win:  # pragma: windows
        flags = ['/W4', '/Zi', "/EHsc"] + flags
    else:
        flags = ['-g', '-Wall'] + flags
    src_base, src_ext = os.path.splitext(src)
    if cpp is None:
        cpp = False
        if src_ext in ['.hpp', '.cpp']:
            cpp = True
    if platform._is_win:  # pragma: windows
        if cpp:
            flags.insert(2, '/TP')
        else:
            flags.insert(2, '/TP')
            # TODO: Currently everything compiled as C++ on windows to allow use of
            # complex types
            # flags.insert(2, '/TC')
    # Add standard library flag
    std_flag = None
    for i, a in enumerate(flags):
        if a.startswith('-std='):
            std_flag = i
            break
    if cpp and (not platform._is_win):
        if std_flag is None:
            flags.append('-std=c++11')
    else:
        if std_flag is not None:
            flags.pop(i)
    # Get compiler command
    cc = get_cc(cpp=cpp)
    # Get output if not provided
    if out is None:
        if platform._is_win:  # pragma: windows
            out_ext = '.obj'
        else:
            out_ext = '.o'
        out = src_base + '_' + src_ext[1:] + out_ext
    if not os.path.isabs(out):
        out = os.path.normpath(os.path.join(working_dir, out))
    # Construct arguments
    args = [cc, "-c"] + flags + [src]
    if not platform._is_win:
        args += ["-o", out]
    else:  # pragma: windows
        args.insert(1, '/Fo%s' % out)
    # Check for file
    if os.path.isfile(out):
        if overwrite:
            os.remove(out)
        else:
            return out
    # Call compiler
    comp_process = tools.popen_nobuffer(args)
    output, err = comp_process.communicate()
    exit_code = comp_process.returncode
    if exit_code != 0:  # pragma: debug
        print(' '.join(args))
        tools.print_encoded(output, end="")
        raise RuntimeError("Compilation of %s failed with code %d." %
                           (out, exit_code))
    if not os.path.isfile(out):  # pragma: debug
        print(' '.join(args))
        raise RuntimeError("Compilation failed to produce result '%s'" % out)
    logging.info("Compiled %s" % out)
    if verbose:  # pragma: debug
        print(' '.join(args))
        tools.print_encoded(output, end="")
    return out


def call_link(obj, out=None, flags=[], overwrite=False, verbose=False,
              cpp=False, shared=False, static=False, working_dir=None):
    r"""Compile a source file, checking for errors.

    Args:
        obj (list): Object files that should be linked.
        out (str, optional): Full path to output file that should be created.
            If None, the path will be determined from the path to the first
            object file provided. Defaults to False.
        flags (list, optional): Compilation flags. Defaults to [].
        overwrite (bool, optional): If True, the existing compile file will be
            overwritten. Otherwise, it will be kept and this function will
            return without recompiling the source file.
        verbose (bool, optional): If True, the linking command and any output
            produced by the command will be displayed on success. Defaults to
            False.
        cpp (bool, optional): If True, value is returned assuming the source
            is written in C++. Defaults to False.
        shared (bool, optional): If True, the object files are combined into a
            shared library. Defaults to False.
        static (bool, optional): If True, the object files are combined into a
            static library. Defaults to False.
        working_dir (str, optional): Working directory that input file paths are
            relative to. Defaults to current working directory.

    Returns:
        str: Full path to compiled source.

    """
    # Set defaults
    if working_dir is None:
        working_dir = os.getcwd()
    flags = copy.deepcopy(flags)
    if not isinstance(obj, list):
        obj = [obj]
    # Set path if not provided
    if out is None:
        obase = os.path.splitext(obj[0])[0]
        if platform._is_win:  # pragma: windows
            oext = '.exe'
        else:
            oext = '.out'
        out = obase + oext
    if not os.path.isabs(out):
        out = os.path.normpath(os.path.join(working_dir, out))
    # Check for file
    if os.path.isfile(out):
        if overwrite:
            os.remove(out)
        else:
            return out
    # Check extension for information about the result
    if out.endswith('.so') or out.endswith('.dll') or out.endswith('.dylib'):
        shared = True
    elif out.endswith('.a') or out.endswith('.lib'):
        static = True
    # Get compiler
    cc = get_cc(shared=shared, static=static, cpp=cpp, linking=True)
    # Construct arguments
    args = [cc]
    if shared:
        if platform._is_win:  # pragma: windows
            flags.append('/DLL')
        elif platform._is_mac:
            flags.append('-dynamiclib')
        else:
            flags.append('-shared')
        args += flags
    elif static:
        if platform._is_win:  # pragma: windows
            pass
        elif platform._is_mac:
            flags += ['-static']
        else:
            flags += ['-rcs', out]
        args += flags
    if platform._is_win:  # pragma: windows
        args += ['/OUT:%s' % out]
    elif platform._is_mac:
        if shared:
            args += ["-o", out]
        else:
            args += ["-o", out]
    else:
        if static:
            args += [out]
        else:
            args += ["-o", out]
    args += obj
    if not (shared or static):
        args += flags
    # Call linker
    comp_process = tools.popen_nobuffer(args)
    output, err = comp_process.communicate()
    exit_code = comp_process.returncode
    if exit_code != 0:  # pragma: debug
        print(' '.join(args))
        tools.print_encoded(output, end="")
        raise RuntimeError("Linking of %s failed with code %d." %
                           (out, exit_code))
    if not os.path.isfile(out):  # pragma: debug
        print(' '.join(args))
        raise RuntimeError("Linking failed to produce result '%s'" % out)
    logging.info("Linked %s" % out)
    if verbose:  # pragma: debug
        print(' '.join(args))
        tools.print_encoded(output, end="")
    return out


def build_api(cpp=False, overwrite=False, as_shared=False):
    r"""Build api library."""
    # Get paths
    api_src = os.path.join(_incl_interface, 'YggInterface')
    if cpp:
        if as_shared:
            api_lib = _api_shared_cpp
        else:
            api_lib = _api_static_cpp
        api_src += '.cpp'
    else:
        if as_shared:
            api_lib = _api_shared_c
        else:
            api_lib = _api_static_c
        api_src += '.c'
    fname_obj = []
    # Compile regex for windows
    if platform._is_win:  # pragma: windows
        fname_obj.append(build_regex_win32(just_obj=True,
                                           overwrite=overwrite))
    # Get flags (after regex to allow dependencies)
    ccflags0, ldflags0 = get_flags(for_api=True, cpp=cpp)
    if platform._is_linux:
        ccflags0.append('-fPIC')
    # Compile C++ wrapper for data types
    fname_obj.append(build_datatypes(just_obj=True,
                                     overwrite=overwrite))
    # Compile object for the interface
    fname_api_base = api_src
    fname_api_out = call_compile(fname_api_base, flags=ccflags0,
                                 overwrite=overwrite)
    fname_obj.append(fname_api_out)
    # Build static library
    out = call_link(fname_obj, api_lib, cpp=True, overwrite=overwrite)
    return out


def build_datatypes(just_obj=False, overwrite=False, as_shared=False):
    r"""Build the datatypes library."""
    if as_shared:
        dtype_lib = _datatypes_shared_lib
    else:
        dtype_lib = _datatypes_static_lib
    _datatypes_dir = os.path.dirname(dtype_lib)
    _datatypes_cpp = os.path.join(_datatypes_dir, 'datatypes.cpp')
    flags = []
    pinc = ygg_cfg.get('c', 'rapidjson_include', False)
    if not pinc:  # pragma: debug
        raise Exception("Could not locate rapidjson include directory.")
    incl_dir = [_datatypes_dir, _incl_regex, pinc]
    if platform._is_win:  # pragma: windows
        incl_dir.append(_top_dir)
    for x in incl_dir:
        flags += ['-I', x]
    if platform._is_linux:
        flags.append('-fPIC')
    _datatypes_obj = call_compile(_datatypes_cpp,
                                  flags=flags,
                                  overwrite=overwrite)
    if just_obj:
        return _datatypes_obj
    # Compile regex for windows
    if platform._is_win:  # pragma: windows
        _regex_obj = build_regex_win32(just_obj=True,
                                       overwrite=overwrite)
        call_link([_regex_obj, _datatypes_obj], dtype_lib, cpp=True,
                  overwrite=overwrite)
    else:
        call_link(_datatypes_obj, dtype_lib, cpp=True, overwrite=overwrite)
    

def build_regex_win32(just_obj=False, overwrite=False):  # pragma: windows
    r"""Build the regex_win32 library."""
    _regex_win32_dir = os.path.dirname(_regex_win32_lib)
    _regex_win32_cpp = os.path.join(_regex_win32_dir, 'regex_win32.cpp')
    # Compile object
    _regex_win32_obj = call_compile(_regex_win32_cpp,
                                    flags=['/I', _regex_win32_dir],
                                    overwrite=overwrite)
    if just_obj:
        return _regex_win32_obj
    # Create library
    call_link(_regex_win32_obj, _regex_win32_lib, static=True,
              overwrite=overwrite)


if _c_installed:
    if not os.path.isfile(_api_static_c):
        build_api(cpp=False, overwrite=False)
    if not os.path.isfile(_api_static_cpp):
        build_api(cpp=True, overwrite=False)


def do_compile(src, out=None, cc=None, ccflags=None, ldflags=None,
               working_dir=None, overwrite=False, verbose=False):
    r"""Compile a C/C++ program with necessary interface libraries.

    Args:
        src (list): List of source files.
        out (str, optional): Path where compile executable should be saved.
            Defaults to name of source file without extension on Linux/MacOS and
            with .exe extension on windows.
        cc (str, optional): Compiler command. Defaults to gcc/g++ on Linux/MacOS
            and cl on windows.
        ccflags (list, optional): Compiler flags. Defaults to [].
        ldflags (list, optional): Linker flags. Defaults to [].
        working_dir (str, optional): Working directory that input file paths are
            relative to. Defaults to current working directory.
        overwrite (bool, optional): If True, any existing executable and object
            files are overwritten. Defaults to False.
        verbose (bool, optional): If True, the compilation/linking commands and
            any output produced by them will be displayed on success. Defaults
            to False.

    Returns:
        list: Products produced by the compilation. The first element will be
            the executable.

    """
    if ccflags is None:  # pragma: no cover
        ccflags = []
    if ldflags is None:  # pragma: no cover
        ldflags = []
    # Change format for path (windows compat for examples)
    if platform._is_win:  # pragma: windows
        for i in range(len(src)):
            src[i] = os.path.join(*(src[i].split('/')))
    # Get primary file for flags
    src_base, src_ext = os.path.splitext(src[0])
    cpp = (src_ext not in ['.c'])
    ccflags0, ldflags0 = get_flags(cpp=cpp)
    # Compile C++ wrapper
    fname_lib_out = build_datatypes(just_obj=True, overwrite=False)
    # Compile each source file
    fname_src_obj = []
    for isrc in src:
        fname_src_obj.append(call_compile(isrc,
                                          flags=copy.deepcopy(ccflags0 + ccflags),
                                          overwrite=overwrite,
                                          working_dir=working_dir,
                                          verbose=verbose))
    fname_src_obj.append(fname_lib_out)
    # Link compile objects
    out = call_link(fname_src_obj, out, cpp=True,
                    flags=copy.deepcopy(ldflags0 + ldflags),
                    overwrite=overwrite, working_dir=working_dir,
                    verbose=verbose)
    return [out] + fname_src_obj


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
            gcc/clang for '.c' files, and g++/clang++ for '.cpp' or '.cc' files
            on Linux/MacOS. Defaults to cl on Windows.
        overwrite (bool, optional): If True, any existing object or executable
            files for the model are overwritten, otherwise they will only be
            compiled if they do not exist. Defaults to True. Setting this to
            False can be done to improve performance after debugging is complete,
            but this dosn't check if the source files should be changed, so
            users should make sure they recompile after any changes. The value
            of this keyword also determines whether or not any compilation
            products are cleaned up after a run.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes (in additon to parent class's):
        overwrite (bool): If True, any existing compilation products will be
            overwritten by compilation and cleaned up following the run.
            Otherwise, existing products will be used and will remain after
            the run.
        products (list): File created by the compilation.
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
    _schema_properties = inherit_schema(
        ModelDriver._schema_properties,
        {'cc': {'type': 'string'},  # default will depend on whats being compiled
         'overwrite': {'type': 'boolean', 'default': True}})

    def __init__(self, name, args, **kwargs):
        super(GCCModelDriver, self).__init__(name, args, **kwargs)
        if not self.is_installed():  # pragma: windows
            raise RuntimeError("No library available for models written in C/C++.")
        self.debug('')
        # Prepare arguments to compile the file
        self.parse_arguments(self.args)
        self.debug("Compiling")
        self.products = do_compile(self.src, out=self.efile, cc=self.cc,
                                   ccflags=self.ccflags, ldflags=self.ldflags,
                                   overwrite=self.overwrite,
                                   working_dir=self.working_dir)
        self.efile = self.products[0]
        assert(os.path.isfile(self.efile))
        self.debug("Compiled %s", self.efile)
        if platform._is_win:  # pragma: windows
            self.args = [os.path.splitext(self.efile)[0]]
        else:
            self.args = [os.path.join(".", self.efile)]
        self.args += self.run_args
        self.debug('Compiled executable with %s', self.cc)

    @classmethod
    def is_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        return _c_installed

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
        self.ccflags.append('-DYGG_DEBUG=%d' % self.logger.getEffectiveLevel())
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
            raise RuntimeError("Could not locate a source file in the "
                               + "provided arguments.")
        
    def remove_products(self):
        r"""Delete products produced during the compilation process."""
        if getattr(self, 'products', None) is None:  # pragma: debug
            return
        products = self.products
        if platform._is_win:  # pragma: windows
            for x in copy.deepcopy(products):
                base = os.path.splitext(x)[0]
                products += [base + ext for ext in ['.ilk', '.pdb', '.obj']]
        for p in products:
            if os.path.isfile(p):
                T = self.start_timeout()
                while ((not T.is_out) and os.path.isfile(p)):
                    try:
                        os.remove(p)
                    except BaseException:  # pragma: debug
                        if os.path.isfile(p):
                            self.sleep()
                        if T.is_out:
                            raise
                self.stop_timeout()
                if os.path.isfile(p):  # pragma: debug
                    raise RuntimeError("Failed to remove product: %s" % p)

    def cleanup(self):
        r"""Remove compile executable."""
        if self.overwrite:
            self.remove_products()
        super(GCCModelDriver, self).cleanup()
