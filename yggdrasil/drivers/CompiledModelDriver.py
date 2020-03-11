import os
import re
import six
import copy
import logging
import warnings
import subprocess
from collections import OrderedDict
from yggdrasil import platform, tools, scanf
from yggdrasil.drivers.ModelDriver import ModelDriver, remove_products
from yggdrasil.components import import_component


logger = logging.getLogger(__name__)
_compiler_registry = OrderedDict()
_linker_registry = OrderedDict()
_archiver_registry = OrderedDict()
_default_libtype = 'static'
_conda_prefix = tools.get_conda_prefix()
_system_suffix = ""
if _conda_prefix is not None:
    _system_suffix = '_' + os.path.basename(_conda_prefix)


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
    if (out is None) and (not allow_failure):
        raise RuntimeError("Could not locate a %s tool." % tooltype)
    return out


def get_compilation_tool(tooltype, name, default=False):
    r"""Return the class providing information about a compilation tool.

    Args:
        tooltype (str): Type of tool. Valid values include 'compiler', 'linker',
            and 'archiver'.
        name (str): Name or path to the desired compilation tool.
        default (object, optional): Value that should be returned if a tool
            cannot be located. If False, an error will be raised. Defaults to
            False.

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
        return reg[name]
    if name.lower() in reg:
        return reg[name.lower()]
    if default is False:
        raise ValueError("Could not locate a %s tool with name '%s'"
                         % (tooltype, name))
    return default


# TODO: Cannot currently make compilation tools components because
# of circular imports
class CompilationToolMeta(type):
    r"""Meta class for registering compilers."""
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if not name.endswith('Base'):
            cls.before_registration(cls)
            if cls._dont_register:
                return cls
            assert(cls.toolname is not None)
            if getattr(cls, 'is_build_tool', False):
                languages = [cls.build_language]
            else:
                languages = cls.languages
            assert(len(languages) > 0)
            if cls.toolname in cls.aliases:  # pragma: debug
                raise ValueError(("The name '%s' for class %s is also in "
                                  "its list of aliases: %s")
                                 % (cls.toolname, name, cls.aliases))
            # Register by toolname & language
            reg = get_compilation_tool_registry(cls.tooltype)
            if 'by_language' not in reg:
                reg['by_language'] = OrderedDict()
            for l in languages:
                if l not in reg['by_language']:
                    reg['by_language'][l] = OrderedDict()
            for x in [cls.toolname] + cls.aliases:
                # Register by toolname
                if (x in reg) and (str(reg[x]) != str(cls)):  # pragma: debug
                    raise ValueError(
                        ("%s toolname '%s' already registered "
                         "(class = %s, existing = %s).")
                        % (cls.tooltype.title(), x, cls, reg[x]))
                reg[x] = cls
                # Register by language
                for l in languages:
                    if x in reg['by_language'][l]:  # pragma: debug
                        raise ValueError(("%s toolname '%s' already registered for "
                                          "%s language.")
                                         % (cls.tooltype.title(), x, l))
                    reg['by_language'][l][x] = cls
        return cls


@six.add_metaclass(CompilationToolMeta)
class CompilationToolBase(object):
    r"""Base class for compilation command line tools.

    Class Attributes:
        toolname (str): Tool name used for registration and as a default for the
            executable. [REQUIRED]
        aliases (list): Alternative names that the tool might have.
        tooltype (str): Tool type. One of 'compiler', 'linker', or 'archiver'.
            [AUTOMATED]
        languages (list): Programming languages that this tool can be used on.
            [REQUIRED]
        platforms (list): Platforms that the tool is available on. Defaults to
            ['Windows', 'MacOS', 'Linux'].
        default_executable (str): The default tool executable command if
            different than the toolname.
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
            to search for library files. Either search_path_env or
            search_path_flags must be set. [REQUIRED]
        search_path_conda (str): Path relative to the conda prefix that should
            be searched if the CONDA_PREFIX environment variable is set.
        search_path_flags (list): Flags that should be passed to the tool
            executable in order to locate the search path. Either search_path_env
            or search_path_flags must be set. [REQUIRED]
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
        product_exts (list): List of extensions that will be added to the
            output file's base to get a list of products that might be produced
            by calling the compilation tool.
        product_files (list): List of file basenames that will be joined with
            the directory containing each output to get a list of products that
            might be produced by calling the compilation tool.
        remove_product_exts (list): List of extensions or directories matching
            entries in product_exts and product_files that should be removed
            during cleanup. Be careful when adding files to this list.

    """

    _schema_type = None
    _schema_subtype_key = 'toolname'
    _schema_required = []
    _schema_properties = {'executable': {'type': 'string'},
                          'flags': {'type': 'array',
                                    'items': {'type': 'string'}}}
    _dont_register = False
    toolname = None
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
    version_flags = ['--version']
    product_exts = []
    product_files = []
    source_product_exts = []
    remove_product_exts = []

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
        if cls.toolname is None:  # pragma: debug
            raise ValueError("Registering unnamed compilation tool.")
        cls._schema_type = cls.tooltype
        attr_list = ['default_executable', 'default_flags']
        # Set attributes based on environment variables
        for k in attr_list:
            # Copy so that list modification is not propagated to subclasses
            setattr(cls, k, copy.deepcopy(getattr(cls, k, [])))
            env = getattr(cls, '%s_env' % k, None)
            if env is not None:
                if k in ['default_flags']:
                    if not isinstance(env, list):
                        env = [env]
                    old_val = getattr(cls, k, [])
                    for ienv in env:
                        new_val = os.environ.get(ienv, '').split()
                        old_val += [v for v in new_val if v not in old_val]
                else:
                    setattr(cls, k, os.environ.get(env, getattr(cls, k)))
        # Set default_executable to name
        if cls.default_executable is None:
            cls.default_executable = cls.toolname
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
                new_ext = import_component('model', x).get_language_ext()
                if new_ext is not None:
                    cls._language_ext += new_ext
        return cls._language_ext

    @classmethod
    def set_env(cls, existing=None, **kwargs):
        r"""Set environment variables required for compilation.

        Args:
            existing (dict, optional): Existing dictionary of environment
                variables that new variables should be added to. Defaults
                to a copy of os.environ.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            dict: Environment variables for the model process.

        """
        if existing is None:
            existing = {}
            existing.update(os.environ)
        return existing

    @classmethod
    def write_wrappers(cls, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are ignored (only included to
               allow cascade from child classes).

        Returns:
            list: Full paths to any created wrappers.

        """
        return []
        
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
            for i, v in enumerate(value):
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
        if (not isinstance(key, dict)) and (key in cls.flag_options):
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
    def get_env_flags(cls):
        r"""Get a list of flags stored in the environment variables.

        Returns:
            list: Flags for the tool.

        """
        out = []
        env = getattr(cls, 'default_flags_env', None)
        if env is not None:
            if not isinstance(env, list):
                env = [env]
            for ienv in env:
                out += os.environ.get(ienv, '').split()
        return out

    @classmethod
    def get_flags(cls, flags=None, outfile=None, output_first=None,
                  unused_kwargs=None, skip_defaults=False,
                  dont_skip_env_defaults=False, **kwargs):
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
            dont_skip_env_defaults (bool, optional): If skip_defaults is True,
                and this keyword is True, the flags from the environment
                variable will be added. Defaults to False.
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
        if skip_defaults:
            # Include flags set by the environment (this is especially
            # important when using the Conda compilers
            if dont_skip_env_defaults:
                out += cls.get_env_flags()
        else:
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
                                      % (cls.tooltype, cls.toolname))
        return out

    @classmethod
    def get_conda_prefix(cls):
        r"""Determine the conda path prefix.

        Returns:
            str: Conda path prefix. None will be returned if conda is not
                installed.

        """
        return tools.get_conda_prefix()
            
    @classmethod
    def get_search_path(cls, conda_only=False):
        r"""Determine the paths searched by the tool for external library files.

        Args:
            conda_only (bool, optional): If True, only the search paths as
                indicated by a conda environment are returned. Defaults to False.

        Returns:
            list: List of paths that the tools will search.

        """
        if (cls.search_path_flags is None) and (cls.search_path_env is None):
            raise NotImplementedError("get_search_path method not implemented for "
                                      "%s tool '%s'" % (cls.tooltype, cls.toolname))
        paths = []
        # Get search paths from environment variable
        if (cls.search_path_env is not None) and (not conda_only):
            if not isinstance(cls.search_path_env, list):
                cls.search_path_env = [cls.search_path_env]
            for ienv in cls.search_path_env:
                ienv_paths = os.environ.get(ienv, '').split(os.pathsep)
                for x in ienv_paths:
                    if x:
                        paths.append(x)
        # Get flags based on path
        if (cls.search_path_flags is not None) and (not conda_only):
            output = cls.call(cls.search_path_flags, skip_flags=True,
                              allow_error=True)
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
        # Get search paths from the conda environment
        if (cls.search_path_conda is not None):
            conda_prefix = cls.get_conda_prefix()
            if conda_prefix:
                if not isinstance(cls.search_path_conda, list):
                    cls.search_path_conda = [cls.search_path_conda]
                for ienv in cls.search_path_conda:
                    ienv_path = os.path.join(conda_prefix, ienv)
                    if (ienv_path not in paths) and os.path.isdir(ienv_path):
                        paths.append(ienv_path)
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
        if (len(cmd) == 0) or (not os.path.splitext(cmd[0])[0].endswith(cls.toolname)):
            cmd = [cls.get_executable()] + cmd
        # Pop library flags so it is not an unused_kwarg in cases of non-linking
        # compiler command
        for k in ['library_flags', 'skip_library_libs']:
            unused_kwargs.pop(k, [])
        return cmd

    @classmethod
    def remove_products(cls, src, new):
        r"""Remove products produced during compilation.

        Args:
            src (list): Input arguments to compilation call that was used to
                generate the output file (usually one or more source files).
            new (str): The full path to the primary product of the compilation
                call (usually an object, executable, or library).

        """
        products = []
        cls.append_product(products, src, new)
        source_products = cls.get_source_products(products)
        remove_products(products, source_products)

    @classmethod
    def get_source_products(cls, products, source_products=[]):
        r"""Get the list of products that should be removed without checking
        for source files based on cls.remove_product_exts.

        Args:
            products (list): List of products that should be checked against
                cls.remove_product_exts.
            source_products (list, optional): Existing list of products that
                new source_products should be added to. Defaults to [].

        Returns:
            list: Products that should be removed without checking for source
                files.

        """
        remove_ext = tuple(cls.remove_product_exts)
        for x in products:
            if x.endswith(remove_ext) and (x not in source_products):
                source_products.append(x)
        return source_products

    @classmethod
    def append_product(cls, products, src, new, new_dir=None,
                       dont_append_src=False):
        r"""Append a product to the specified list along with additional values
        indicated by cls.product_exts.

        Args:
            products (list): List of of existing products that new product
                should be appended to.
            src (list): Input arguments to compilation call that was used to
                generate the output file (usually one or more source files).
            new (str): New product that should be appended to the list.
            new_dir (str, optional): Directory that should be used as base when
                adding files listed in cls.product_files. Defaults to
                os.path.dirname(new).
            dont_append_src (bool, optional): If True and src is in the list of
                products, it will be removed. Defaults to False.

        """
        products.append(new)
        # Add products based on extensions
        new_base = os.path.splitext(new)[0]
        for ext in cls.product_exts:
            inew = new_base + ext
            if inew not in products:
                products.append(inew)
        # Add products based on directory
        if new_dir is None:
            new_dir = os.path.dirname(new)
        for base in cls.product_files:
            inew = os.path.join(new_dir, base)
            if inew not in products:
                products.append(inew)
        # Make sure the source is not in the product list
        if dont_append_src:
            for isrc in src:
                if isrc in products:  # pragma: debug
                    products.remove(isrc)

    @classmethod
    def call(cls, args, language=None, skip_flags=False, dry_run=False,
             out=None, overwrite=False, products=None, allow_error=False,
             working_dir=None, additional_args=None, suffix='', **kwargs):
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
            suffix (str, optional): Suffix that should be added to the
                output file (before the extension). Defaults to "".
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
                                 additional_args=additional_args,
                                 suffix=suffix, **kwargs)
        # Add additional arguments
        if isinstance(args, (str, bytes)):
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
                                          suffix=suffix, **kwargs)
            elif (((out != 'clean') and (not os.path.isabs(out))
                   and (working_dir is not None))):
                out = os.path.join(working_dir, out)
            assert(out not in args)  # Don't remove source files
            # Check for file
            if overwrite and (not dry_run):
                cls.remove_products(args, out)
                if os.path.isfile(out) or os.path.isdir(out):  # pragma: debug
                    raise RuntimeError("Product not removed: %s" % out)
            if (not dry_run) and (os.path.isfile(out) or os.path.isdir(out)):
                cls.append_product(products, args, out)
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
                    cls.append_product(products, args, out)
                return out
        # Run command
        output = ''
        try:
            if (not skip_flags) and ('env' not in unused_kwargs):
                unused_kwargs['env'] = cls.set_env()
            logger.debug('Command: "%s"' % ' '.join(cmd))
            proc = tools.popen_nobuffer(cmd, **unused_kwargs)
            output, err = proc.communicate()
            output = output.decode("utf-8")
            if (proc.returncode != 0) and (not allow_error):
                raise RuntimeError("Command '%s' failed with code %d:\n%s."
                                   % (' '.join(cmd), proc.returncode, output))
            try:
                logger.debug(' '.join(cmd) + '\n' + output)
            except UnicodeDecodeError:  # pragma: debug
                tools.print_encoded(output)
        except (subprocess.CalledProcessError, OSError) as e:
            if not allow_error:
                raise RuntimeError("Could not call command '%s': %s"
                                   % (' '.join(cmd), e))
        # Check for output
        if (not skip_flags):
            if (out != 'clean'):
                if not (os.path.isfile(out)
                        or os.path.isdir(out)):  # pragma: debug
                    logger.error('%s\n%s' % (' '.join(cmd), output))
                    raise RuntimeError(("%s tool, %s, failed to produce "
                                        "result '%s'")
                                       % (cls.tooltype.title(), cls.toolname, out))
                logger.debug("%s %s produced %s"
                             % (cls.tooltype.title(), cls.toolname, out))
                cls.append_product(products, args, out)
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
        linker_flags (list, optional): Flags that should be used when linking
            compiled objects. Defaults to default_linker_flags if not provided.
        archiver_flags (list, optional): Flags that should be used for combining
            compiled objects into a static library. Defaults to
            default_archiver_flags if not provided.

    Class Attributes:
        compile_only_flag (str): Flag that should prepended to compiler/linker
            combination tool arguments to indicate that only compilation should
            be performed.
        default_linker (str): Name of linker that should be used after compiling
            with this compiler. If not set, it is assumed that this compiler is
            also a linker.
        default_archiver (str): Name of archiver that should be used to create
            a static library after compiling with this compiler. If not set,
            it is assumed that this compiler is also a linker.
        default_linker_flags (list): Flags that should be used with the linker
            if no other flags are provided.
        default_archiver_flags (list): Flags that should be used with the
            archiver if no other flags are provided.
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

    def __init__(self, **kwargs):
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
        if platform._is_win:  # pragma: windows
            cls.object_ext = '.obj'
        if cls.no_separate_linking:
            cls.is_linker = True
            cls.compile_only_flag = None
        if cls.is_linker:
            if cls.default_linker is None:
                cls.default_linker = cls.toolname
            copy_attr = ['toolname', 'aliases', 'languages', 'platforms',
                         'default_executable', 'default_executable_env']
            # 'product_exts', 'product_files']
            linker_name = '%sLinker' % cls.__name__.split('Compiler')[0]
            linker_attr = copy.deepcopy(cls.linker_attributes)
            linker_attr.setdefault('toolname', cls.default_linker)
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
            cls.combine_with_linker = (cls.toolname == cls.default_linker)

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
    def get_library_tool(cls, libtype=None, **kwargs):
        r"""Determine the tool that should be used based on the provided
        arguments.

        Args:
            libtype (str, optional): Library type that should be created by the
                linker/archiver. If 'static', the archiver is returned. If
                'shared' or any other value, the linker is returned. Defaults to
                None.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            CompilationToolBase: Linker/archiver that should be used.

        """
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
        if not dont_link:
            outfile_link = kwargs.pop('outfile', None)
        out = super(CompilerBase, cls).get_flags(**kwargs)
        # Add flags for compilation only or provided output file
        if ((dont_link and (cls.compile_only_flag is not None)
             and (not kwargs.get('skip_defaults', False)))):
            if cls.compile_only_flag not in out:
                out.insert(0, cls.compile_only_flag)
        # Add linker switch
        if (not dont_link) or add_linker_switch:
            if cls.linker_switch is not None:  # pragma: windows
                if cls.linker_switch not in out:
                    out.append(cls.linker_switch)
        # Add linker flags
        if (not dont_link):
            if (not cls.combine_with_linker):
                raise ValueError("Cannot combine linker and compiler flags.")
            logger.debug('The returned flags will contain linker flags that '
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
                        libtype=None, no_src_ext=False,
                        suffix="", **kwargs):
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
            libtype (str, optional): Library type that should be created by the
                linker/archiver. Defaults to None.
            no_src_ext (bool, optional): If True, the source extension will not
                be added to the object file name. Defaults to False. Ignored if
                dont_link is False.
            suffix (str, optional): Suffix that should be added to the
                output file (before the extension). Defaults to "".
            **kwargs: Additional keyword arguments are ignored unless dont_link
                is False; then they are passed to the linker's get_output_file
                method.

        Returns:
            str: Full path to file that will be produced.

        """
        # Get intermediate file
        if cls.no_separate_linking:
            obj = src
            kwargs['suffix'] = suffix
        else:
            if isinstance(src, list):
                obj = []
                for isrc in src:
                    obj.append(cls.get_output_file(isrc, dont_link=True,
                                                   working_dir=working_dir,
                                                   no_src_ext=no_src_ext,
                                                   libtype=libtype, **kwargs))
            else:
                src_base, src_ext = os.path.splitext(src)
                if no_src_ext or src_base.endswith('_%s' % src_ext[1:]):
                    obj = '%s%s%s' % (src_base, suffix, cls.object_ext)
                else:
                    obj = '%s_%s%s%s' % (src_base, src_ext[1:],
                                         suffix, cls.object_ext)
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
        tool = None
        if not dont_link:
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
                kwargs_link = tool.extract_kwargs(kwargs, compiler=cls)
            else:
                kwargs.pop('linker_language', None)
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
            kwargs.pop('linker_language', None)
            return super(CompilerBase, cls).call(args, skip_flags=skip_flags,
                                                 out=out, **kwargs)
        else:
            kwargs_link = tool.extract_kwargs(kwargs, compiler=cls)
            if (tool.tooltype != 'linker') and ('linker_language' in kwargs):
                kwargs_link[tool.tooltype + '_language'] = kwargs.pop(
                    'linker_language')
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
        if platform._is_win:  # pragma: windows
            # TODO: Use 'cyg' prefix on cygwin?
            cls.library_prefix = ''
            cls.library_ext = '.dll'
            cls.executable_ext = '.exe'
            cls.search_path_conda = 'DLLs'
        elif platform._is_mac:
            # TODO: Dynamic library by default on windows?
            # cls.shared_library_flag = '-dynamiclib'
            cls.library_ext = '.dylib'
            cls.flag_options['library_rpath'] = '-rpath'
        else:
            cls.library_ext = '.so'
            cls.flag_options['library_rpath'] = '-Wl,-rpath'

    @classmethod
    def libpath2libname(cls, libpath):
        r"""Determine the library name from the library path.

        Args:
            libpath (str): Full or partial path to library.
        
        Returns:
            str: Library name.

        """
        if platform._is_win:  # pragma: windows
            # Extension must remain or else the MSVC linker assumes the name
            # refers to a .obj file
            libname = os.path.basename(libpath)
        else:
            libname = cls.file2base(libpath)
        if cls.library_prefix:
            libname = libname.split(cls.library_prefix)[-1]
        return libname

    @classmethod
    def extract_kwargs(cls, kwargs, compiler=None, add_kws_link=[],
                       add_kws_both=[]):
        r"""Extract linker kwargs, leaving behind just compiler kwargs.

        Args:
            kwargs (dict): Keyword arguments passed to the compiler that should
                be sorted into kwargs used by either the compiler or linker or
                both. Keywords that are not used by the compiler will be removed
                from this dictionary.
            compiler (CompilerBase, optional): Compiler tool that linker kwargs
                are being extracted in order to call. Defaults to None and is
                ignored.
            add_kws_link (list, optional): Addition keywords that should be
                added to the list of those reserved for the linker. Defaults to
                [].
            add_kws_both (list, optional): Additional keywords that should be
                added to the list of those that are valid for both the linker
                and compiler. Defaults to [].

        Returns:
            dict: Keyword arguments that should be passed to the linker.

        """
        kws_link = ['build_library', 'skip_library_libs', 'use_library_path',
                    '%s_flags' % cls.tooltype, '%s_language' % cls.tooltype,
                    'libraries', 'library_dirs', 'library_libs', 'library_flags']
        kws_both = ['overwrite', 'products', 'allow_error', 'dry_run',
                    'working_dir', 'env']
        kws_link += add_kws_link
        kws_both += add_kws_both
        kwargs_link = {}
        # Add kwargs from flag_options
        flag_options_comp = []
        if compiler is not None:
            flag_options_comp = list(compiler.flag_options.keys())
        for k in cls.flag_options.keys():
            if (k in kws_link) or (k in kws_both):
                continue
            if k in flag_options_comp:
                kws_both.append(k)
            else:
                kws_link.append(k)
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
        library_rpath = kwargs.pop('library_rpath', [])
        library_flags = kwargs.pop('library_flags', [])
        flags = copy.deepcopy(kwargs.pop('flags', []))
        # Get list of libraries
        dest_flags = []
        if use_library_path:
            if skip_library_libs:
                if ((isinstance(use_library_path, bool)
                     or (use_library_path == 'library_flags'))):
                    dest_flags = library_flags
                else:
                    dest_flags = kwargs.pop(use_library_path)
            else:
                dest_flags = flags
        for x in libraries:
            if use_library_path:
                if x not in dest_flags:
                    dest_flags.append(x)
            else:
                x_d, x_f = os.path.split(x)
                if x_d not in library_dirs:
                    library_dirs.append(x_d)
                x_l = cls.libpath2libname(x_f)
                if x_l not in library_libs:
                    library_libs.append(x_l)
                if (((cls.tooltype == 'linker') and x_f.endswith(cls.library_ext)
                     and ('library_rpath' in cls.flag_options))):
                    if x_d not in library_rpath:
                        library_rpath.append(x_d)
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
        if library_rpath:
            kwargs['library_rpath'] = library_rpath
        out = super(LinkerBase, cls).get_flags(flags=flags, **kwargs)
        # Add flag specifying the shared library
        if build_library and (cls.shared_library_flag is not None):
            out.insert(0, cls.shared_library_flag)
        return out
    
    @classmethod
    def get_output_file(cls, obj, build_library=False, working_dir=None,
                        suffix="", **kwargs):
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
            suffix (str, optional): Suffix that should be added to the
                output file (before the extension). Defaults to "".
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            str: Full path to file that will be produced.

        """
        if isinstance(obj, list):
            return [cls.get_output_file(obj[0], build_library=build_library,
                                        working_dir=working_dir,
                                        suffix=suffix, **kwargs)]
        if build_library:
            prefix = cls.library_prefix
            out_ext = cls.library_ext
        else:
            prefix = ''
            out_ext = cls.executable_ext
        obj_dir, obj_base = os.path.split(obj)
        out_base = '%s%s%s%s' % (prefix,
                                 os.path.splitext(obj_base)[0],
                                 suffix,
                                 out_ext)
        out = os.path.join(obj_dir, out_base)
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
        # Delete attributes that are linker specific
        for k in ['shared_library_flag']:
            setattr(cls, k, None)
        if platform._is_win:  # pragma: windows
            cls.library_ext = '.lib'
            cls.search_path_conda = os.path.join('Library', 'lib')
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

    
class BuildToolBase(CompilerBase):  # pragma: in progress
    r"""Base class for build tools which are used to coordinate compilation.

    Args:
        buildfile (str, optional): File containing information about the build.
            Defaults to default_buildfile class attribute, if set.
        builddir (str, optional): Directory where build files should be placed.
            Defaults to directory where build is called.
        sourcedir (str, optional): Directory where source files are stored.
            Defaults to directory where build is called.
        target (str, optional): Build target. If not provided, build will be
            created without a target.

    Class Attributes:

    """
    tooltype = 'buildtool'
    flag_options = OrderedDict()
    default_buildfile = None
    _schema_properties = {
        'buildfile': {'type': 'string'},
        'builddir': {'type': 'string'},
        'sourcedir': {'type': 'string'},
        'target': {'type': 'string'}}
    

