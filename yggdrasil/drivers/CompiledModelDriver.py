import os
import re
import six
import copy
import logging
import warnings
import subprocess
from collections import OrderedDict
from yggdrasil import platform, backwards, tools, scanf
from yggdrasil.config import ygg_cfg, locate_file
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.components import import_component


_compiler_registry = OrderedDict()
_linker_registry = OrderedDict()
_archiver_registry = OrderedDict()
_default_libtype = 'static'


def get_compilation_tool_registry(tooltype):
    r"""Return the registry containing compilation tools of the specified type.

    Args:
        tooltype (str): Type of tool. Valid values include 'compiler', 'linker',
            and 'archiver'.

    Returns:
        collections.OrderedDict: Registry for specified type.

    Raises:
        ValueError: If tooltype is not a valid value (i.e. 'compiler', 'linker',
            or 'archiver').

    """
    if tooltype == 'compiler':
        global _compiler_registry
        reg = _compiler_registry
    elif tooltype == 'linker':
        global _linker_registry
        reg = _linker_registry
    elif tooltype == 'archiver':
        global _archiver_registry
        reg = _archiver_registry
    else:
        raise ValueError(("tooltype '%s' is not supported. This keyword must "
                          "be one of 'compiler', 'linker', or 'archiver'.")
                         % tooltype)
    return reg


def find_compilation_tool(tooltype, language, allow_failure=False):
    r"""Return the prioritized class for a compilation tool of a certain type
    that can handle the specified language.

    Args:
        tooltype (str): Type of tool. Valid values include 'compiler', 'linker',
            and 'archiver'.
        allow_failure (bool, optional): If True and a tool cannot be located,
            None will be returned. Otherwise, an error will be raised if a tool
            cannot be located. Defaults to False.

    Returns:
        str: Name of the determined tool type.

    Raises:
        RuntimeError: If a tool cannot be located for the specified language on
            the current platform and allow_failure is False.

    """
    out = None
    reg = get_compilation_tool_registry(tooltype).get('by_language', {})
    for kname, v in reg.get(language, {}).items():
        if (platform._platform in v.platforms) and v.is_installed():
            out = kname
    if out is None:
        raise RuntimeError("Could not locate a %s tool." % tooltype)
    return out


def get_compilation_tool(tooltype, name):
    r"""Return the class providing information about a compilation tool.

    Args:
        tooltype (str): Type of tool. Valid values include 'compiler', 'linker',
            and 'archiver'.
        name (str): Name or path to the desired compilation tool.

    Returns:
        CompilationToolBase: Class providing access to the specified tool.

    Raises:
        ValueError: If a tool with the provided name cannot be located.

    """
    reg = get_compilation_tool_registry(tooltype)
    if name in reg:
        return reg[name]
    # Try variations before raising an error
    if name.lower() in reg:
        return reg[name.lower()]
    name = os.path.basename(name)
    if name in reg:
        return reg[name]
    name = os.path.splitext(name)[0]
    if name in reg:
        return name
    if name.lower() in reg:
        return reg[name.lower()]
    raise ValueError("Could not locate a %s tool with name '%s'"
                     % (tooltype, name))


class CompilationToolMeta(type):
    r"""Meta class for registering compilers."""
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if not name.endswith('Base'):
            cls.before_registration(cls)
            assert(cls.name is not None)
            assert(len(cls.languages) > 0)
            reg = get_compilation_tool_registry(cls.tooltype)
            # Register by name & language
            if cls.name in cls.aliases:  # pragma: debug
                raise ValueError(("The name '%s' for class %s is also in "
                                  "its list of aliases: %s")
                                 % (cls.name, name, cls.aliases))
            if 'by_language' not in reg:
                reg['by_language'] = OrderedDict()
            for l in cls.languages:
                if l not in reg['by_language']:
                    reg['by_language'][l] = OrderedDict()
            for x in [cls.name] + cls.aliases:
                # Register by name
                if x in reg:
                    raise ValueError("%s name '%s' already registered."
                                     % (cls.tooltype.title(), x))
                reg[x] = cls
                # Register by language
                for l in cls.languages:
                    if x in reg['by_language'][l]:
                        raise ValueError(("%s name '%s' already registered for "
                                          "%s language.")
                                         % (cls.tooltype.title(), x, l))
                    reg['by_language'][l][x] = cls
        return cls


@six.add_metaclass(CompilationToolMeta)
class CompilationToolBase(object):
    r"""Base class for compilation command line tools.

    Attributes:
        name (str): Tool name used for registration and as a default for the
            executable.
        aliases (list): Alternative names that the tool might have.
        tooltype (str): Tool type. One of 'compiler', 'linker', or 'archiver'.
        languages (list): Programming languages that this tool can be used on.
        platforms (list): Platforms that the tool is available on.
        default_executable (str): The default tool executable command if
            different than the tool name.
        default_executable_env (str): Environment variable where the executable
            command might be stored.
        default_flags (list): Default flags that should be used when calling the
            tool (e.g. for verbose output or enhanced warnings).
        default_flags_env (str): Environment variable where default flags for
            the tools might be stored.
        output_key (str): Option key indicating the output file name.
        output_first (bool): If True, the output key (and its value) are put in
            front of the other flags.
        flag_options (collections.OrderedDict): Mappings between keyword
            arguments passed to get_flags and command line tool flags. Keys
            indicate the keyword argument that will be processed in Python
            and values are the string used with the tool on the command line to
            indicate the desired flag. Flags that contain '%s' will be formatted
            with values passed to get_flags as the designated keyword argument.
            Flags that do not contain '%s' will assumed to act on the following
            argument. If the value passed to get_flags under the designated
            keyword argument is not a boolean, it will be appended to the flag
            list following the corresponding flag. If the value is a boolean and
            it is True, only the flag will be added to the list of flags. The
            order of entries indicates the order the flags should be added to
            the list.
        search_path_env (str): Environment variables containing a list of paths
            to search for library files.
        search_path_conda (str): Path relative to the conda prefix that should
            be searched if the CONDA_PREFIX environment variable is set.
        search_path_flags (list): Flags that should be passed to the tool
            executable in order to locate the search path.
        search_regex_begin (str): Search string indicating where the set of
            paths begins in the output from running the tool executable with the
            search_path_flags. If None, the search is performed from the very
            beginning of the output.
        search_regex_end (str): Search string indicating where the set of
            paths ends in the output from running the tool executable with the
            search_path_flags. If None, the search is performed to the very end
            of the output.
        search_regex (list): Regex strings that should be used to locate paths
            in the output from running the tool executable with the
            search_path_flags.

    """

    name = None
    aliases = []
    tooltype = None
    languages = []
    platforms = ['Windows', 'MacOS', 'Linux']  # all by default
    default_executable = None
    default_executable_env = None
    default_flags = []
    default_flags_env = None
    output_key = '-o'
    output_first = False
    flag_options = OrderedDict()
    search_path_env = None
    search_path_conda = None
    search_path_flags = None
    search_regex_begin = None
    search_regex_end = None
    search_regex = ['([^\n]+)']

    _language_ext = None  # only update once per class
    
    def __init__(self, **kwargs):
        for k in ['executable', 'flags']:
            v = kwargs.pop(k, None)
            if v is not None:
                setattr(self, k, v)
        if len(kwargs) > 0:
            raise RuntimeError("Unused keyword arguments: %s" % kwargs.keys())
        super(CompilationToolBase, self).__init__(**kwargs)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        if cls.name is None:
            return
        attr_list = ['default_executable', 'default_flags']
        # Set attributes based on environment variables
        for k in attr_list:
            env = getattr(cls, '%s_env' % k, None)
            if env is not None:
                if k in ['default_flags']:
                    old_val = getattr(cls, k)
                    new_val = os.environ.get(env, '').split()
                    for v in new_val:
                        old_val.append(v)
                else:
                    setattr(cls, k, os.environ.get(env, getattr(cls, k)))
        # Set default_executable to name
        if cls.default_executable is None:
            cls.default_executable = cls.name
        # Add executable extension
        if platform._is_win:  # pragma: windows
            if not cls.default_executable.endswith('.exe'):
                cls.default_executable += '.exe'

    @classmethod
    def get_language_ext(cls):
        r"""Get the extensions associated with the language that this tool can
        handle.

        Returns:
            list: Language file extensions.

        """
        if cls._language_ext is None:
            cls._language_ext = []
            for x in cls.languages:
                new_ext = import_component('model', x).language_ext
                if new_ext is not None:
                    cls._language_ext += new_ext
        return cls._language_ext

    @classmethod
    def file2base(cls, fname):
        r"""Determine basename from path.

        Args:
            fname (str): Full or partial path to file.

        Returns:
            str: File name without extension.

        """
        return os.path.splitext(os.path.basename(fname))[0]

    @classmethod
    def append_flags(cls, out, key, value, **kwargs):
        r"""Append one ore more flag(s) to a list of flags based on a key value/set.

        Args:
            out (list): Existing list that the new flag should be appended to.
            key (str): String identifying the type of flag. See create_flag for
                additional details.
            value (object): Value that should be set in the flag. If a list,
                multiple flags are added, one for each item in the list.
            prepend (bool, optional): If True, new flags are prepended to the
                front of the list rather than the end. Defaults to False. This
                keyword argument is ignoerd if position is provided.
            position (int, optional): If not None, this is the position that
                the new elements should be added to the existing flags. Positive
                positions indicate indexes into the existing list of flags.
                Negative are relative to the end of the existing list such that
                -1 is the same as just appending the new flags to the end of the
                list. Defaults to None and prepend takes precedence.
            no_duplicates (bool, optional): If True, the new flags being added
                will be checked against the existing ones to ensure that there
                are not duplicates. If False, the new flags are added
                reguardless of the existing flags. Defaults to False.

        Raises:
            ValueError: If there are unexpected keyword arguments.
            ValueError: If no_duplicates is True and the existing list of flags
                already contains a flag matching the provided flag key.

        """
        # Access class level flag option definitions
        if key in cls.flag_options:
            key = cls.flag_options[key]
        if isinstance(key, dict):
            for k, v in key.items():
                if k != 'key':
                    kwargs.setdefault(k, v)
            key = key['key']
        # Loop over list
        if isinstance(value, list):
            for v in value:
                cls.append_flags(out, key, v, **kwargs)
            return
        # Unpack keyword arguments
        prepend = kwargs.pop('prepend', False)
        position = kwargs.pop('position', None)
        no_duplicates = kwargs.pop('no_duplicates', None)
        if kwargs:  # pragma: debug
            raise ValueError("Unexpected keyword arguments: %s" % kwargs)
        # Create flags and check for duplicates
        new_flags = cls.create_flag(key, value)
        if no_duplicates:
            for o in out:
                if scanf.scanf(key, o):
                    raise ValueError("Flag for key %s already exists: '%s'"
                                     % (key, o))
        # Determine location where flags should be added & add them
        if position is None:
            if prepend:
                position = 0
            else:
                position = -1
        if position == -1:
            out.extend(new_flags)
        elif position < 0:
            for f in new_flags:
                out.insert(position + 1, f)
        else:
            for f in new_flags[::-1]:
                out.insert(position, f)

    @classmethod
    def create_flag(cls, key, value):
        r"""Create a flag from a key/value set.

        Args:
            key (str): String identifying the type of flag. If key contains '%s',
                it is assumed that the flag will be produced by formatting the
                value according to key. If key dosn't contain '%s', it is assumed
                that key indicates that value is the following item and they
                both will be returned. If key is an empty string, then the value
                is assumed to constitute the entire flag.
            value (object): Value that should be set in the flag. If a list,
                multiple flags are returned, one for each item in the list.

        Returns:
            list: Items representing the flag.

        """
        if key in cls.flag_options:
            key = cls.flag_options[key]
        if isinstance(key, dict):
            key = key['key']
        if isinstance(value, list):
            out = []
            for v in value:
                out += cls.create_flag(key, v)
        elif value is None:
            out = []
        elif len(key) == 0:
            out = [value]
        elif '%s' in key:
            out = [key % value]
        elif isinstance(value, bool):
            out = []
            if value:
                out.append(key)
        else:
            out = [key, value]
        return out

    @classmethod
    def is_installed(cls):
        r"""Determine if this tool is installed by looking for the executable.

        Returns:
            bool: True if the tool is installed, False otherwise.

        """
        exec_path = tools.which(cls.get_executable())
        return (exec_path is not None)

    @classmethod
    def get_flags(cls, flags=None, outfile=None, output_first=None,
                  unused_kwargs=None, skip_defaults=False, **kwargs):
        r"""Get a list of flags for the tool.

        Args:
            flags (list, optional): User defined flags that should be included.
                Defaults to empty list.
            outfile (str, optional): If provided, it is appended to the end of
                the flags following the cls.output_key flag to indicate that
                this is the name of the output file. Defaults to None and is
                ignored.
            output_first (bool, optional): If True, output flag(s) will be
                placed at the front of the returned flags. If False, they are
                placed at the end. Defaults to None and is set by
                cls.output_first.
            unused_kwargs (dict, optional): Existing dictionary that unused
                keyword arguments should be added to. Defaults to None and is
                ignored.
            skip_defaults (bool, optional): If True, the default flags will
                not be added. Defaults to False.
            **kwargs: Additional keyword arguments are ignored and added to
                unused_kwargs if provided.

        Returns:
            list: Flags for the tool.

        """
        if flags is None:
            flags = []
        flags = kwargs.pop('%s_flags' % cls.tooltype, flags)
        out = copy.deepcopy(flags)
        if not isinstance(out, list):
            out = [out]
        if output_first is None:
            output_first = cls.output_first
        # Add default & user defined flags
        if not skip_defaults:
            new_flags = cls.default_flags + getattr(cls, 'flags', [])
            for x in new_flags:
                # It is on the user to make sure there are not conflicting flags
                # when an error is thrown
                out.append(x)
        # Add class defined flags
        for k in cls.flag_options.keys():
            if k in kwargs:
                cls.append_flags(out, k, kwargs.pop(k))
        # Add output file
        if (outfile is not None) and (cls.output_key is not None):
            cls.append_flags(out, cls.output_key, outfile,
                             prepend=output_first, no_duplicates=True)
        # Handle unused keyword argumetns
        if isinstance(unused_kwargs, dict):
            unused_kwargs.update(kwargs)
        return out

    @classmethod
    def get_executable(cls):
        r"""Determine the executable that should be used to call this tool.

        Returns:
            str: Name of (or path to) the tool executable.

        """
        out = getattr(cls, 'executable', cls.default_executable)
        if out is None:
            raise NotImplementedError("Executable not set for %s '%s'."
                                      % (cls.tooltype, cls.name))
        return out

    @classmethod
    def get_search_path(cls):
        r"""Determine the paths searched by the tool for external library files.

        Returns:
            list: List of paths that the tools will search.

        """
        if (cls.search_path_flags is None) and (cls.search_path_env is None):
            raise NotImplementedError("get_search_path method not implemented for "
                                      "%s tool '%s'" % (cls.tooltype, cls.name))
        paths = []
        # Get search paths from environment variable
        if cls.search_path_env is not None:
            if not isinstance(cls.search_path_env, list):
                cls.search_path_env = [cls.search_path_env]
            for ienv in cls.search_path_env:
                ienv_paths = os.environ.get(ienv, '').split(os.pathsep)
                print('search_path_env', cls.search_path_env, ienv_paths)
                for x in ienv_paths:
                    if x:
                        paths.append(x)
        # Get search paths from the conda environment
        if (cls.search_path_conda is not None) and ('CONDA_PREFIX' in os.environ):
            prefix = os.environ['CONDA_PREFIX']
            if not isinstance(cls.search_path_conda, list):
                cls.search_path_conda = [cls.search_path_conda]
            for ienv in cls.search_path_conda:
                ienv_path = os.path.join(prefix, ienv)
                if os.path.isdir(ienv_path):
                    paths.append(ienv_path)
        # Get flags based on path
        if cls.search_path_flags is not None:
            print('search_path_flags', cls.search_path_flags)
            output = cls.call(cls.search_path_flags, skip_flags=True,
                              allow_error=True)
            print('output', output)
            # Split on beginning & ending regexes if they exist
            if cls.search_regex_begin is not None:
                output = re.split(cls.search_regex_begin, output)[-1]
            if cls.search_regex_end is not None:
                output = re.split(cls.search_regex_end, output)[0]
            # Search for paths
            for r in cls.search_regex:
                for x in re.findall(r, output):
                    if os.path.isdir(x):
                        paths.append(x)
        print('search paths', paths)
        return paths

    @classmethod
    def get_executable_command(cls, args, skip_flags=False, unused_kwargs=None,
                               **kwargs):
        r"""Determine the command required to run the tool using the specified
        arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool. If
                skip_flags is False, these are treated as input files that will
                be used by the tool.
            skip_flags (bool, optional): If True, args is assumed to include
                any necessary flags. If False, args are assumed to the files
                that the tool is called on and flags are determined from them.
                Defaults to False.
            unused_kwargs (dict, optional): Existing Python dictionary that
                unused keyword arguments will be added to. Defaults to None and
                is initialized to an empty dict.
            **kwargs: Additional keyword arguments are ignored and stored in
                unused_kwargs if provided.

        Returns:
            str: Output to stdout from the command execution.

        """
        library_flags = kwargs.pop('library_flags', [])
        if unused_kwargs is None:
            unused_kwargs = {}
        # Get flags
        if skip_flags:
            flags = []
            library_flags = []
            unused_kwargs.update(kwargs)
        else:
            flags = cls.get_flags(unused_kwargs=unused_kwargs,
                                  skip_library_libs=True,
                                  library_flags=library_flags, **kwargs)
        # Form command
        cmd = flags + args + library_flags
        if (len(cmd) == 0) or (not os.path.splitext(cmd[0])[0].endswith(cls.name)):
            cmd = [cls.get_executable()] + cmd
        # Pop library flags so it is not an unused_kwarg in cases of non-linking
        # compiler command
        for k in ['library_flags', 'skip_library_libs']:
            unused_kwargs.pop(k, [])
        return cmd

    @classmethod
    def call(cls, args, language=None, skip_flags=False, dry_run=False,
             out=None, overwrite=False, products=None, allow_error=False,
             working_dir=None, additional_args=None, **kwargs):
        r"""Call the tool with the provided arguments. If the first argument
        resembles the name of the tool executable, the executable will not be
        added.

        Args:
            args (list): The arguments that should be passed to the tool.
            language (str, optional): Language of tool that should be used. If
                different than the languages supported by the current tool,
                the correct tool is used instead. Defaults to None and is
                ignored.
            skip_flags (bool, optional): If True, args is assumed to include
                any necessary flags. If False, args are assumed to the files
                that the tool is called on and flags are determined from them.
                Defaults to False.
            dry_run (bool, optional): If True, the tool won't be called, but
                the products will be updated. Defautls to False.
            out (str, optional): Full path to output file that should be created.
                If None, the path will be determined from the path to the first
                argument provided. Defaults to None. This keyword argument will
                be ignored if skip_flags is True.
            overwrite (bool, optional): If True, the existing compile file will
                be overwritten. Otherwise, it will be kept and this function
                will return without recompiling the source file.
            products (list, optional): Existing Python list that additional
                products produced by the compilation should be appended to.
                Defaults to None and is ignored.
            allow_error (bool, optional): If True and there is an error when
                call the executable, it will be ignored. If False, errors will
                result in an exception being raised. Defaults to False.
            working_dir (str, optional): Working directory where tool should be
                called from. This will also be used to construct the path for
                the output file. Defaults to None and is ignored.
            additional_args (list, optional): Additional arguments that should
                be appended to args before continuing. Defaults to None and is
                ignored.
            **kwargs: Additional keyword arguments are passed to
                cls.get_executable_command. and tools.popen_nobuffer.

        Returns:
            str: Output to stdout from the command execution if skip_flags is
                True, produced file otherwise.

        Raises:
            RuntimeError: If there is an error when running the command and
                allow_error is False.
        
        """
        # Call from another tool if the language dosn't match
        language = kwargs.pop('%s_language' % cls.tooltype, language)
        if (language is not None) and (language not in cls.languages):
            lang_drv = import_component('model', language)
            lang_cls = lang_drv.get_tool(cls.tooltype)
            return lang_cls.call(args, skip_flags=skip_flags, dry_run=dry_run,
                                 out=out, overwrite=overwrite, products=products,
                                 allow_error=allow_error, working_dir=working_dir,
                                 additional_args=additional_args, **kwargs)
        # Add additional arguments
        if isinstance(args, backwards.string_types):
            args = [args]
        assert(isinstance(args, list))
        if additional_args is not None:
            args = args + additional_args
        # Process arguments only valid if skip_flags is False
        if (not skip_flags):
            if products is None:
                products = []
            # Get output file
            if out is None:
                out = cls.get_output_file(args[0], working_dir=working_dir,
                                          **kwargs)
            elif (((out != 'clean') and (not os.path.isabs(out))
                   and (working_dir is not None))):
                out = os.path.join(working_dir, out)
            assert(out not in args)  # Don't remove source files
            # Check for file
            if overwrite and (not dry_run):
                if os.path.isfile(out):
                    if os.path.splitext(out)[-1] in cls.get_language_ext():
                        raise RuntimeError("Source file will not be overwritten: "
                                           + out)
                    os.remove(out)
                    # raise RuntimeError("Output already exists: %s" % out)
                elif os.path.isdir(out):
                    if not os.listdir(out):
                        os.rmdir(out)
                    else:  # pragma: debug
                        raise RuntimeError("Output directory %s is not empty: %s."
                                           % (out, os.listdir(out)))
            if (not dry_run) and (os.path.isfile(out) or os.path.isdir(out)):
                products.append(out)
                return out
            kwargs['outfile'] = out
        # Get command
        unused_kwargs = kwargs.pop('unused_kwargs', {})
        cmd = cls.get_executable_command(args, skip_flags=skip_flags,
                                         unused_kwargs=unused_kwargs,
                                         cwd=working_dir, **kwargs)
        # Return if dry run, adding potential output to product
        if dry_run:
            if skip_flags:
                return ''
            else:
                if out != 'clean':
                    products.append(out)
                return out
        # Run command
        output = ''
        try:
            proc = tools.popen_nobuffer(cmd, **unused_kwargs)
            output, err = proc.communicate()
            if (proc.returncode != 0) and (not allow_error):
                logging.error(output)
                raise RuntimeError("Command '%s' failed with code %d."
                                   % (' '.join(cmd), proc.returncode))
            output = backwards.as_str(output)
            logging.debug('%s\n%s' % (' '.join(cmd), output))
        except (subprocess.CalledProcessError, OSError) as e:
            if not allow_error:
                raise RuntimeError("Could not call command '%s': %s"
                                   % (' '.join(cmd), e))
        # Check for output
        if (not skip_flags):
            if (out != 'clean'):
                if not (os.path.isfile(out)
                        or os.path.isdir(out)):  # pragma: debug
                    logging.error('%s\n%s' % (' '.join(cmd), output))
                    raise RuntimeError(("%s tool, %s, failed to produce "
                                        "result '%s'")
                                       % (cls.tooltype.title(), cls.name, out))
                logging.debug("%s %s produced %s"
                              % (cls.tooltype.title(), cls.name, out))
                products.append(out)
            return out
        return output