class DummyLinkerBase(LinkerBase):
    r"""Base class for a dummy linker in the case that the linking step cannot
    be split into a separate call."""

    toolname = 'dummy'
    is_dummy = True

    @classmethod
    def get_flags(cls, **kwargs):  # pragma: debug
        r"""Raises an error to ward off getting flags for the dummy linker."""
        raise RuntimeError("DummyLinker")

    @classmethod
    def call(cls, *args, **kwargs):  # pragma: debug
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
    _config_keys = ['compiler', 'linker', 'archiver']
    _config_attr_map = [{'attr': 'default_compiler',
                         'key': 'compiler'},
                        {'attr': 'default_compiler_flags',
                         'key': 'compiler_flags',
                         'type': list},
                        {'attr': 'default_linker',
                         'key': 'linker'},
                        {'attr': 'default_linker_flags',
                         'key': 'linker_flags',
                         'type': list},
                        {'attr': 'default_archiver',
                         'key': 'archiver'},
                        {'attr': 'default_archiver_flags',
                         'key': 'archiver_flags',
                         'type': list}]

    def __init__(self, name, args, skip_compile=False, **kwargs):
        kwargs.setdefault('overwrite', (not kwargs.pop('preserve_cache', False)))
        super(CompiledModelDriver, self).__init__(name, args, **kwargs)
        # Compile
        if not skip_compile:
            try:
                self.compile_dependencies()
                self.compile_model()
                self.products.append(self.model_file)
            except BaseException:
                self.remove_products()
                raise
            assert(os.path.isfile(self.model_file))
            self.debug("Compiled %s", self.model_file)

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        ModelDriver.after_registration(cls, **kwargs)
        for k, v in cls.external_libraries.items():
            libtype = v.get('libtype', None)
            if (libtype is not None) and (libtype not in v):
                libfile = cls.cfg.get(cls.language,
                                      '%s_%s' % (k, libtype), None)
                if libfile is not None:
                    v[libtype] = libfile
        for k in ['compiler', 'linker', 'archiver']:
            # Set default linker/archiver based on compiler
            default_tool_name = getattr(cls, 'default_%s' % k, None)
            if default_tool_name:
                default_tool = get_compilation_tool(k, default_tool_name,
                                                    default=None)
                if (((default_tool is None)
                     or (not default_tool.is_installed()))):  # pragma: debug
                    warnings.warn(('Default %s for %s (%s) not installed. '
                                   'Attempting to locate an alternative .')
                                  % (k, cls.language, default_tool_name))
                    setattr(cls, 'default_%s' % k, None)
        
    def parse_arguments(self, args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        # Set defaults from attributes
        for k0 in ['compiler', 'linker', 'archiver']:
            for k in [k0, '%s_flags' % k0]:
                v = getattr(self, k, None)
                if v is None:
                    setattr(self, k, getattr(self, 'default_%s' % k))
        # Set tools so that they are cached
        for k in ['compiler', 'linker', 'archiver']:
            setattr(self, '%s_tool' % k, self.get_tool_instance(k))
            self.get_tool_instance(k)
        super(CompiledModelDriver, self).parse_arguments(args, **kwargs)
        # Handle case where provided argument is source and not executable
        # and case where provided argument is executable, but source files are
        # not specified
        model_ext = os.path.splitext(self.model_file)[-1]
        model_is_source = self.is_source_file(self.model_file)
        if model_is_source:
            self.model_src = self.model_file
            if len(self.source_files) == 0:
                self.source_files.append(self.model_file)
        else:
            if len(model_ext) == 0:
                self.model_file += self.get_tool_instance('linker').executable_ext
            else:
                # Assert that model file is not source code in any of the
                # registered languages
                if (((model_ext in self.get_all_language_ext())
                     and (model_ext != '.exe'))):  # pragma: debug
                    from yggdrasil.components import import_component
                    from yggdrasil.schema import get_schema
                    s = get_schema()['model']
                    for v_name in s.classes:
                        v = import_component('model', v_name)
                        if (((v.language_ext is not None)
                             and (model_ext in v.language_ext))):
                            raise RuntimeError(
                                ("Extension '%s' indicates that the "
                                 "model language is '%s', not '%s' "
                                 "as specified.")
                                % (model_ext, v.language, self.language))
            if (len(self.source_files) == 0) and (self.language_ext is not None):
                # Add source file based on the model file
                # model_is_source = True
                self.model_src = (os.path.splitext(self.model_file)[0]
                                  + self.language_ext[0])
                self.source_files.append(self.model_src)
        # Add intermediate files and executable by doing a dry run
        self.set_target_language()  # Required by make and cmake
        kwargs = dict(products=self.products, dry_run=True)
        if model_is_source:
            kwargs['out'] = None
        out = self.compile_model(**kwargs)
        if model_is_source:
            self.debug('Determined model file: %s', out)
            self.model_file = out
        # Adjust products
        self.get_tool_instance('compiler').get_source_products(
            self.products, source_products=self.source_products)
        self.debug("source_files: %s", str(self.source_files))
        self.debug("model_file: %s", self.model_file)

    def set_target_language(self):
        r"""Set the language of the target being compiled (usually the same
        as the language associated with this driver.

        Returns:
            str: Name of language.

        """
        return self.language

    def get_source_file(self, args):
        r"""Determine the source file based on arguments.

        Args:
            args (list): Arguments provided.

        Returns:
            str: Full path to source file select.

        """
        out = args[0]
        if (not self.is_source_file(out)) and self.source_files:
            assert(isinstance(self.source_files, list))
            out = self.source_files[0]
        out = super(CompiledModelDriver, self).get_source_file([out])
        return out

    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            list: Full paths to any created wrappers.

        """
        out = super(CompiledModelDriver, self).write_wrappers(**kwargs)
        kwargs.setdefault('logging_level', self.logger.getEffectiveLevel())
        for k in self._schema_properties.keys():
            kwargs.setdefault(k, getattr(self, k, None))
        out += self.get_tool_instance('compiler').write_wrappers(**kwargs)
        return out
        
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

    @staticmethod
    def get_tool_static(cls, tooltype, return_prop='tool', default=False):
        r"""Get the class associated with the specified compilation tool for
        this language.

        Args:
            tooltype (str): Type of compilation tool that should be returned.
            return_prop (str, optional): Value that should be returned. If
                'tool', the tool is returned. If 'name', the tool name is
                returned. If 'flags', the tool flags are returned. Defaults to
                'tool'.
            default (object, optiona): Tool that should be returned if one cannot
                be identified. If False, an error will be raised when a tool
                cannot be located. Defaults to False.

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
                toolname = getattr(cls, tooltype, None)
                if toolname is None:
                    toolname = getattr(cls, 'default_%s' % tooltype, None)
                if toolname is None:
                    if default is False:
                        raise NotImplementedError("%s not set for language '%s'."
                                                  % (tooltype.title(), cls.language))
                    return default
                if return_prop == 'name':
                    return toolname
                # Get flags
                tool_flags = getattr(cls, '%s_flags' % tooltype, None)
                if tool_flags is None:
                    tool_flags = getattr(cls, 'default_%s_flags' % tooltype, None)
                if return_prop == 'flags':
                    return tool_flags
                # Get tool
                kwargs = {'executable': toolname, 'flags': tool_flags}
                if tooltype == 'compiler':
                    kwargs.update(
                        linker=cls.get_tool(
                            'linker', return_prop='name', default=None),
                        linker_flags=cls.get_tool(
                            'linker', return_prop='flags', default=None),
                        archiver=cls.get_tool(
                            'archiver', return_prop='name', default=None),
                        archiver_flags=cls.get_tool(
                            'archiver', return_prop='flags', default=None))
                out = get_compilation_tool(tooltype, toolname)(**kwargs)
            else:
                out_tool = cls.get_tool('compiler', default=None)
                if out_tool is None:  # pragma: debug
                    if default is False:
                        raise NotImplementedError("%s not set for language '%s'."
                                                  % (tooltype.title(), cls.language))
                    return default
                out = getattr(out_tool, tooltype)()
        # Returns correct property given the tool
        if return_prop == 'tool':
            return out
        elif return_prop == 'name':  # pragma: no cover
            return out.name
        elif return_prop == 'flags':  # pragma: no cover
            return out.flags
        else:
            raise ValueError("Invalid return_prop: '%s'" % return_prop)

    def get_tool_instance(self, *args, **kwargs):
        r"""Get tool from a driver instance.

        Args:
            *args: Arguments are passed to the get_tool_static method.
            **kwargs: Keyword arguments are passed to the get_tool_static method.

        Returns:
            CompilationToolBase: Class providing an interface to the specified
                compilation tool.

        """
        return CompiledModelDriver.get_tool_static(self, *args, **kwargs)
        
    @classmethod
    def get_tool(cls, *args, **kwargs):
        r"""Get tool from a driver class.

        Args:
            *args: Arguments are passed to the get_tool_static method.
            **kwargs: Keyword arguments are passed to the get_tool_static method.

        Returns:
            CompilationToolBase: Class providing an interface to the specified
                compilation tool.

        """
        return CompiledModelDriver.get_tool_static(cls, *args, **kwargs)

    @classmethod
    def get_external_libraries(cls, no_comm_libs=False):
        r"""Determine the external libraries that are required based on the
        default comm.

        Args:
            no_comm_libs (bool, optional): If True, libraries for the installed
                comms are not included in the returned list. Defaults to False.

        Returns:
            list: The names of external libraries required by the interface
                library, including the dependency libraries for the installed
                comm libraries.

        """
        out = copy.deepcopy(cls.internal_libraries.get(cls.interface_library, {}).get(
            'external_dependencies', []))
        if (not no_comm_libs) and (cls.language is not None):
            for k, v in cls.supported_comm_options.items():
                if ('libraries' in v) and cls.is_comm_installed(k):
                    out += v['libraries']
        return out

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
        out = None
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
            out = cls.cfg.get(dep_lang, '%s_%s' % (dep, 'include'), None)
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
                if os.path.isfile(libinfo[libtype]):
                    out = libinfo[libtype]
                else:  # pragma: no cover
                    out = cls.cfg.get(dep_lang, '%s_%s' % (dep, libtype), None)
            elif cls.cfg.has_option(dep_lang, '%s_%s' % (dep, libtype)):
                out = cls.cfg.get(dep_lang, '%s_%s' % (dep, libtype))
            else:
                libtype_found = []
                for k in libtype_list:
                    if cls.cfg.has_option(dep_lang, '%s_%s' % (dep, k)):
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
                                       suffix=_system_suffix,
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
                out = []
                src = cls.internal_libraries[dep].get('source', None)
                if (src is not None) and os.path.isabs(src):
                    out.append(os.path.dirname(src))
            else:
                out = [out]
            out += cls.internal_libraries[dep].get('include_dirs', [])
        elif dep in cls.external_libraries:
            dep_lang = cls.external_libraries[dep].get('language', cls.language)
            out = cls.cfg.get(dep_lang, '%s_include' % dep, None)
            if os.path.isfile(out):
                out = os.path.dirname(out)
        elif os.path.isfile(dep):
            out = os.path.dirname(dep)
        if not out:
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
            tooltype = 'archiver'
        else:
            tooltype = 'linker'
        tool = cls.get_tool(tooltype)
        if tool is False:
            raise RuntimeError("No %s tool for language %s."
                               % (tooltype, cls.language))
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
        # Communication specific compilation flags
        if (for_model or for_api) and (not skip_interface_flags):
            for c in tools.get_installed_comm(language=cls.language):
                definitions.append('%sINSTALLED' % c[:3].upper())
                for x in cls.supported_comm_options.get(c, {}).get('libraries', []):
                    if x not in external_dependencies:
                        external_dependencies.append(x)
            if commtype is None:
                commtype = tools.get_default_comm()
            definitions.append('%sDEF' % commtype[:3].upper())
        # Add interface as internal_dependency for models and expand
        # dependencies to get entire chain including sub-dependencies and so on
        if for_model and (not skip_interface_flags):
            if (((cls.interface_library is not None)
                 and (cls.interface_library not in internal_dependencies))):
                internal_dependencies.append(cls.interface_library)
            for k in cls.get_external_libraries(no_comm_libs=True):
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
                    src, dont_link=True, suffix=_system_suffix))
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
        # Communication specific compilation flags
        if (for_model or for_api) and (not skip_interface_flags):
            for c in tools.get_installed_comm(language=cls.language):
                for x in cls.supported_comm_options.get(c, {}).get('libraries', []):
                    if x not in external_dependencies:
                        external_dependencies.append(x)
        # Add interface as internal_dependency for models
        if for_model and (not skip_interface_flags):
            if (((cls.interface_library is not None)
                 and (cls.interface_library not in internal_dependencies))):
                internal_dependencies.append(cls.interface_library)
            for k in cls.get_external_libraries(no_comm_libs=True):
                if (k not in external_dependencies) and cls.is_library_installed(k):
                    external_dependencies.append(k)
        # TODO: Expand library flags to include subdependencies?
        # Add flags for internal/external depenencies
        for dep in internal_dependencies + external_dependencies:
            dep_lib = cls.get_dependency_library(dep)
            if dep_lib and (dep_lib not in libraries):
                if not kwargs.get('dry_run', False):
                    if not os.path.isfile(dep_lib):  # pragma: debug
                        print('dep_lib', dep, dep_lib)
                    assert(os.path.isfile(dep_lib))
                if use_library_path_internal and (dep in internal_dependencies):
                    if kwargs.get('skip_library_libs', False):
                        if isinstance(use_library_path_internal, bool):
                            libkey = 'library_flags'
                        else:
                            libkey = use_library_path_internal
                    else:
                        libkey = 'flags'
                    kwargs.setdefault(libkey, [])
                    kwargs[libkey].append(dep_lib)
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
        compiler = cls.get_tool('compiler')
        if hasattr(compiler, 'language_version'):  # pragma: windows
            return compiler.language_version(**kwargs).strip()
        kwargs['version_flags'] = compiler.version_flags
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
            cfg = cls.cfg
        out = True
        if lib in cls.internal_libraries:
            src = cls.get_dependency_source(lib)
            return os.path.isfile(src)
        dep_lang = cls.external_libraries[lib].get('language', cls.language)
        for lib_typ in cls.external_libraries[lib].keys():
            if lib_typ in ['libtype', 'language']:
                continue
            if not out:  # pragma: no cover
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
        for k in cls.get_external_libraries():
            if not out:  # pragma: no cover
                break
            out = cls.is_library_installed(k)
        return out

    @classmethod
    def configure_executable_type(cls, cfg):
        r"""Add configuration options specific in the executable type
        before the libraries are configured.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        out = super(CompiledModelDriver, cls).configure_executable_type(cfg)
        compiler = None
        linker = None
        archiver = None
        for k in ['compiler', 'linker', 'archiver']:
            # Set default linker/archiver based on compiler
            default_tool_name = cfg.get(
                cls.language, k, getattr(cls, 'default_%s' % k, None))
            if (((default_tool_name is None) and (compiler is not None)
                 and (k in ['linker', 'archiver']))):
                default_tool_name = getattr(compiler, 'default_%s' % k, None)
            # Check default tool to make sure it is installed
            if default_tool_name:
                default_tool = get_compilation_tool(k, default_tool_name)
                if not default_tool.is_installed():  # pragma: debug
                    warnings.warn(('Default %s for %s (%s) not installed. '
                                   'Attempting to locate an alternative .')
                                  % (k, cls.language, default_tool_name))
                    default_tool_name = None
            # Determine compilation tools based on language/platform
            if default_tool_name is None:  # pragma: no cover
                default_tool_name = find_compilation_tool(k, cls.language,
                                                          allow_failure=True)
            # Set default tool attribute & record compiler tool if set
            setattr(cls, 'default_%s' % k, default_tool_name)
            if default_tool_name:
                cfg.set(cls.language, k, default_tool_name)
                if k == 'compiler':
                    compiler = get_compilation_tool(k, default_tool_name)
                elif k == 'linker':
                    linker = get_compilation_tool(k, default_tool_name)
                elif k == 'archiver':
                    archiver = get_compilation_tool(k, default_tool_name)
        # Check for missing library names
        for k, v in cls.external_libraries.items():
            libtype = v.get('libtype', None)
            if (libtype is not None) and (libtype not in v):  # pragma: no cover
                if (libtype == 'static') and (archiver is not None):
                    v[libtype] = archiver.get_output_file(k)
                elif (libtype == 'shared') and (linker is not None):
                    v[libtype] = linker.get_output_file(k, build_library=True)
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
        out = ModelDriver.configure_libraries.__func__(cls, cfg)
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
                else:  # pragma: no cover
                    desc_end = '%s %s' % (k, t)
                desc = 'The full path to the directory containing %s.' % desc_end
                if cfg.has_option(k_lang, opt):
                    continue
                if os.path.isabs(fname):
                    fpath = fname
                else:
                    fpath = os.path.join(os.getcwd(), fname)
                fname = os.path.basename(fpath)
                search_list = []
                if not os.path.isfile(fpath):
                    # Search the compiler/linker's search path, then the
                    # PATH environment variable.
                    tool = None
                    try:
                        if t in ['include']:
                            tool = cls.get_tool('compiler', default=None)
                        else:
                            tool = cls.get_tool('linker', default=None)
                    except NotImplementedError:  # pragma: debug
                        pass
                    fpath = None
                    if tool is not None:
                        search_list = tool.get_search_path()
                        if ((platform._is_win and fname.endswith('.lib')
                             and (not fname.startswith('lib')))):  # pragma: windows
                            fname = [fname, 'lib' + fname]
                        fpath = tools.locate_file(
                            fname, directory_list=search_list)
                if fpath:
                    logger.info('Located %s: %s' % (fname, fpath))
                    # if (t in ['static']) and platform._is_mac:
                    #     fpath_orig = fpath
                    #     fpath = '_s'.join(os.path.splitext(fpath))
                    #     logger.info('Using symbolic link: %s' % fpath)
                    #     if not os.path.isfile(fpath):
                    #         os.symlink(fpath_orig, fpath)
                    cfg.set(k_lang, opt, fpath)
                else:
                    logger.info('Could not locate %s (search_list = %s)'
                                % (fname, '\n\t'.join(search_list)))
                    out.append((k_lang, opt, desc))
        return out

    @classmethod
    def set_env_compiler(cls, compiler=None, **kwargs):
        r"""Get environment variables that should be set for the compilation
        process.

        Args:
            compiler (CompilerBase, optional): Compiler that set_env shoudl
                be called for. If not provided, the default compiler for
                this language will be used.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        if compiler is None:
            compiler = cls.get_tool('compiler')
        return compiler.set_env(**kwargs)

    def set_env(self, for_compile=False, compile_kwargs=None, **kwargs):
        r"""Get environment variables that should be set for the model process.

        Args:
            for_compile (bool, optional): If True, environment variables are set
                that are necessary for compiling. Defaults to False.
            compile_kwargs (dict, optional): Keyword arguments that should be
                passed to the compiler's set_env method. Defaults to empty dict.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CompiledModelDriver, self).set_env(**kwargs)
        if for_compile:
            if compile_kwargs is None:
                compile_kwargs = {}
            compiler = self.get_tool_instance('compiler')
            out = self.set_env_compiler(
                compiler=compiler, existing=out,
                logging_level=self.logger.getEffectiveLevel(),
                **compile_kwargs)
        return out
        
    @classmethod
    def compile_dependencies(cls, **kwargs):
        r"""Compile any required internal libraries, including the interface."""
        kwargs.setdefault('products', [])
        base_libraries = []
        for x in cls.base_languages:
            base_cls = import_component('model', x)
            base_libraries.append(base_cls.interface_library)
            base_cls.compile_dependencies(**kwargs)
        if (((cls.interface_library is not None) and cls.is_installed()
             and (cls.interface_library not in base_libraries))):
            # cls.call_compiler(cls.interface_library)
            dep_order = cls.get_dependency_order(cls.interface_library)
            for k in dep_order[::-1]:
                cls.call_compiler(k, **kwargs)

    @classmethod
    def cleanup_dependencies(cls, products=None, **kwargs):
        r"""Cleanup dependencies."""
        if products is None:
            products = []
        kwargs['dry_run'] = True
        cls.compile_dependencies(products=products, **kwargs)
        super(CompiledModelDriver, cls).cleanup_dependencies(products=products)

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
                              for_model=True,
                              env=self.set_env(for_compile=True),
                              skip_interface_flags=skip_interface_flags,
                              overwrite=self.overwrite,
                              working_dir=self.working_dir,
                              products=self.products)
        if not kwargs.get('dont_link', False):
            default_kwargs.update(linker_flags=self.linker_flags)
        for k, v in default_kwargs.items():
            kwargs.setdefault(k, v)
        return self.call_compiler(source_files, **kwargs)
    
    @classmethod
    def call_compiler(cls, src, language=None, dont_build=None, **kwargs):
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
            dont_build (bool, optional): If True, cmake configuration/generation
                will be run, but the project will not be built. Defaults to
                None. If provided, this overrides dont_link.
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
        if dont_build is not None:
            kwargs['dont_link'] = dont_build
        language = kwargs.pop('compiler_language', language)
        if 'env' not in kwargs:
            kwargs['env'] = cls.set_env_compiler()
        # Compile using another driver if the language dosn't match
        if (language is not None) and (language != cls.language):
            drv = import_component('model', language)
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
            return cls.call_compiler(src, suffix=_system_suffix,
                                     **kwargs)
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
            drv = import_component('model', language)
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