class CompilerBase(CompilationToolBase):
    r"""Base class for compilers.

    Args:
        linker (str, optional): Name of the linker that should be used for
            linking compiled objects. Defaults to None if not provided and
            default_linker will be used.
        archiver (str, optional): Name of the archiver that should be used for
            combining compiled objects into a static library. Defaults to None
            if not provided and default_archiver will be used.

    Attributes:
        compile_only_flag (str): Flag that should prepended to compiler/linker
            combination tool arguments to indicate that only compilation should
            be performed.
        default_linker (str): Name of linker that should be used after compiling
            with this compiler. If not set, it is assumed that this compiler is
            also a linker.
        linker_switch (str): Flag to indicate beginning of flags that should be
            passed to the linker from a call to a compiler/linker combination
            tools (e.g. /link on Windows).
        object_ext (str): Extension that should be used for object files.
        is_linker (bool): If True, the tool also serves as a linker and a
            separate linker class will be automatically generating from the
            linker_attributes dictionary. This will be set to True if
            no_separate_linking is True.
        no_separate_linking (bool): If True, the tool severs as linker but
            cannot be called for just compilation or linking alone.
        linker_attributes (dict): Attributes that should be added to the linker
            class created for this tool if is_linker is True.
        linker_base_classes (tuple): Base classes that should be used to create
            the default linker from the compiler tool. If None, (LinkerBase, )
            is used if no_separate_linking is False and (DummyLinkerBase, )
            is used if no_separate_linking is True.
        combine_with_linker (bool): If True, the compiler and linker flags can
            be combined and passed to the compiler executable to perform both
            operations in succession. If False, the compilation and linking
            steps must be performed separately. If None, this is determined by
            checking if the compiler and linker names match.

    """
    tooltype = 'compiler'
    flag_options = OrderedDict([('definitions', '-D%s'),
                                ('include_dirs', '-I%s')])
    compile_only_flag = '-c'
    default_linker = None
    default_archiver = None
    default_linker_flags = None
    default_archiver_flags = None
    linker_switch = None
    object_ext = '.o'
    is_linker = True  # Most compiler's also perform linking
    no_separate_linking = False
    linker_attributes = {}
    linker_base_classes = None
    combine_with_linker = None
    search_path_conda = 'include'

    def __init__(self, linker=None, archiver=None, linker_flags=None,
                 archiver_flags=None, **kwargs):
        for k in ['linker', 'archiver', 'linker_flags', 'archiver_flags']:
            v = kwargs.pop(k, None)
            if v is not None:
                setattr(self, '_%s' % k, v)
        super(CompilerBase, self).__init__(**kwargs)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilationToolBase.before_registration(cls)
        if cls.name is None:
            return
        if platform._is_win:  # pragma: windows
            cls.object_ext = '.obj'
        if cls.no_separate_linking:
            cls.is_linker = True
            cls.compile_only_flag = None
        if cls.is_linker:
            if cls.default_linker is None:
                cls.default_linker = cls.name
            copy_attr = ['name', 'aliases', 'languages', 'platforms',
                         'default_executable', 'default_executable_env']
            linker_name = '%sLinker' % cls.__name__.split('Compiler')[0]
            linker_attr = copy.deepcopy(cls.linker_attributes)
            for k in copy_attr:
                linker_attr.setdefault(k, getattr(cls, k))
            linker_base_cls = cls.linker_base_classes
            if linker_base_cls is None:
                if cls.no_separate_linking:
                    linker_base_cls = (DummyLinkerBase, )
                else:
                    linker_base_cls = (LinkerBase, )
            linker_cls = type(linker_name, linker_base_cls, linker_attr)
            globals()[linker_cls.__name__] = linker_cls
            del linker_cls
        if cls.combine_with_linker is None:
            cls.combine_with_linker = (cls.name == cls.default_linker)

    @classmethod
    def linker(cls):
        r"""Get the associated linker class.

        Returns:
            CompilationToolBase: Linker class associated with this compiler.

        """
        linker = getattr(cls, '_linker', cls.default_linker)
        linker_flags = getattr(cls, '_linker_flags', cls.default_linker_flags)
        if linker is None:
            linker = find_compilation_tool('linker', cls.languages[0])
        if linker:
            out = get_compilation_tool('linker', linker)(flags=linker_flags,
                                                         executable=linker)
        else:
            out = linker
        return out

    @classmethod
    def archiver(cls):
        r"""Get the associated archiver class.

        Returns:
            ArchiverToolBase: Archiver class associated with this compiler.

        """
        archiver = getattr(cls, '_archiver', cls.default_archiver)
        archiver_flags = getattr(cls, '_archiver_flags', cls.default_archiver_flags)
        if archiver is None:
            archiver = find_compilation_tool('archiver', cls.languages[0])
        if archiver:
            out = get_compilation_tool('archiver', archiver)(flags=archiver_flags,
                                                             executable=archiver)
        else:
            out = archiver
        return out

    @classmethod
    def get_library_tool(cls, build_library=None, libtype=None, **kwargs):
        r"""Determine the tool that should be used based on the provided
        arguments.

        Args:
            build_library (bool, optional): If True, the linker/archiver for
                building the library type specified by libtype will be returned.
                If False, the linker will be returned for creating an executable.
                Defaults to None and is only set to True if libtype is 'static'
                or 'shared'.
            libtype (str, optional): Library type that should be created by the
                linker/archiver. If 'static', the archiver is returned. If
                'shared' or any other value, the linker is returned. Defaults to
                None and is set to _default_libtype if build_library is True.

        Returns:
            CompilationToolBase: Linker/archiver that should be used.

        """
        if build_library is None:
            if libtype in ['static', 'shared']:
                build_library = True
            else:
                build_library = False
        if (libtype is None) and build_library:
            libtype = _default_libtype
        if libtype == 'static':
            tool = cls.archiver()
        else:
            tool = cls.linker()
        return tool

    @classmethod
    def get_flags(cls, dont_link=None, add_linker_switch=False,
                  libtype=None, logging_level=None, **kwargs):
        r"""Get a list of compiler flags.

        Args:
            dont_link (bool, optional): If True, the command will result in a
                linkable object file rather than an executable or library.
                Defaults to True if cls.no_separate_linking is True or libtype
                is 'object' and False otherwise.
            add_linker_switch (bool, optional): If True, the linker_switch flag
                will be added to the flags even if dont_link is True as long
                as the flag is not None. Defaults to False.
            libtype (str, optional): Library type that should be created by the
                linker/archiver. Defaults to None.
            logging_level (int, optional): Logging level that should be passed
                as a definition to the C compiler. Defaults to None and will be
                ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and get_linker_flags if dont_link is False.

        Returns:
            list: Compiler flags.

        Raises:
            ValueError: If dont_link is False and cls.combine_with_linker is
                False.

        """
        # Turn off linking if it is part of the compilation call
        if cls.no_separate_linking:
            dont_link = True
        # Set dont_link based on libtype
        if dont_link is None:
            if libtype == 'object':
                dont_link = True
            else:
                dont_link = False
        # Add logging level as a definition
        if logging_level is not None:
            kwargs.setdefault('definitions', [])
            kwargs['definitions'].append('YGG_DEBUG=%d' % logging_level)
        # Call parent class
        outfile_link = None
        if not dont_link:  # pragma: debug
            outfile_link = kwargs.pop('outfile', None)
        out = super(CompilerBase, cls).get_flags(**kwargs)
        # Add flags for compilation only or provided output file
        if ((dont_link and (cls.compile_only_flag is not None)
             and (not kwargs.get('skip_defaults', False)))):
            if cls.compile_only_flag not in out:
                out.insert(0, cls.compile_only_flag)
        # Add linker switch
        if (not dont_link) or add_linker_switch:  # pragma: debug
            if cls.linker_switch is not None:  # pragma: windows
                if cls.linker_switch not in out:
                    out.append(cls.linker_switch)
        # Add linker flags
        if (not dont_link):  # pragma: debug
            if (not cls.combine_with_linker):
                raise ValueError("Cannot combine linker and compiler flags.")
            warnings.warn('The returned flags will contain linker flags that '
                          'may need to follow the list of source files.')
            unused_kwargs_comp = kwargs.pop('unused_kwargs', {})
            unused_kwargs_link = {}
            tool = cls.get_library_tool(libtype=libtype, **unused_kwargs_comp)
            out += tool.get_flags(outfile=outfile_link,
                                  unused_kwargs=unused_kwargs_link,
                                  **unused_kwargs_comp)
            for k in copy.deepcopy(list(unused_kwargs_comp.keys())):
                if k not in unused_kwargs_link:
                    del unused_kwargs_comp[k]
        return out

    @classmethod
    def get_output_file(cls, src, dont_link=False, working_dir=None,
                        libtype=None, no_src_ext=False, **kwargs):
        r"""Determine the appropriate output file that will result when
        compiling a given source file.

        Args:
            src (str): Source file being compiled that name base will be taken
                from.
            dont_link (bool, optional): If True, the result assumes that the
                source is just compiled and not linked. If False, the result
                will be the final result after linking. Defaults to None and
                will be set to True if libtype is 'object' and False otherwise.
            working_dir (str, optional): Working directory where output file
                should be located. Defaults to None and is ignored.
            no_src_ext (bool, optional): If True, the source extension will not
                be added to the object file name. Defaults to False. Ignored if
                dont_link is False.
            libtype (str, optional): Library type that should be created by the
                linker/archiver. Defaults to None.
            **kwargs: Additional keyword arguments are ignored unless dont_link
                is False; then they are passed to the linker's get_output_file
                method.

        Returns:
            str: Full path to file that will be produced.

        """
        # Set dont_link based on libtype
        if dont_link is None:
            if libtype == 'object':
                dont_link = True
            else:
                dont_link = False
        # Get intermediate file
        if cls.no_separate_linking:
            obj = src
        else:
            if isinstance(src, list):
                obj = []
                for isrc in src:
                    obj.append(cls.get_output_file(dont_link=True,
                                                   working_dir=working_dir,
                                                   no_src_ext=no_src_ext,
                                                   libtype=libtype, **kwargs))
            else:
                src_base, src_ext = os.path.splitext(src)
                if no_src_ext or src_base.endswith('_%s' % src_ext[1:]):
                    obj = '%s%s' % (src_base, cls.object_ext)
                else:
                    obj = '%s_%s%s' % (src_base, src_ext[1:], cls.object_ext)
                if (not os.path.isabs(obj)) and (working_dir is not None):
                    obj = os.path.normpath(os.path.join(working_dir, obj))
        # Pass to linker unless dont_link is True
        if dont_link and (not cls.no_separate_linking):
            out = obj
        else:
            tool = cls.get_library_tool(libtype=libtype, **kwargs)
            out = tool.get_output_file(obj, working_dir=working_dir, **kwargs)
        return out

    @classmethod
    def call(cls, args, dont_link=None, skip_flags=False, out=None,
             libtype=None, additional_objs=None, **kwargs):
        r"""Call the tool with the provided arguments. If the first argument
        resembles the name of the tool executable, the executable will not be
        added.

        Args:
            args (list): The arguments that should be passed to the tool.
            dont_link (bool, optional): If True, the command will result in a
                linkable object file rather than an executable or library.
                Defaults to True if cls.no_separate_linking is True or libtype
                is 'object' and False otherwise.
            skip_flags (bool, optional): If True, args is assumed to include
                any necessary flags. If False, args are assumed to the files
                that the tool is called on and flags are determined from them.
                Defaults to False.
            out (str, optional): Full path to output file that should be created.
                If None, the path will be determined from the path to the first
                arguments provided. Defaults to None. This keyword argument will
                be ignored if skip_flags is True.
            libtype (str, optional): Library type that should be created by the
                linker/archiver. Defaults to None.
            additional_objs (list, optional): Additional linkable object files
                that should be supplied to the linker/archiver if dont_link is
                False. Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and the associated linker/archiver's call method
                if dont_link is False.

        Returns:
            str: Output to stdout from the command execution if skip_flags is
                True, produced file otherwise.

        """
        # Turn off linking if it is part of the compilation call
        if cls.no_separate_linking:
            dont_link = True
        # Set dont_link based on libtype
        if dont_link is None:
            if libtype == 'object':
                dont_link = True
            else:
                dont_link = False
        # Get appropriate tool
        tool = cls.get_library_tool(libtype=libtype, **kwargs)
        # Handle list of sources
        if (not skip_flags) and isinstance(args, list) and (len(args) > 1):
            if dont_link:
                out_comp = out
            else:
                out_comp = None
            if out_comp is None:
                out_comp = [None for _ in args]
            elif not isinstance(out_comp, list):
                out_comp = [out_comp]
            if len(args) != len(out_comp):
                raise ValueError("Cannot compile %d sources into %d objects."
                                 % (len(args), len(out_comp)))
            # Compile each source
            kwargs_link = {}
            if not dont_link:
                kwargs_link = tool.extract_kwargs(kwargs)
            obj_list = []
            for isrc, iout in zip(args, out_comp):
                iobj = cls.call(isrc, out=iout, dont_link=True, **kwargs)
                obj_list.append(iobj)
            if dont_link:
                return obj_list
            # Link/archive
            return tool.call(obj_list, out=out, additional_args=additional_objs,
                             **kwargs_link)
        # Call without linking/archiving
        if skip_flags or dont_link:
            if not skip_flags:
                kwargs['dont_link'] = dont_link
            return super(CompilerBase, cls).call(args, skip_flags=skip_flags,
                                                 out=out, **kwargs)
        else:
            kwargs_link = tool.extract_kwargs(kwargs)
            out_comp = super(CompilerBase, cls).call(args, dont_link=True,
                                                     out=None, **kwargs)
            return tool.call(out_comp, out=out, additional_args=additional_objs,
                             **kwargs_link)

        
class LinkerBase(CompilationToolBase):
    r"""Base class for linkers.

    Attributes:
        shared_library_flag (str): Flag that should be prepended to the linker
            tool arguments to indicate that a shared/dynamic library should be
            produced instead of an executable.
        library_name_key (str): Option key indicating the name of a library
            that should be linked against.
        library_directory_key (str): Option key indicating a directory that
            should be included in the linker search path for libraries.
        library_prefix (str): Prefix that should be added to library paths.
        library_ext (str): Extension that should be used for shared libraries.
        executable_ext (str): Extension that should be used for executables.
        output_first_library (bool): If True, the output key (and its value) are
            put in front of the other flags when building a library. A value of
            None causes the output_first attribute to be used (unless explicitly
            set in the method call).

    """

    tooltype = 'linker'
    flag_options = OrderedDict([('library_libs', '-l%s'),
                                ('library_dirs', '-L%s')])
    shared_library_flag = '-shared'
    library_prefix = 'lib'
    library_ext = None  # depends on the OS
    executable_ext = '.out'
    output_first_library = None
    search_path_conda = 'lib'

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilationToolBase.before_registration(cls)
        if cls.name is None:
            return
        if platform._is_win:  # pragma: windows
            # TODO: Use 'cyg' prefix on cygwin?
            cls.library_prefix = ''
            cls.library_ext = '.dll'
            cls.executable_ext = '.exe'
        elif platform._is_mac:
            # TODO: Dynamic library by default on windows?
            # cls.shared_library_flag = '-dynamiclib'
            cls.library_ext = '.dylib'
        else:
            cls.library_ext = '.so'

    @classmethod
    def libpath2libname(cls, libpath):
        r"""Determine the library name from the library path.

        Args:
            libpath (str): Full or partial path to library.
        
        Returns:
            str: Library name.

        """
        if platform._is_win:  # pragma: windows
            libname = os.path.basename(libpath)
        else:
            libname = cls.file2base(libpath)
        if cls.library_prefix:
            libname = libname.split(cls.library_prefix)[-1]
        return libname

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
        kws_link = ['build_library', 'skip_library_libs', 'use_library_path',
                    '%s_flags' % cls.tooltype, '%s_language' % cls.tooltype,
                    'libraries', 'library_dirs', 'library_libs', 'library_flags']
        kws_both = ['overwrite', 'products', 'allow_error', 'dry_run']
        kwargs_link = {}
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
    def get_flags(cls, build_library=False, skip_library_libs=False,
                  use_library_path=False, **kwargs):
        r"""Get a list of linker flags.

        Args:
            libraries (list, optional): Full paths to libraries that should be
                linked against. Defaults to an empty list.
            library_dirs (list, optional): Directories that should be searched
                for libraries. Defaults to an empty list.
            library_libs (list, optional): Names of libraries that should be
                linked against. Defaults to an empty list.
            library_flags (list, optional): Existing list that library flags
                should be appended to instead of the returned flags if
                skip_library_libs is True. Defaults to [].
            build_library (bool, optional): If True, a shared library is built.
                If False, an executable is created. Defaults to False.
            skip_library_libs (bool, optional): If True, the library_libs will
                not be added to the returned flags. Instead, any additional
                required library flags will be appended to the provided
                library_flags list which should then be added to the compilation
                command by the user in the appropriate location. Defaults to
                False.
            use_library_path (bool, optional): If True, the included libraries
                will be added to the output list as complete paths rather than
                as separate flags for library and library search directory.
                Defaults to False.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Linker flags.

        """
        # Add output_first keyword argument for libraries
        if build_library:
            kwargs.setdefault('output_first', cls.output_first_library)
        # Copy/Pop so that empty default dosn't get appended to and then
        # call the parent class's method
        libraries = kwargs.pop('libraries', [])
        library_dirs = kwargs.pop('library_dirs', [])
        library_libs = kwargs.pop('library_libs', [])
        library_flags = kwargs.pop('library_flags', [])
        flags = copy.deepcopy(kwargs.pop('flags', []))
        # Get list of libraries
        for x in libraries:
            if use_library_path:
                if skip_library_libs:
                    library_flags.append(x)
                else:
                    flags.append(x)
            else:
                x_d, x_f = os.path.split(x)
                library_dirs.append(x_d)
                library_libs.append(cls.libpath2libname(x_f))
        # Add libraries to library_flags instead of flags so they can be
        # used elsewhere
        if skip_library_libs and library_libs:
            cls.append_flags(library_flags, cls.flag_options['library_libs'],
                             library_libs)
            library_libs = []
        # Call parent class
        if library_dirs:
            kwargs['library_dirs'] = library_dirs
        if library_libs:
            kwargs['library_libs'] = library_libs
        out = super(LinkerBase, cls).get_flags(flags=flags, **kwargs)
        # Add flag specifying the shared library
        if build_library and (cls.shared_library_flag is not None):
            out.insert(0, cls.shared_library_flag)
        return out
    
    @classmethod
    def get_output_file(cls, obj, build_library=False, working_dir=None, **kwargs):
        r"""Determine the appropriate output file that will result when linking
        a given object file.

        Args:
            obj (str): Object file being linked that name base will be taken
                from.
            build_library (bool, optional): If True, a shared library path is
                returned. If False, an executable file name is returned.
                Defaults to False.
            working_dir (str, optional): Working directory where output file
                should be located. Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            str: Full path to file that will be produced.

        """
        if isinstance(obj, list):
            return [cls.get_output_file(obj[0], build_library=build_library,
                                        working_dir=working_dir, **kwargs)]
        if build_library:
            prefix = cls.library_prefix
            out_ext = cls.library_ext
        else:
            prefix = ''
            out_ext = cls.executable_ext
        obj_dir, obj_base = os.path.split(obj)
        out = os.path.join(obj_dir,
                           prefix + os.path.splitext(obj_base)[0] + out_ext)
        if (not os.path.isabs(out)) and (working_dir is not None):
            out = os.path.normpath(os.path.join(working_dir, out))
        return out
    
    
class ArchiverBase(LinkerBase):
    r"""Base class for archivers.

    Attributes:
        static_library_flag (str): Flag that should be prepended to the archiver
            tool arguments to indicated that a static library should be produced.
        library_name_key (str): Option key indicating the name of a library
            that should be linked against.
        library_directory_key (str): Option key indicating a directory that
            should be included in the linker search path for libraries.
        library_prefix (str): Prefix that should be added to library paths.
        library_ext (str): Extension that should be used for static libraries.

    """

    tooltype = 'archiver'
    flag_options = OrderedDict()
    static_library_flag = '-static'
    library_ext = None  # depends on the OS

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        LinkerBase.before_registration(cls)
        if cls.name is None:
            return
        # Delete attributes that are linker specific
        for k in ['shared_library_flag']:
            setattr(cls, k, None)
        if platform._is_win:  # pragma: windows
            cls.library_ext = '.lib'
        else:
            cls.library_ext = '.a'

    @classmethod
    def get_flags(cls, **kwargs):
        r"""Get a list of flags for this archiver tool.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Archiver flags.

        """
        # Call super class of parent class which handles defaults and user
        # defined options without adding any library info
        cls.extract_kwargs(kwargs)
        out = super(LinkerBase, cls).get_flags(**kwargs)
        # Add flag specifying the static library
        if cls.static_library_flag is not None:
            out.insert(0, cls.static_library_flag)
        return out

    @classmethod
    def get_output_file(cls, obj, **kwargs):
        r"""Determine the appropriate output file that will result when linking
        a given object file.

        Args:
            obj (str): Object file being linked that name base will be taken
                from.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            str: Full path to file that will be produced.

        """
        kwargs['build_library'] = True
        return super(ArchiverBase, cls).get_output_file(obj, **kwargs)
    

class DummyLinkerBase(LinkerBase):
    r"""Base class for a dummy linker in the case that the linking step cannot
    be split into a separate call."""

    name = 'dummy'

    @classmethod
    def get_flags(cls, **kwargs):
        r"""Raises an error to ward off getting flags for the dummy linker."""
        raise RuntimeError("DummyLinker")

    @classmethod
    def call(cls, *args, **kwargs):
        r"""Raises an error to ward off calling the dummy linker."""
        raise RuntimeError("DummyLinker")
        

class CompiledModelDriver(ModelDriver):
    r"""Base class for models written in compiled languages.

    Args:
        name (str): Driver name.
        args (str or list): The model executable and any arguments that should
            be passed to the model executable.
        source_files (list, optional): Source files that should be compiled
            into an executable. Defaults to an empty list and the driver will
            search for a source file based on the model executable (the first
            model argument).
        compiler (str, optional): Command or path to executable that should be
            used to compile the model. If not provided, the compiler will be
            determined based on configuration options for the language (if
            present) and the registered compilers that are available on the
            current operating system.
        compiler_flags (list, optional): Flags that should be passed to the
            compiler during compilation. If nto provided, the compiler flags
            will be determined based on configuration options for the language
            (if present), the compiler defaults, and the default_compiler_flags
            class attribute.
        linker (str, optional): Command or path to executable that should be
            used to link the model. If not provided, the linker will be
            determined based on configuration options for the language (if
            present) and the registered linkers that are available on the
            current operating system
        linker_flags (list, optional): Flags that should be passed to the
            linker during compilation. If nto provided, the linker flags
            will be determined based on configuration options for the language
            (if present), the linker defaults, and the default_linker_flags
            class attribute.
        **kwargs: Additional keyword arguments are passed to parent class.

    Class Attributes:
        default_compiler (str): Name of compiler that will be used if not
            set explictly by instance or config file.
        default_compiler_flags (list): Flags that should be passed to the
            compiler by default for this language.
        default_linker (str): Name of linker that will be used if not
            set explictly by instance or config file
        default_linker_flags (list): Flags that should be passed to the
            linker by default for this language.

    Attributes:
        source_files (list): Source files.
        compiler (str): Name or path to the compiler that should be used.
        compiler_flags (list): Compiler flags.
        linker (str): Name or path to the linker that should be used.
        linker_flags (list): Linker flags.
        compiler_tool (CompilerBase): Compiler tool that will be used.
        linker_tool (LinkerBase): Linker tool that will be used.

    """

    _schema_properties = {
        'source_files': {'type': 'array', 'items': {'type': 'string'},
                         'default': []},
        'compiler': {'type': 'string'},
        'compiler_flags': {'type': 'array', 'items': {'type': 'string'},
                           'default': []},
        'linker': {'type': 'string'},
        'linker_flags': {'type': 'array', 'items': {'type': 'string'},
                         'default': []}}
    executable_type = 'compiler'
    default_compiler = None
    default_compiler_flags = None
    default_linker = None
    default_linker_flags = None
    default_archiver = None
    default_archiver_flags = None

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('overwrite', (not kwargs.pop('preserve_cache', False)))
        super(CompiledModelDriver, self).__init__(name, args, **kwargs)
        # Set defaults from attributes
        for k0 in ['compiler', 'linker', 'archiver']:
            for k in [k0, '%s_flags' % k0]:
                v = getattr(self, k, None)
                if v is None:
                    setattr(self, k, getattr(self, 'default_%s' % k))
        # Set tools so that they are cached
        for k in ['compiler', 'linker', 'archiver']:
            setattr(self, '%s_tool' % k, self.get_tool(k))
        # Compile
        try:
            self.compile_dependencies()
            self.compile_model()
            self.products.append(self.model_file)
        except BaseException:
            self.remove_products()
            raise
        assert(os.path.isfile(self.model_file))
        self.debug("Compiled %s", self.model_file)

    def parse_arguments(self, args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        super(CompiledModelDriver, self).parse_arguments(args, **kwargs)
        # Handle case where provided argument is source and not executable
        # and case where provided argument is executable, but source files are
        # not specified
        model_ext = os.path.splitext(self.model_file)[-1]
        model_is_source = False
        if (self.language_ext is not None) and (len(model_ext) > 0):
            if (model_ext in self.language_ext):
                model_is_source = True
                if len(self.source_files) == 0:
                    self.source_files.append(self.model_file)
            else:
                # Assert that model file is not source code in any of the
                # registered languages
                from yggdrasil.components import import_component
                from yggdrasil.schema import get_schema
                s = get_schema()['model']
                for v_name in s.classes:
                    v = import_component('model', v_name)
                    if (((v.language_ext is not None)
                         and (model_ext in v.language_ext))):  # pragma: debug
                        raise RuntimeError(("Extension '%s' indicates that the "
                                            "model language is '%s', not '%s' "
                                            "as specified.")
                                           % (model_ext, v.language,
                                              self.language))
        elif (len(self.source_files) == 0) and (self.language_ext is not None):
            self.source_files.append(os.path.splitext(self.model_file)[0]
                                     + self.language_ext[0])
        # Add intermediate files and executable by doing a dry run
        kwargs = dict(products=[], dry_run=True)
        if model_is_source:
            kwargs['out'] = None
        out = self.compile_model(**kwargs)
        if model_is_source:
            self.info('Determined model file: %s', out)
            self.model_file = out
        for x in kwargs['products']:
            if self.language_ext is not None:
                x_ext = os.path.splitext(x)[-1]
                if x_ext in self.language_ext:
                    raise Exception("Product is source file: '%s'" % x)
            if x not in self.products:
                self.products.append(x)
        if self.language_ext is not None:
            assert(os.path.splitext(self.model_file)[-1] not in self.language_ext)
        self.debug("source_files: %s", str(self.source_files))
        self.debug("model_file: %s", self.model_file)
        
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        ModelDriver.before_registration(cls)
        if cls.language is not None:
            compiler = None
            for k in ['compiler', 'linker', 'archiver']:
                # Set attribute defaults based on config options
                for k0 in [k, '%s_flags' % k]:
                    ka = 'default_%s' % k0
                    if k0.endswith('_flags'):
                        old_val = getattr(cls, ka)
                        new_val = ygg_cfg.get(cls.language, k0, '').split()
                        for v in new_val:
                            old_val.append(v)
                    else:
                        setattr(cls, ka, ygg_cfg.get(cls.language, k0,
                                                     getattr(cls, ka)))
                # Set default linker/archiver based on compiler
                default_tool_name = getattr(cls, 'default_%s' % k, None)
                if (((default_tool_name is None) and (compiler is not None)
                     and (k in ['linker', 'archiver']))):
                    default_tool_name = getattr(compiler, 'default_%s' % k, None)
                # Check default tool to make sure it is installed
                if default_tool_name:
                    default_tool = get_compilation_tool(k, default_tool_name)
                    if not default_tool.is_installed():
                        warnings.warn(('Default %s for %s (%s) not installed. '
                                       'Attempting to locate an alternative .')
                                      % (k, cls.language, default_tool_name))
                        default_tool_name = None
                # Determine compilation tools based on language/platform
                if default_tool_name is None:
                    default_tool_name = find_compilation_tool(k, cls.language,
                                                              allow_failure=True)
                # Set default tool attribute & record compiler tool if set
                setattr(cls, 'default_%s' % k, default_tool_name)
                if (default_tool_name is not None) and (k == 'compiler'):
                    compiler = get_compilation_tool(k, default_tool_name)

    def model_command(self):
        r"""Return the command that should be used to run the model.

        Returns:
            list: Any commands/arguments needed to run the model from the
                command line.

        """
        if platform._is_win:  # pragma: windows
            model_exec = os.path.splitext(self.model_file)[0]
        else:
            model_exec = os.path.join(".", self.model_file)
        return [model_exec] + self.model_args

    @classmethod
    def get_available_tools(cls, tooltype):
        r"""Return the registry of compilation tools for this language.

        Args:
            tooltype (str): Name of tool type that should be returned. Values
                include 'compiler', 'linker', or 'archiver'.

        Returns:
            dict: Registry of tools for this language.

        """
        reg = get_compilation_tool_registry(tooltype).get('by_language', {})
        return copy.deepcopy(reg.get(cls.language, {}))

    @classmethod
    def get_tool(cls, tooltype, return_prop='tool'):
        r"""Get the class associated with the specified compilation tool for
        this language.

        Args:
            tooltype (str): Type of compilation tool that should be returned.
            return_prop (str, optional): Value that should be returned. If
                'tool', the tool is returned. If 'name', the tool name is
                returned. If 'flags', the tool flags are returned. Defaults to
                'tool'.

        Returns:
            CompilationToolBase: Class providing an interface to the specified
                compilation tool.

        Raises:
            NotImplementedError: If a tool is not specified.
            ValueError: If return_prop is not 'tool', 'name', or 'flags'.

        """
        out = getattr(cls, '%s_tool' % tooltype, None)
        if out is None:
            # Associate linker & archiver with compiler so that it can be
            # used to retrieve them
            if (tooltype == 'compiler') or (return_prop in ['name', 'flags']):
                # Get tool name
                toolname = getattr(cls, tooltype,
                                   getattr(cls, 'default_%s' % tooltype, None))
                if toolname is None:
                    raise NotImplementedError("%s not set for language '%s'."
                                              % (tooltype.title(), cls.language))
                if return_prop == 'name':
                    return toolname
                # Get flags
                tool_flags = getattr(cls, '%s_flags' % tooltype,
                                     getattr(cls, 'default_%s_flags' % tooltype, None))
                if return_prop == 'flags':
                    return tool_flags
                # Get tool
                kwargs = {'executable': toolname, 'flags': tool_flags}
                if tooltype == 'compiler':
                    kwargs.update(
                        linker=cls.get_tool('linker', return_prop='name'),
                        linker_flags=cls.get_tool('linker', return_prop='flags'),
                        archiver=cls.get_tool('archiver', return_prop='name'),
                        archiver_flags=cls.get_tool('archiver', return_prop='flags'))
                out = get_compilation_tool(tooltype, toolname)(**kwargs)
            else:
                out = getattr(cls.get_tool('compiler'), tooltype)()
        # Return correct property given the tool
        if return_prop == 'tool':
            return out
        elif return_prop == 'name':
            return out.name
        elif return_prop == 'flags':
            return out.flags
        else:
            raise ValueError("Invalid return_prop: '%s'" % return_prop)

    @classmethod
    def get_dependency_source(cls, dep, default=None):
        r"""Get the path to the library source files (or header files) for a
        dependency.
        
        Args:
            dep (str): Name of internal or external dependency or full path
                to the library.
            default (str, optional): Default that should be used if a value
                cannot be determined form internal/external dependencies or
                if dep is not a valid file. Defaults to None and is ignored.

        Returns:
            str: Full path to the library source file. For header only libraries
                this will be the header location.

        """
        if dep in cls.internal_libraries:
            dep_info = cls.internal_libraries[dep]
            out = dep_info.get('source', None)
            out_dir = dep_info.get('directory', None)
            if out is None:
                dep_lang = dep_info.get('language', cls.language)
                if dep_lang == cls.language:
                    dep_drv = cls
                else:
                    dep_drv = import_component('model', dep_lang)
                out = dep + dep_drv.language_ext[0]
            if (((out is not None) and (out_dir is not None)
                 and (not os.path.isabs(out)))):
                out = os.path.join(out_dir, out)
        elif dep in cls.external_libraries:
            dep_lang = cls.external_libraries[dep].get('language', cls.language)
            out = ygg_cfg.get(dep_lang, '%s_%s' % (dep, 'include'), None)
        elif os.path.isfile(dep):
            out = dep
        if out is None:
            if default is None:
                raise ValueError("Could not determine source location for "
                                 "dependency '%s'" % dep)
            else:
                out = default
        return out

    @classmethod
    def get_dependency_library(cls, dep, default=None, libtype=None):
        r"""Get the library location for a dependency.

        Args:
            dep (str): Name of internal or external dependency or full path
                to the library.
            default (str, optional): Default that should be used if a value
                cannot be determined form internal/external dependencies or
                if dep is not a valid file. Defaults to None and is ignored.
            libtype (str, optional): Library type that should be returned.
                Valid values are 'static' and 'shared'. Defaults to None and
                will be set on the dependency's libtype (if it has one) or
                the _default_libtype parameter (if it doesn't).

        Returns:
            str: Full path to the library file. For header only libraries,
                an empty string will be returned.

        Raises:
            ValueError: If libtype is not 'static' or 'shared'.
            ValueError: If the path to the library cannot be determined for the
                specified dependency and default is None.

        """
        libclass = None
        libinfo = {}
        if dep in cls.internal_libraries:
            libclass = 'internal'
            libinfo = cls.internal_libraries[dep]
        elif dep in cls.external_libraries:
            libclass = 'external'
            libinfo = cls.external_libraries[dep]
        # Get default libtype and return if header_only library
        if libtype is None:
            libtype = libinfo.get('libtype', _default_libtype)
        if libinfo.get('libtype', None) in ['header_only', 'object']:
            return ''
        # Check that libtype is valid
        libtype_list = ['static', 'shared']
        if libtype not in libtype_list:
            raise ValueError("libtype must be one of %s" % libtype_list)
        # Determine output
        out = None
        if libclass == 'external':
            dep_lang = libinfo.get('language', cls.language)
            if libtype in libinfo:
                out = ygg_cfg.get(dep_lang, '%s_%s' % (dep, libtype), None)
            else:
                libtype_found = []
                for k in libtype_list:
                    if ygg_cfg.has_option(dep_lang, '%s_%s' % (dep, k)):
                        libtype_found.append(k)
                if len(libtype_found) > 0:
                    raise ValueError(("A '%s' library could not be located for "
                                      "dependency '%s', but one or more "
                                      "libraries of types %s were found.")
                                     % (libtype, dep, libtype_found))
        elif libclass == 'internal':
            tool = cls.get_tool('compiler')
            src = cls.get_dependency_source(dep)
            out = tool.get_output_file(dep, libtype=libtype, no_src_ext=True,
                                       build_library=True,
                                       working_dir=os.path.dirname(src))
        elif os.path.isfile(dep):
            out = dep
        if out is None:
            if default is None:
                raise ValueError("Could not determine library path for "
                                 "dependency '%s'" % dep)
            else:
                out = default
        return out

    @classmethod
    def get_dependency_include_dirs(cls, dep, default=None):
        r"""Get the include directories for a dependency.

        Args:
            dep (str): Name of internal or external dependency or full path
                to the library.
            default (str, optional): Default that should be used if a value
                cannot be determined form internal/external dependencies or
                if dep is not a valid file. Defaults to None and is ignored.

        Returns:
            list: Full paths to the directories containing the dependency's
                header(s).

        Raises:
            ValueError: If the include directory cannot be determined for the
                specified dependency and default is None.

        """
        out = None
        if dep in cls.internal_libraries:
            out = cls.internal_libraries[dep].get('directory', None)
            if out is None:
                src = cls.internal_libraries[dep].get('source', None)
                if (src is not None) and os.path.isabs(src):
                    out = os.path.dirname(src)
            add_out = cls.internal_libraries[dep].get('include_dirs', None)
            if add_out:
                if out is None:
                    out = add_out
                else:
                    out = [out] + add_out
        elif dep in cls.external_libraries:
            dep_lang = cls.external_libraries[dep].get('language', cls.language)
            out = ygg_cfg.get(dep_lang, '%s_include' % dep, None)
            if os.path.isfile(out):
                out = os.path.dirname(out)
        elif os.path.isfile(dep):
            out = os.path.dirname(dep)
        if out is None:
            if default is None:
                raise ValueError("Could not determine include directory for "
                                 "dependency '%s'" % dep)
            else:
                out = default
        if not isinstance(out, list):
            out = [out]
        return out

    @classmethod
    def get_dependency_order(cls, deps):
        r"""Get the correct dependency order, including any dependencies for
        the direct dependencies.

        Args:
            deps (list): Dependencies in order.

        Returns:
            list: Dependency order.

        """
        out = []
        if not isinstance(deps, list):
            deps = [deps]
        for d in deps:
            new_deps = []
            sub_deps = cls.internal_libraries.get(d, {}).get(
                'internal_dependencies', [])
            sub_deps = cls.get_dependency_order(sub_deps)
            min_dep = len(out)
            for sub_d in sub_deps:
                if sub_d in out:
                    min_dep = min(min_dep, out.index(sub_d))
                else:
                    new_deps.append(sub_d)
            if d in out:
                dpos = out.index(d)
                assert(dpos < min_dep)
                min_dep = dpos
            else:
                new_deps.insert(0, d)
            out = out[:min_dep] + new_deps + out[min_dep:]
        return out

    @classmethod
    def get_compiler_flags(cls, **kwargs):
        r"""Determine the flags required by the current compiler.

        Args:
            **kwargs: Keyword arguments are passed to cls.update_compiler_kwargs
                first and then the compiler's get_flags method.

        Returns:
            list: Flags for the compiler.

        """
        kwargs = cls.update_compiler_kwargs(**kwargs)
        return cls.get_tool('compiler').get_flags(**kwargs)

    @classmethod
    def get_linker_flags(cls, **kwargs):
        r"""Determine the flags required by the current linker.

        Args:
            **kwargs: Keyword arguments are passed to cls.update_linker_kwargs
                first and then the linker's get_flags method.

        Returns:
            list: Flags for the linker.

        """
        if kwargs.get('libtype', None) == 'static':
            tool = cls.get_tool('archiver')
        else:
            tool = cls.get_tool('linker')
        kwargs = cls.update_linker_kwargs(**kwargs)
        return tool.get_flags(**kwargs)

    @classmethod
    def update_compiler_kwargs(cls, for_api=False, for_model=False,
                               commtype=None, directory=None, include_dirs=None,
                               definitions=None, skip_interface_flags=False,
                               **kwargs):
        r"""Update keyword arguments supplied to the compiler get_flags method
        for various options.

        Args:
            dont_link (bool, optional): If True, the command will result in a
                linkable object file rather than an executable. Defaults to
                False.
            for_api (bool, optional): If True, flags are added that are required
                for compiling internal api libraries in this language. This
                includes external communication libraries. Defaults to False.
            for_model (bool, optional): If True, flags are added that are
                required for including the interface library. Defaults to False.
            commtype (str, optional): If provided, this is the communication
                type that should be used for the model and flags for just that
                comm type will be included. If None, flags for all installed
                comm types will be included. Default to None. This keyword is
                only used if for_model is True.
            include_dirs (list, optional): If provided, each list element will
                be added as an included directory flag. Defaults to None and
                is initialized as an empty list.
            definitions (list, optional): If provided, each list element will be
                added as a defintion. Defaults to None and is initialized to an
                empty list.
            skip_interface_flags (bool, optional): If True, interface flags will
                not be added. Defaults to False.
            internal_dependencies (list, optional): If provided, a list of names
                of internal libraries that are required or linkable object files
                for dependencies. Defaults to an empty list.
            external_dependencies (list, optional): If provided, a list of names
                of external libraries that are required or linkable object files
                for dependencies. Defaults to an empty list.
            **kwargs: Additional keyword arguments are passed to the compiler
                class's 'get_flags' method and get_linker_flags if dont_link is
                False.

        Returns:
            dict: Keyword arguments for a get_flags method providing compiler
                flags.

        """
        if include_dirs is None:
            include_dirs = []
        if definitions is None:
            definitions = []
        internal_dependencies = kwargs.pop('internal_dependencies', [])
        external_dependencies = kwargs.pop('external_dependencies', [])
        # Model specific compilation flags
        if (for_model or for_api) and (not skip_interface_flags):
            # Add comm flags
            for c in tools.get_installed_comm(language=cls.language):
                definitions.append('%sINSTALLED' % c[:3].upper())
            if commtype is None:
                commtype = tools.get_default_comm()
            definitions.append('%sDEF' % commtype[:3].upper())
        # Add interface as internal_dependency for models and expand
        # dependencies to get entire chain including sub-dependencies and so on
        if for_model and (not skip_interface_flags):
            if (((cls.interface_library is not None)
                 and (cls.interface_library not in internal_dependencies))):
                internal_dependencies.append(cls.interface_library)
            for k in cls.external_libraries.keys():
                if (k not in external_dependencies) and cls.is_library_installed(k):
                    external_dependencies.append(k)
        all_internal_dependencies = cls.get_dependency_order(internal_dependencies)
        # Add internal libraries as objects for api
        additional_objs = kwargs.pop('additional_objs', [])
        for x in internal_dependencies:
            libinfo = cls.internal_libraries[x]
            if libinfo.get('libtype', None) == 'object':
                src = cls.get_dependency_source(x)
                additional_objs.append(cls.get_tool('compiler').get_output_file(
                    src, dont_link=True))
        if additional_objs:
            kwargs['additional_objs'] = additional_objs
        # Add directories for internal/external dependencies
        for dep in all_internal_dependencies + external_dependencies:
            include_dirs += cls.get_dependency_include_dirs(dep)
        # Add flags for included directories
        if directory is not None:
            include_dirs.insert(0, directory)
        # Update kwargs
        if include_dirs:
            kwargs['include_dirs'] = include_dirs
        if definitions:
            kwargs['definitions'] = definitions
        if not kwargs.get('dont_link', False):
            libtype = kwargs.get('libtype', None)
            if libtype != 'object':
                kwargs = cls.update_linker_kwargs(
                    for_api=for_api, for_model=for_model, commtype=commtype,
                    skip_interface_flags=skip_interface_flags,
                    internal_dependencies=internal_dependencies,
                    external_dependencies=external_dependencies, **kwargs)
            if libtype is not None:
                kwargs['libtype'] = libtype
        return kwargs

    @classmethod
    def update_linker_kwargs(cls, for_api=False, for_model=False, commtype=None,
                             libtype='object', skip_interface_flags=False,
                             use_library_path_internal=False, **kwargs):
        r"""Update keyword arguments supplied to the linker/archiver get_flags
        method for various options.

        Args:
            for_api (bool, optional): If True, flags are added that are required
                for linking internal api libraries in this language. This
                includes external communication libraries. Defaults to False.
            for_model (bool, optional): If True, flags are added that are
                required for including the interface library. Defaults to False.
            commtype (str, optional): If provided, this is the communication
                type that should be used for the model and flags for just that
                comm type will be included. If None, flags for all installed
                comm types will be included. Default to None. This keyword is
                only used if for_model is True.
            libtype (str, optional): Library type that should be created by the
                linker/archiver. Valid values are 'static', 'shared', or
                'object'. Defaults to 'object'.
            skip_interface_flags (bool, optional): If True, interface flags will
                not be added. Defaults to False.
            libraries (list, optional): Full paths to libraries that should be
                linked against. Defaults to an empty list.
            internal_dependencies (list, optional): If provided, a list of names
                of internal libraries that are required or linkable object files
                for dependencies. Defaults to an empty list.
            external_dependencies (list, optional): If provided, a list of names
                of external libraries that are required or linkable object files
                for dependencies. Defaults to an empty list.
            use_library_path_internal (bool, optional): If True, internal
                dependencies are included as full paths. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the linker
                (or archiver if static is True) 'get_flags' method.

        Returns:
            dict: Keyword arguments for a get_flags method providing linker/
                archiver flags.

        """
        # Copy/Pop so that empty default dosn't get appended to
        libraries = kwargs.pop('libraries', [])
        internal_dependencies = kwargs.pop('internal_dependencies', [])
        external_dependencies = kwargs.pop('external_dependencies', [])
        # Add interface as internal_dependency for models
        if for_model and (not skip_interface_flags):
            if (((cls.interface_library is not None)
                 and (cls.interface_library not in internal_dependencies))):
                internal_dependencies.append(cls.interface_library)
            for k in cls.external_libraries.keys():
                if (k not in external_dependencies) and cls.is_library_installed(k):
                    external_dependencies.append(k)
        # TODO: Expand library flags to include subdependencies?
        # Add flags for internal/external depenencies
        for dep in internal_dependencies + external_dependencies:
            dep_lib = cls.get_dependency_library(dep)
            if dep_lib and (dep_lib not in libraries):
                if not kwargs.get('dry_run', False):
                    assert(os.path.isfile(dep_lib))
                if use_library_path_internal and (dep in internal_dependencies):
                    kwargs.setdefault('flags', [])
                    kwargs['flags'].append(dep_lib)
                else:
                    libraries.append(dep_lib)
        # Update kwargs
        if libraries:
            kwargs['libraries'] = libraries
        if libtype in ['static', 'shared']:
            kwargs['build_library'] = True
        return kwargs

    @classmethod
    def language_executable(cls):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return cls.get_tool('compiler').get_executable()

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        kwargs['skip_flags'] = True
        return super(CompiledModelDriver, cls).language_version(**kwargs)
        
    def run_model(self, **kwargs):
        r"""Run the model. Unless overridden, the model will be run using
        run_executable.

        Args:
            **kwargs: Keyword arguments are passed to run_executable.

        """
        kwargs.update(exec_type='direct')
        return super(CompiledModelDriver, self).run_model(**kwargs)
        
    @classmethod
    def executable_command(cls, args, exec_type='compiler', **kwargs):
        r"""Compose a command for running a program using the compiler for this
        language and the provied arguments. If not already present, the
        compiler command and compiler flags are prepended to the provided
        arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it. For the compiler, this
                means the source files, for the linker, this means the object
                files.
            exec_type (str, optional): Type of executable command that will be
                returned. If 'compiler', a command using the compiler is
                returned, if 'linker', a command using the linker is returned,
                and if 'direct', the raw args being provided are returned.
                Defaults to 'compiler'.
            **kwargs: Additional keyword arguments are passed to either
                get_linker_flags or get_compiler_flags.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the compiler for this language.

        Raises:
            ValueError: If exec_type is not 'compiler', 'linker', or 'direct'.

        """
        if exec_type == 'direct':
            unused_kwargs = kwargs.pop('unused_kwargs', {})
            unused_kwargs.update(kwargs)
            return args
        elif exec_type == 'linker':
            exec_cls = cls.get_tool('linker')
        elif exec_type == 'compiler':
            exec_cls = cls.get_tool('compiler')
        else:
            raise ValueError("Invalid exec_type '%s'" % exec_type)
        return exec_cls.get_executable_command(args, **kwargs)
    
    @classmethod
    def is_library_installed(cls, lib, cfg=None):
        r"""Determine if a dependency is installed by check for the appropriate
        config options setting the path to the library files.

        Args:
            lib (str): Name of the library that should be checked.
            cfg (CisConfigParser, optional): Config class that should be checked.
                Defaults to yggdrasil.config.ygg_cfg if not provided.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        if cfg is None:
            cfg = ygg_cfg
        out = True
        dep_lang = cls.external_libraries[lib].get('language', cls.language)
        for lib_typ in cls.external_libraries[lib].keys():
            if lib_typ in ['libtype', 'language']:
                continue
            if not out:
                break
            lib_opt = '%s_%s' % (lib, lib_typ)
            out = (cfg.get(dep_lang, lib_opt, None) is not None)
        return out
        
    @classmethod
    def is_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        out = super(CompiledModelDriver, cls).is_configured()
        for k in cls.external_libraries.keys():
            if not out:
                break
            out = cls.is_library_installed(k)
        return out

    @classmethod
    def configure_libraries(cls, cfg):
        r"""Add configuration options for external libraries in this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        out = super(CompiledModelDriver, cls).configure_libraries(cfg)
        # Search for external libraries
        for k, v in cls.external_libraries.items():
            k_lang = v.get('language', cls.language)
            for t in v.keys():
                fname = v[t]
                assert(isinstance(fname, str))
                opt = '%s_%s' % (k, t)
                if t in ['libtype', 'language']:
                    continue
                elif t in ['include']:
                    desc_end = '%s headers' % k
                elif t in ['static', 'shared']:
                    desc_end = '%s %s library' % (k, t)
                else:
                    desc_end = '%s %s' % (k, t)
                desc = 'The full path to the directory containing %s.' % desc_end
                if cfg.has_option(k_lang, opt):
                    continue
                if os.path.isabs(fname):
                    fpath = fname
                else:
                    fpath = os.path.join(os.getcwd(), fname)
                fname = os.path.basename(fpath)
                if not os.path.isfile(fpath):
                    # Search the compiler/linker's search path, then the
                    # PATH environment variable.
                    if t in ['include']:
                        search_list = cls.get_tool('compiler').get_search_path()
                    else:
                        search_list = cls.get_tool('linker').get_search_path()
                    fpath = locate_file(fname, directory_list=search_list)
                if fpath:
                    logging.info('Located %s: %s' % (fname, fpath))
                    cfg.set(k_lang, opt, fpath)
                else:
                    out.append((k_lang, opt, desc))
        return out

    @classmethod
    def compile_dependencies(cls, **kwargs):
        r"""Compile any required internal libraries, including the interface."""
        base_libraries = []
        print('compile_dependencies', cls.language, cls.base_languages,
              cls.interface_library, cls.is_installed(),
              cls.is_language_installed(), cls.are_dependencies_installed(),
              cls.is_comm_installed(), cls.is_configured())
        for x in cls.base_languages:
            base_cls = import_component('model', x)
            base_libraries.append(base_cls.interface_library)
            print(base_cls, 'calling compile')
            base_cls.compile_dependencies(**kwargs)
        if (((cls.interface_library is not None) and cls.is_installed()
             and (cls.interface_library not in base_libraries))):
            # cls.call_compiler(cls.interface_library)
            dep_order = cls.get_dependency_order(cls.interface_library)
            print('dep_order', cls.language, dep_order)
            for k in dep_order[::-1]:
                cls.call_compiler(k, **kwargs)

    def compile_model(self, source_files=None, skip_interface_flags=False,
                      **kwargs):
        r"""Compile model executable(s).

        Args:
            source_files (list, optional): Source files that will be compiled.
                Defaults to None and is set to the source_files attribute.
            skip_interface_flags (bool, optional): If True, interface flags will
                not be added. This includes the logger flag specifying the
                current logging level. Defaults to False.
            **kwargs: Keyword arguments are passed on to the call_compiler
                method.

        Returns:
            str: Compiled model file path.

        """
        if source_files is None:
            source_files = self.source_files
        if not skip_interface_flags:
            kwargs['logging_level'] = self.logger.getEffectiveLevel()
        default_kwargs = dict(out=self.model_file,
                              compiler_flags=self.compiler_flags,
                              linker_flags=self.linker_flags,
                              for_model=True,
                              skip_interface_flags=skip_interface_flags,
                              overwrite=self.overwrite,
                              working_dir=self.working_dir,
                              products=self.products)
        for k, v in default_kwargs.items():
            kwargs.setdefault(k, v)
        return self.call_compiler(source_files, **kwargs)
    
    @classmethod
    def call_compiler(cls, src, language=None, **kwargs):
        r"""Compile a source file into an executable or linkable object file,
        checking for errors.

        Args:
            src (str): Full path to source file.
            out (str, optional): Full path to the output object file that should
                be created. Defaults to None and is created from the provided
                source file.
            flags (list, optional): Compilation flags. Defaults to []. If
                compiler_flags is present, flags is replaced by compiler_flags.
            compiler_flags (list, optional): Alternative to flags. Ignored
                if not provided.
            dont_link (bool, optional): If True, the command will result in a
                linkable object file rather than an executable. Defaults to
                False.
            overwrite (bool, optional): If True, the existing compile file will
                be overwritten. Otherwise, it will be kept and this function
                will return without recompiling the source file.
            language (str, optional): Language that should be used to compile
                the files. Defaults to None and the language of the current
                driver is used.
            products (list, optional): Existing Python list that additional
                products produced by the compilation should be appended to.
                Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are passed to run_executable.
                and call_linker if dont_link is False.

        Returns:
            str: Full path to compiled source.

        Raises:
            RuntimeError: If there is an error in calling the compiler.
            RuntimeError: If the compilation command dosn't yield the specified
                output file.

        """
        language = kwargs.pop('compiler_language', language)
        # Compile using another driver if the language dosn't match
        if (language is not None) and (language != cls.language):
            drv = import_component('model', cls.language)
            return drv.call_compiler(src, **kwargs)
        # Handle internal library
        if isinstance(src, str) and (src in cls.internal_libraries):
            dep = src
            # Compile an internal library using class defined options
            for k, v in cls.internal_libraries[dep].items():
                if k == 'directory':
                    kwargs.setdefault('working_dir', v)
                kwargs[k] = copy.deepcopy(v)
            src = kwargs.pop('source', None)
            if src is None:
                src = cls.get_dependency_source(dep)
            kwargs.setdefault('for_api', True)
            kwargs.setdefault('libtype', _default_libtype)
            if kwargs['libtype'] == 'header_only':
                return src
            elif kwargs['libtype'] in ['static', 'shared']:
                kwargs.setdefault(
                    'out', cls.get_dependency_library(dep, libtype=kwargs['libtype']))
                if (kwargs['libtype'] == 'static') and ('linker_language' in kwargs):
                    kwargs['archiver_language'] = kwargs.pop('linker_language')
            return cls.call_compiler(src, **kwargs)  # out=out, flags=flags,
        # Compile using the compiler after updating the flags
        kwargs = cls.update_compiler_kwargs(**kwargs)
        tool = cls.get_tool('compiler')
        out = tool.call(src, **kwargs)
        return out

    @classmethod
    def call_linker(cls, obj, language=None, **kwargs):
        r"""Link several object files to create an executable or library (shared
        or static), checking for errors.

        Args:
            obj (list): Object files that should be linked.
            language (str, optional): Language that should be used to link
                the files. Defaults to None and the language of the current
                driver is used.
            **kwargs: Additional keyword arguments are passed to run_executable.

        Returns:
            str: Full path to compiled source.

        """
        language = kwargs.pop('linker_language', language)
        # Link using another driver if the language dosn't match
        if (language is not None) and (language != cls.language):
            drv = import_component('model', cls.language)
            return drv.call_linker(obj, **kwargs)
        # Determine tool that should be used
        if kwargs.get('libtype', 'object') == 'static':
            tool = cls.get_tool('archiver')
        else:
            tool = cls.get_tool('linker')
        # Compile using the tool after updating the flags
        kwargs = cls.update_linker_kwargs(**kwargs)
        out = tool.call(obj, **kwargs)
        return out
