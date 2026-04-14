import subprocess
import re
import os
import copy
import warnings
import shutil
import pprint
import tempfile
import contextlib
from yggdrasil import tools, platform, yamlfile
from yggdrasil.services import _service_repo_dir
from yggdrasil_rapidjson import NormalizationError
from yggdrasil.components import (
    ComponentBase, import_component, create_component, ComponentError,
    identify_component_subtype, get_component_classes)
git = None
try:
    import git
except ImportError:
    pass


_base_version_regex = r'(?P<ver>[\.\w\-\_\#]+)'
_min_version_regex = r'\>(?P<eq>\=)\s*' + _base_version_regex
_max_version_regex = r'\<(?P<eq>\=)\s*' + _base_version_regex
_strict_version_regex = r'(?P<eq>\=\=\s*)?' + _base_version_regex
_comp_version_regex = r'\s*(?:(?P<op>=?[\=\<\>]=?)\s*)?'
_version_part_regex_search = re.compile(
    _comp_version_regex + _base_version_regex
)
_version_part_regex = re.compile(
    r'(?:(?:^)|(?:\s*,))'
    + _comp_version_regex + _base_version_regex
)
_in_github_action = bool(os.environ.get('GITHUB_ACTIONS', False))
_default_always_yes = (
    _in_github_action or os.environ.get(_service_repo_dir, False)
)
_cached_results = {}
if platform._is_mac:
    _default_package_manager = ['conda', 'brew', 'apt', 'choco', 'vcpkg']
elif platform._is_linux:
    _default_package_manager = ['conda', 'apt', 'brew', 'choco', 'vcpkg']
elif platform._is_win:
    _default_package_manager = ['conda', 'choco', 'vcpkg', 'apt', 'brew']


class DependencyError(BaseException):
    r"""Class for dependency errors"""
    pass


class DependencyValidationError(DependencyError):
    r"""Class for validation error"""
    pass


class DependencyInstalledError(DependencyError):
    r"""Class for error raised when checking a package is installed"""
    pass


class DependencyUninstalledError(DependencyError):
    r"""Class for error raised when checking a package is uninstalled"""
    pass


class DependencySourceError(DependencyError):
    r"""Class for source code based error"""
    pass


class VersionParsingError(BaseException):
    r"""Class for errors in version parsing"""
    pass


def version_tuple(a):
    r"""Get a tuple containg the parts of a version string with numeric
    values converted to integers.

    Args:
        a (str, tuple, list): Version string or parts of a version
            string.

    Returns:
        tuple: Version parts.

    """
    if isinstance(a, str):
        a = tuple(a.split('.'))
    out = []
    for x in a:
        if x.isnumeric():
            out.append(int(x))
        else:
            out.append(x)
    return tuple(out)


def compare_versions(a, b, op='=='):
    r"""Compare two version strings.

    Args:
        a (str, tuple, list): Version string or parts of a version
            string.
        b (str, tuple, list): Version string or parts of a version
            string.
        op (str, optional): Operator to use for comparison.

    Returns:
        bool: True if the comparison is true, False otherwise.

    """
    a = list(version_tuple(a))
    b = list(version_tuple(b))
    if op == '==':
        new_len = min(len(a), len(b))
        b = b[:new_len]
        a = a[:new_len]
    if len(a) < len(b):
        a += (len(b) - len(a)) * [0]
    if len(a) > len(b):
        b += (len(a) - len(b)) * [0]
    for i in range(len(a)):
        if isinstance(a[i], str) and not isinstance(b[i], str):
            b[i] = str(b[i])
        elif isinstance(b[i], str) and not isinstance(a[i], str):
            a[i] = str(a[i])
        if isinstance(a[i], str):
            Na = 0
            Nb = 0
            while a[i][Na].isnumeric():
                Na += 1
            while b[i][Nb].isnumeric():
                Nb += 1
            pad = '0' * abs(Nb - Na)
            if Na < Nb:
                a[i] = pad + a[i]
            else:
                b[i] = pad + b[i]
            Na = len(a[i])
            Nb = len(b[i])
            pad = '0' * abs(Nb - Na)
            if Na < Nb:
                a[i] += pad
            else:
                b[i] += pad
    a = tuple(a)
    b = tuple(b)
    if op == '=>':
        op = '>='
    return eval(f'(a {op} b)')


def parse_version_string(version, pos=0, endswith=False):
    r"""Parse a version constraint string.

    Args:
        version (str): Version constraint string (e.g '1.2', '<1.2',
            '>=1.2'). More than one constraint can be specified with a
            comma separator. (e.g. '>= 1.12.0, < 1.14')
        pos (int, optional): Position to begin matching version at.
        endswith (bool, optional): If True, the version components of the
            input string may start after the first character.

    Returns:
        dict: Version components. Possible fields include:
            min  : Minimum version specified with '<'
            mineq: True if minimum is inclusive (i.e. '<=' is used)
            max  : Maximum version specified with '>'
            maxeq: True if maximum is inclusive (i.e. '>=' is used)
            ver  : Pinned version that is not minimum or maximum
            vereq: True if ver value is strict (i.e. '==' is used)

    """
    if isinstance(version, str):
        version = version.strip()
    if not version:
        return {}
    out = {'constraints': []}
    pos_orig = pos
    while pos < len(version):
        is_relative = False
        if endswith and pos == pos_orig:
            match = _version_part_regex_search.search(version, pos)
        else:
            match = _version_part_regex.match(version, pos)
            if pos > 0 and pos == pos_orig and not match:
                match_2 = _version_part_regex.match(version[pos:])
                if match_2:
                    match = match_2
                    is_relative = True
        if not match:
            raise VersionParsingError(
                f"Version does not match expected pattern: "
                f"\"{version}\" (mismatch occurs at "
                f"position {pos})")
        if pos_orig > 0 and 'start' not in out:
            out['start'] = match.start()
            if is_relative:
                out['start'] += pos
        val = match.groupdict()
        if match.group('op') and '<' in match.group('op'):
            dst = 'max'
        elif match.group('op') and '>' in match.group('op'):
            dst = 'min'
        else:
            dst = 'strict'
            val['op'] = '=='
        for x in out['constraints']:
            if x['op'] != '==' or x['op'] == val['op']:
                if not compare_versions(val['ver'], x['ver'], x['op']):
                    raise VersionParsingError(
                        f"Constraints '{val['op']}{val['ver']}' and "
                        f"'{x['op']}{x['ver']}' conflict")
            if val['op'] != '==' or x['op'] == val['op']:
                if not compare_versions(x['ver'], val['ver'], val['op']):
                    raise VersionParsingError(
                        f"Constraints '{val['op']}{val['ver']}' and "
                        f"'{x['op']}{x['ver']}' conflict")
        if not (dst in out or 'strict' in out):
            if dst == 'strict':
                out['constraints'] = []
                for k in ['min', 'max']:
                    out.pop(k, None)
                    out.pop(f'{k}eq', None)
            out['constraints'].append(val)
            out[dst] = val['ver']
            out[f'{dst}eq'] = bool(match.group('op')
                                   and ('=' in match.group('op')))
        if is_relative:
            pos += match.end()
        else:
            pos = match.end()
    return out


class ErrorRegistry(object):
    r"""Registry for catching and accumulating errors.

    Args:
        error_types (type, tuple): One or more error types that should be
            registered.
        final_error (type, optional): Type of error that should be raised
            raised when the context exits if errors were registered. If
            False, no error will be raised. Defaults to False if registry
            is provided and the first error in error_types otherwise.
        error_prefix (str, optional): Prefix that should be added to
            the final error raised with all accumulated errors.
        error_count (int, optional): Minimum number of errors that
            need to be registered for the final error to be raised when
            the context exits.
        registry (list, optional): Existing list that errors should be
            appended to when they are registered.
        print_accumulated (bool, optional): If True, print the registered
            errors when the instance is finalized.

    """

    def __init__(self, error_types, final_error=None,
                 error_prefix='Accumulated errors: ', error_count=1,
                 registry=None, print_accumulated=False):
        if isinstance(error_types, type):
            error_types = (error_types, )
        elif isinstance(error_types, list):
            error_types = tuple(error_types)
        if isinstance(final_error, str):
            error_prefix = final_error
            final_error = None
        if final_error is None:
            if registry is None and not print_accumulated:
                final_error = error_types[0]
            else:
                final_error = False
        if registry is None:
            registry = []
        self.error_types = error_types
        self.registry = registry
        self.final_error = final_error
        self.error_prefix = error_prefix
        self.error_count = error_count
        self.print_accumulated = print_accumulated
        self.active = False

    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, ext, exv, trb):
        # if ext:
        #     print("ERROR REGISTRY")
        #     print(ext, type(ext), ext in self.error_types)
        #     print(exv, type(exv), isinstance(exv, self.error_types))
        #     import pdb; pdb.set_trace()
        self.active = False
        out = None
        if ext and ext in self.error_types:
            self.registry.append(exv)
            out = True
            ext = None
        return out

    @classmethod
    def format_errors(cls, prefix, errors):
        r"""Format a list of errors.

        Args:
            prefix (str): Error prefix.
            errors (list): List of errors.

        Returns:
            str: Formated error message.

        """
        error_list = []
        for x in errors:
            x = str(x).splitlines()
            error_list += [f'- {x[0]}']
            error_list += [f' {xx}' for xx in x[1:]]
        sep = '\n    '
        return prefix + sep + sep.join(error_list)

    def finalize(self):
        r"""Finalize the registry, raising the final error if
        appropriate.

        Returns:
            list, BaseException: Registered errors if final_error not set
                or the number of registered errors does not exceed
                error_count. Otherwise, the final error is returned.

        """
        message = self.format_errors(self.error_prefix, self.registry)
        if self.print_accumulated:
            print(message)
        if not (self.final_error
                and len(self.registry) >= self.error_count):
            return self.registry
        return self.final_error(message)


class ErrorRegistrySet(object):
    r"""Set of registries for catching and accumulating errors."""

    def __init__(self):
        self.registries = []

    def accumulate_error(self, error, message=None, dont_raise=False):
        r"""Add an error to the most recent matching registry or raise
        it.

        Args:
            error (BaseException): Error instance or error class. If a
                class is provided, message must be as well.
            message (str, optional): Error message used to create error
                instance from class passed via error.
            dont_raise (bool, optional): If True, don't raise the error
                if it does not match any of the current registries.

        Returns:
            bool: True if the error was registered, False otherwise.

        """
        if isinstance(error, type):
            error = error(message)
        for x in self.registries[::-1]:
            if isinstance(error, x.error_types):
                x.registry.append(error)
                return True
        if not dont_raise:
            raise error
        return False

    @contextlib.contextmanager
    def accumulate(self, *args, **kwargs):
        r"""Context manager to accumulate errors to any of the registries
        in this set.

        Args:
            *args: Arguments are used to create a new registry. If
                provided, the created registry will be removed and
                finalized when the context exits.
            **kwargs: Additional keyword arguments are passed to append
                only if args are provided.

        Returns:
            list: Registered errors if args provided to create a new
                registry.
        
        """
        out = None
        if args:
            self.append(*args, **kwargs)
        with contextlib.ExitStack() as stack:
            for x in self.registries:
                if not x.active:
                    stack.enter_context(x)
            try:
                yield
            except BaseException as e:
                if not self.accumulate_error(e, dont_raise=True):
                    raise
        if args:
            out = self.pop()
        return out

    def append(self, *args, **kwargs):
        r"""Begin registering errors.

        Args:
            *args: All arguments are passed to the ErrorRegistry
                 constructor.
            **kwargs: All keyword arguments are passed to the
                 ErrorRegistry constructor.

        """
        self.registries.append(ErrorRegistry(*args, **kwargs))

    def pop(self):
        r"""Remove and return the last registry added.

        Returns:
            list: List of error registered.

        """
        out = self.registries.pop().finalize()
        if isinstance(out, BaseException):
            self.accumulate_error(out)
            out = None
        return out


class ManagedDependencyBase(ComponentBase):
    r"""Base class for managed dependencies.

    Args:
        package (str): Name of the package that should be installed. If
            the package manager supports it, this can include version
            requirements.
        package_manager (str, optional): Package manager that should be
            used to install the package.
        version (str, optional): Version of the package that should
            be installed. This string can begin with '==', '<', '<=',
            '>', or '>=' to indicate the type of contraint on the version
            installed. If none of these are present, it will be assumed to
            be a strict version requirement (i.e. ==version).
        arguments (str, optional): Additional arguments that should be
            passed to the package manager during installation.
        arguments_uninstall (str, optional): Additional arguments that
            should be passed to the package manager during uninstall.
        command_kwargs (dict, optional): Keyword arguments that should
            be passed to the subprocess call for the installation.
        pre_install_steps (list, optional): Additional commands that
            should be executed before install in order to install the
            package.
        post_install_steps (list, optional): Additional commands that
            should be executed in order to install the package.
        pre_uninstall_steps (list, optional): Additional commands that
            should be executed before uninstall in order to uninstall the
            package.
        post_uninstall_steps (list, optional): Additional commands
            that should be executed in order to uninstall the package.
        operating_systems (list, optional): Operating systems that the
            dependency is valid for.
        conda_env (str, optional): Conda environment where the dependency
            should be installed.
        products (list, optional): Files that are required for the
            dependency to be considered installed.
        sourcedir (str, optional): Directory containing package source
            code that the package should be installed from.

    Class Attributes:
        args_yes (list): Arguments added to an installation command so
            that user input is not required.
        args_prefix (list): Arguments added after the executable to every
            command.
        args_prefix_install (list): Arguments added to an installation
            command after the executable, but before the package name.
        args_suffix_install (list): Arguments added to an installation
            command after the package name.
        args_prefix_uninstall (list): Arguments added to an
            uninstallation command after the executable, but before the
            package name.
        args_suffix_uninstall (list): Arguments added to an
            uninstallation command after the package name.
        args_prefix_list (list): Arguments added to a list command after
            the executable.
        args_prefix_search (list): Arguments added to a search command
            after the executable, but before the package name.
        quoted_names (bool): If True, packages should be quoted in the
            installation command.
        ignore_properties_appendable (list): Properties that should not
            be compared with determining if two dependencies can be
            installed together.
        constraint_fstring (str): Format string that should be used for
            version constraints.
        versioned_fstring (str): Format string that should be used for
            formatting constrained package names.
        constraint_sep (str): Separator that should be used to join
            individual version constraints.
        list_field_names (list): Names for columns in the output from a
            list command.
        affected_by_conda_env (bool): If True, the package manager is
            affected by the conda_env used.
        manager_executable_name (str): Base name for executable if
            different than package_manager name.
        double_check_install (bool): If True, the installation should
            be checked after install/uninstall because the command
            error may not get picked up by subprocess.
        installable_from_source (bool): If True, the package manager
            can be used to install a package from the source code. If a
            list, a directory will be labeled a source directory for the
            package manager if the directory contains any of the
            elements. If any of the elements is a set, the directory will
            be labeled a source directory if it contains all of the paths
            in the set.
        language_specific (str): Name of the language that the package
            manager is specific to. False if the package manager is
            language agnostic.

    """

    _package_manager = None
    _schema_subtypes_in_single_file = True
    _schema_type = 'dependency'
    _schema_subtype_key = 'package_manager'
    _schema_properties = {
        'package': {'type': 'string'},
        'version': {'type': 'string'},
        'arguments': {
            'type': 'array',
            'items': {'type': 'string'},
        },
        'arguments_uninstall': {
            'type': 'array',
            'items': {'type': 'string'},
        },
        'command_kwargs': {
            'type': 'object',
            'properties': {
                'shell': {
                    'type': 'boolean',
                    'default': False
                },
            },
            'additionalProperties': True,
        },
        'pre_install_steps': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'post_install_steps': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'pre_uninstall_steps': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'post_uninstall_steps': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'operating_systems': {
            'type': 'array',
            'items': {
                'type': 'string',
                'enum': ['windows', 'macos', 'linux', 'unix'],
            }
        },
        'products': {
            'type': 'array',
            'items': {'type': 'string'},
        },
    }
    _schema_required = ['package']
    _schema_additional_kwargs = {
        'allowSingular': 'package',
    }
    args_yes = []
    args_prefix = []
    args_prefix_install = []
    args_suffix_install = []
    args_prefix_uninstall = []
    args_suffix_uninstall = []
    args_prefix_list = []
    args_prefix_search = []
    quoted_names = False
    ignore_properties_appendable = ['package']
    constraint_fstring = '{op}{ver}'
    versioned_fstring = '{package}{ver}'
    constraint_sep = ', '
    list_field_names = None
    affected_by_conda_env = False
    manager_executable_name = None
    double_check_install = False
    installable_from_source = False
    manager_conda_package = None
    language_specific = False
    _install_manager_called = {}

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration. These actions will still be performed if the environment
        variable YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        if cls.affected_by_conda_env:
            cls._schema_properties['conda_env'] = {'type': 'string'}
        if ((cls.installable_from_source
             and 'sourcedir' not in cls._schema_properties
             and 'directory' not in cls._schema_properties)):
            cls._schema_properties['sourcedir'] = {'type': 'string'}

    def __init__(self, package=None, **kwargs):
        if package is not None:
            kwargs['package'] = package
        super(ManagedDependencyBase, self).__init__(**kwargs)
        for k in ['pre_install_steps', 'post_install_steps',
                  'pre_uninstall_steps', 'post_uninstall_steps',
                  'products']:
            if not getattr(self, k, None):
                setattr(self, k, [])
        self.additional_packages = []
        if not self.command_kwargs:
            self.command_kwargs = {}
        if not self.affected_by_conda_env:
            self.conda_env = None
        self.conda_prefix = tools.get_conda_prefix(self.conda_env)
        if self.conda_env and not self.conda_prefix:
            raise DependencyError('conda_env set, but conda could '
                                  'not be located')
        self._error_registries = ErrorRegistrySet()
        self._version_parts = None
        self._install_called = False
        if self.package:
            idx = len(self.package)
            for x in ['=', '<', '>']:
                if x in self.package:
                    idx = min(self.package.index(x), idx)
            if idx < len(self.package):
                new_match = parse_version_string(self.package, pos=idx)
                new_version = self.package[new_match['start']:]
                if new_version.strip():
                    self.package = self.package[:new_match['start']]
                    if self.version and new_version != self.version:
                        raise DependencyError(
                            f'Version in package name '
                            f'"{new_version}" conflicts '
                            f'with explicit version '
                            f'property "{self.version}"')
                    self.version = new_version

    def __str__(self):
        return f'{self.versioned_package}[{self._package_manager}]'

    @classmethod
    def select_installed(cls, managers):
        r"""Select the first installed manager from the provided list of
        values. If none of the managers are installed, the first one will
        be returned.

        Args:
            managers (list): List of package managers.

        Returns:
            str: First installed manager.

        """
        if isinstance(managers, str):
            return managers
        if len(managers) == 1:
            return managers[0]
        for x in managers:
            xcls = import_component('dependency', x)
            if xcls.manager_installed():
                return x
        return managers[0]

    @classmethod
    def create_component(cls, package=None, default_package_manager=None,
                         **kwargs):
        r"""Create a dependency component instance.

        Args:
            package (str, optional): Name of the package that should be
                installed. If the package manager supports it, this can
                include version requirements or version can be specified
                as a separate keyword argument.
            default_package_manager (str, list, optional): Package
                manager(s) that should be used to install the package if
                the package_manager property is not set and one cannot
                be determined from the provided properties. If a list is
                provided, the first package_manager that is installed
                will be used. If not provided, the default order will be
                based on the operating system:
                    macos  : ['conda', 'brew', 'apt', 'choco', 'vcpkg']
                    linux  : ['conda', 'apt', 'brew', 'choco', 'vcpkg']
                    windows: ['conda', 'choco', 'vcpkg', 'apt', 'brew']
            **kwargs: Additional keyword arguments are passed to the
                class constructor.
        
        Returns:
            ManagedDependencyBase: Dependency instance.

        """
        if default_package_manager is None:
            default_package_manager = _default_package_manager
        if default_package_manager is not None:
            default_package_manager = cls.select_installed(
                default_package_manager)
        if isinstance(package, str):
            package = package.split()
        if isinstance(package, list):
            if len(package) != 1:
                if default_package_manager:
                    kwargs.setdefault('default_package_manager',
                                      default_package_manager)
                if kwargs.get('package_manager', None) == 'options':
                    return DependencyOptions(options=package, **kwargs)
                return DependencySet(members=package, **kwargs)
            package = package[0]
        if isinstance(package, dict):
            kwargs.update(package)
            package = None
        if package is not None:
            kwargs['package'] = package
        if ((default_package_manager
             and not kwargs.get('package_manager', None)
             and any(k not in ManagedDependencyBase._schema_properties.keys()
                     for k in kwargs.keys()))):
            try:
                kwargs['package_manager'] = identify_component_subtype(
                    'dependency', kwargs)
            except ComponentError:
                pass
        if ((default_package_manager
             and not kwargs.get('package_manager', None))):
            kwargs['package_manager'] = default_package_manager
        if ((default_package_manager
             and kwargs['package_manager'] in ['set', 'options'])):
            kwargs['default_package_manager'] = default_package_manager
        return create_component('dependency', **kwargs)

    @classmethod
    def manager_executable(cls, conda_env=None, alternate_name=None):
        r"""Executable used for installation command.

        Args:
            conda_env (str, optional): Conda environment that executable
                should come from.
            alternate_name (str, optional): Alternate executable that
                should be used.

        Returns:
            str: Path to the installation executable.
        
        """
        if alternate_name is not None:
            name = alternate_name
        elif cls.manager_executable_name:
            name = cls.manager_executable_name
        else:
            name = cls._package_manager
        if cls.affected_by_conda_env and conda_env:
            # Check for executable in the desired conda environment
            # first, but allow for another executable on PATH (e.g.
            # system installation to be returned as long as it is not in
            # another conda environment
            # TODO: This is different on windows
            out = os.path.join(tools.get_conda_prefix(conda_env),
                               'bin', name)
            if not os.path.isfile(out):
                default = shutil.which(name)
                if default and not default.startswith(tools.get_conda_root()):
                    return default
            return out
        return name

    @classmethod
    def manager_not_yet_installed(cls, conda_env=None):
        r"""Check if the manager has not yet been installed, but can be.

        Args:
            conda_env (str, optional): Conda environment that executable
                should come from.

        Returns:
            bool: True if the package manager is not installed, but can
                be.

        """
        if not cls.manager_conda_package:
            return False
        return (not cls.manager_installed(conda_env=conda_env,
                                          dont_allow_conda_install=True))

    @classmethod
    def manager_installed(cls, conda_env=None,
                          dont_allow_conda_install=False):
        r"""Determine if the package manager is installed.

        Args:
            conda_env (str, optional): Conda environment that executable
                should come from.
            dont_allow_conda_install (bool, optional): If False and
                the manager can be installed via conda, the result will
                be True even if the manager is not currently installed.

        Returns:
            bool: True if the package manager is installed.

        """
        if (((not dont_allow_conda_install) and cls.manager_conda_package
             and os.environ.get('CONDA_PREFIX', None))):
            return True
        out = bool(shutil.which(cls.manager_executable(
            conda_env=conda_env)))
        return out

    def install_manager(self, always_yes=_default_always_yes):
        r"""Install the manager package.

        Args:
            always_yes (bool, optional): If True, the installation
                will not ask for user confirmation. Defaults to False.

        """
        if not self.manager_conda_package:
            return
        if self.manager_installed(conda_env=self.conda_env,
                                  dont_allow_conda_install=True):
            return
        kws = {'package': self.manager_conda_package}
        if self.conda_env:
            kws['conda_env'] = self.conda_env
        dep = CondaDependency(**kws)
        dep.install(always_yes=always_yes)

    @classmethod
    def is_source_dir(cls, directory):
        r"""Determine if a source directory contains a package that
        can be installed by this package manager.

        Args:
            directory (str): Directory to check.

        """
        if not cls.installable_from_source:
            return False
        if isinstance(cls.installable_from_source, list):
            for x in cls.installable_from_source:
                if isinstance(x, str):
                    if os.path.exists(os.path.join(directory, x)):
                        return True
                elif isinstance(x, set):
                    if all(os.path.exists(os.path.join(directory, xx))
                           for xx in x):
                        return True
        return False

    @classmethod
    def command_prefix(cls, uninstall=False, conda_env=None):
        r"""Prefix arguments for installation commands.

        Args:
            uninstall (bool, optional): If True, get the prefix for
                uninstallation.
            conda_env (str, optional): Conda environment that executable
                should come from.

        Returns:
            list: Prefix arguments.
        
        """
        out = [cls.manager_executable()] + cls.args_prefix
        if uninstall:
            out += cls.args_prefix_uninstall
        else:
            out += cls.args_prefix_install
        return out

    @contextlib.contextmanager
    def error_accumulator(self, *args, **kwargs):
        r"""If an exception is raised within this context that matches
        any of the error registries, it will be registered instead of
        raised.

        Args:
            *args: All arguments are passed to the accumulate method of
                the _error_registries attribute.
            **kwargs: All keyword arguments are passed to the accumulate
                method of the _error_registries attribute.

        """
        with self._error_registries.accumulate(*args, **kwargs):
            yield
        
    def accumulate_error(self, *args, **kwargs):
        r"""Raise an exception that can be accumulated instead of being
        raised if an appriate error registry has been set up.

        Args:
            *args: All arguments are passed to the accumulate_error
                method of the _error_registries attribute.
            **kwargs: All keyword arguments are passed to the
                accumulate_error method of the _error_registries
                attribute.

        Returns:
            bool: True if the error was registered, False otherwise.

        """
        return self._error_registries.accumulate_error(*args, **kwargs)
        
    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        if self.operating_systems:
            if not (platform._platform.lower() in self.operating_systems
                    or (platform._platform.lower() in ['macos', 'linux']
                        and 'unix' in self.operating_systems)):
                self.accumulate_error(
                    DependencyValidationError,
                    f'Platform "{platform._platform.lower()}" is '
                    f'not one of the enumerated options specified '
                    f'by operating_systems '
                    f'({self.operating_systems})'
                )
        if self.conda_env and not os.path.isdir(self.conda_prefix):
            self.accumulate_error(
                DependencyValidationError,
                f'Conda env "{self.conda_env}" does not exist at prefix '
                f'"{self.conda_prefix}"'
            )
        if not self.manager_installed(conda_env=self.conda_env):
            self.accumulate_error(
                DependencyValidationError,
                f'Manager executable "'
                f'{self.manager_executable(conda_env=self.conda_env)}" '
                f'is not installed or is not on the current path'
            )

    def check_installed(self, **kwargs):
        r"""Check if the dependency is installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            DependencyInstalledError: If the dependency is not installed.

        """
        with self.error_accumulator(
                DependencyValidationError,
                DependencyInstalledError,
                f'Dependency {self.package} is not valid:'):
            self.check_validity()
        try:
            info = self.search()
        except DependencyError as e:
            self.accumulate_error(
                DependencyInstalledError,
                f'Search for {self.package} failed: {e}'
            )
            info = None
        for x in self.additional_packages:
            x.check_installed(**kwargs)
        for x in self.products:
            if not os.path.exists(x):
                self.accumulate_error(
                    DependencyInstalledError,
                    f'Product \'{x}\' does not exist'
                )
        return info

    def check_uninstalled(self, **kwargs):
        r"""Check if the dependency is uninstalled.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            DependencyUninstalledError: If the dependency is not
                uninstalled.

        """
        for x in self.products:
            if os.path.exists(x):
                self.accumulate_error(
                    DependencyUninstalledError,
                    f'Product \'{x}\' exists'
                )
        for x in self.additional_packages:
            x.check_uninstalled()
        if self.is_installed:
            self.accumulate_error(
                DependencyUninstalledError,
                f'Package \'{self.package}\' installed'
            )

    @property
    def is_valid(self):
        r"""bool: True if the dependency can be installed."""
        try:
            self.check_validity()
            return True
        except DependencyValidationError:
            return False

    @property
    def is_installed(self):
        r"""bool: True if the dependency has already been installed."""
        try:
            return self.check_installed()
        except DependencyInstalledError:
            return False

    @property
    def is_uninstalled(self):
        r"""bool: True if the dependency has been uninstalled."""
        try:
            self.check_uninstalled()
            return True
        except DependencyUninstalledError:
            return False

    @classmethod
    def parse_list(cls, contents, field_names=None):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.
            field_names (list, optional): List of field names for columns
                in contents.

        Returns:
           list: List of package information in dictionaries.

        """
        if field_names is None:
            field_names = cls.list_field_names
        if field_names is None:
            raise NotImplementedError(f'{cls}.parse_list. Cannot parse'
                                      f'\n===={contents}\n====')
        out = []
        for x in contents.splitlines():
            x = x.strip()
            if not x:
                continue
            out.append(
                {k: v.strip() for k, v in zip(field_names, x.split())}
            )
        return out

    @classmethod
    def list(cls, package=None, invalidate_cache=False, conda_env=None,
             **kwargs):
        r"""List the packages installed by this package manager.

        Args:
            package (str, optional): Name of package to restrict list to.
            invalidate_cache (bool, optional): If True, invalidate any
                existing cached list and generate a new one. If False,
                use any existing cached result.
            conda_env (str, optional): Conda environment that executable
                should come from.
            **kwargs: Additional keyword arguments are passed to
                parse_list.

        Returns:
            list: List of package information in dictionaries.

        """
        if not (cls.args_prefix_list
                or (package and cls.args_prefix_search)):
            raise DependencyError(f"No command for listing "
                                  f"\"{cls._package_manager}\" packages")
        if cls.manager_not_yet_installed(conda_env=conda_env):
            return []
        cmd = [cls.manager_executable()] + cls.args_prefix
        if package and cls.args_prefix_search:
            cmd += cls.args_prefix_search + [package]
        else:
            cmd += cls.args_prefix_list
        out = cls.run_command_class(
            cmd, context='check', package=package, return_output=True,
            invalidate_cache=invalidate_cache, conda_env=conda_env,
        ).decode('utf-8')
        return cls.parse_list(out, **kwargs)

    @classmethod
    def compare_versions(cls, a, b, **kwargs):
        r"""Compare two version strings.

        Args:
            a (str, tuple, list): Version string or parts of a version
                string.
            b (str, tuple, list): Version string or parts of a version
                string.
            **kwargs: Additional keyword arguments are passed to
                compare_versions.
        
        Returns:
            bool: True if the comparison is true, False otherwise.

        """
        return compare_versions(a, b, **kwargs)

    @classmethod
    def ask_user(cls, message):  # pragma: user input
        r"""Ask for the user to answer a yes or no question.

        Args:
            message (str): Message containing the question to pose to the
                user.

        Returns:
            bool: True if the response was yes, False if the response
                was no.

        """
        options_yes = ['yes', 'y']
        options_no = ['no', 'n', '']
        options = options_yes + options_no
        while True:
            check = input(f'{message} [y/N]: ')
            if check.lower() in options:
                break
            print(f"Invalid selection '{check}'.")
        return (check.lower() in options_yes)

    def check_version(self, version, base_version=None, **kwargs):
        r"""Check if a version string satisfies the version constraints.

        Args:
            version (str): Version string to check against constraints.
            base_version (str, optional): Alternate version string that
                version should be compared against for equality.
            **kwargs: Additional keyword arguments are passed to
                compare_versions.

        Returns:
            bool: True if version satisfies the constraints, False
                otherwise.

        """
        if not (self.version and version):
            return True
        if base_version:
            return self.compare_versions(version, base_version,
                                         op='==', **kwargs)
        for x in self.version_constraints:
            if not self.compare_versions(version, x['ver'],
                                         op=x['op'], **kwargs):
                return False
        return True

    def search(self, package=None, version=None, package_list=None,
               **kwargs):
        r"""Search for the current version of the dependency if one
        exists.

        Args:
            package (str, optional): Package to search for. Defaults to
                this dependency.
            version (str, optional): Package to search for. Defautls to
                this dependency's version (unless package specified).
            package_list (list, optional): List of packages that should
                be used instead of the output from list method.
            **kwargs: Additional keyword arguments are passed to list.

        Raises:
            DependencyError: If the package is not installed.

        Returns:
            dict: Parameters of package.

        """
        if package is None:
            package = self.package
        if version is None and package != self.package:
            version = False
        if package_list is None:
            kwargs.setdefault('conda_env', self.conda_env)
            package_list = self.list(package=package, **kwargs)
        for x in package_list:
            if 'name' not in x:
                raise RuntimeError(f'{self}: Invalid package from list: {x}')
            if ((x['name'].lower() == package.lower()
                 and self.check_version(x.get('version', None),
                                        base_version=version))):
                return x
        raise DependencyError(f'Could not locate dependency '
                              f'"{self.package}" within package list:\n'
                              f"{pprint.pformat(package_list)}")

    def alternate_manager_properties(self, manager, kwargs=None,
                                     include=None, exclude=None):
        r"""Get the properties for an alternate package manager.

        Args:
            manager (ManagedDependencyBase): Class that kwargs should be
                catered to.
            kwargs (dict, optional): Additional keyword arguments that
                should be added to the returned dictionary, overriding
                any values from this instance.
            include (list, optional): Properties that should be included.
            exclude (list, optional): Properties that should be excluded.

        Returns:
            dict: Update kwargs.

        """
        if kwargs is None:
            kwargs = {}
        for k in manager._schema_properties.keys():
            if include and k not in include:
                continue
            if exclude and k in exclude:
                continue
            if k in self._properties_set:
                kwargs.setdefault(k, getattr(self, k))
        return kwargs

    def alternate_manager_instance(self, manager, *args, **kwargs):
        r"""Get an instance for an alternate package manager.

        Args:
            manager (ManagedDependencyBase): Class that kwargs should be
                catered to.
            *args, **kwargs: Additional arguments are passed to
                alternate_manager_properties.

        Returns:
            dict: Update kwargs.

        """
        props = self.alternate_manager_properties(manager, *args, **kwargs)
        for k in manager._schema_required:
            if k not in props:
                raise NormalizationError(f"Missing required property {k}")
        return manager(**props)

    def is_installed_by_other(self, include=None, exclude=None, **kwargs):
        r"""Check if package is installed by another package manager.

        Args:
            include (str, list, optional): Package manager(s) to
                check. If not provided, all installed package managers
                will be checked.
            exclude (str, list, optional): Package manager(s) to exclude
                from check.
            **kwargs: Additional keyword arguments are used as inputs
                to the other package manager constructors.

        Returns:
            ManagedDependencyBase: Alternate instance of the package
                installed by another package manager if the package is
                installed, False otherwise.

        """
        if include is None:
            include = get_component_classes('dependency')
        if isinstance(exclude, str):
            exclude = [exclude]
        if isinstance(include, list):
            for x in include:
                x_inst = self.is_installed_by_other(
                    x, exclude=exclude, **kwargs)
                if x_inst:
                    return x_inst
            return False
        x = include
        if not isinstance(x, type):
            x = import_component('dependency', x)
        if x._package_manager == self._package_manager:
            return False
        if exclude and x._package_manager in exclude:
            return False
        if x._schema_required != ['package']:
            return False
        if ((self.language_specific and x.language_specific
             and self.language_specific != x.language_specific)):
            return False
        try:
            x_inst = self.alternate_manager_instance(
                x, kwargs, include=['package', 'conda_env'])
        except NormalizationError:
            return False
        x_is_installed = x_inst.is_installed
        if x_is_installed:
            x_is_installed['package_manager'] = x._package_manager
            return x_inst
        return False

    @property
    def source_directory(self):
        r"""str: Directory containing the package source code if
         available."""
        if not self.installable_from_source:
            return None
        return getattr(self, 'sourcedir', getattr(self, 'directory', None))
        
    def is_appendable(self, solf):
        r"""Determine if this dependency can be installed at the same
        time as another dependency.

        Args:
            solf (ManagedDependencyBase): Dependency to compare against.

        Returns:
            bool: True if solf can be appended to this dependency, False
                otherwise.

        """
        if self._package_manager != solf._package_manager:
            return False
        if self.source_directory or solf.source_directory:
            return False
        for k in self._schema_properties.keys():
            if k in self._schema_excluded_from_class:
                continue
            if k in self.ignore_properties_appendable:
                continue
            if getattr(self, k, None) != getattr(solf, k, None):
                return False
        return True

    def init_child(self, solf, **kwargs):
        r"""Initialize a child dependency that may be added as an
        additional package.

        Args:
            solf (ManagedDependencyBase, dict): Dependency or dependency
                properties from which a child dependency should be
                created.
            **kwargs: Additional keyword arguments are passed to the
                create_component class method.

        Returns:
            ManagedDependencyBase: Updated/created child dependency.

        """
        if not isinstance(solf, ManagedDependencyBase):
            if 'package' in kwargs:
                if isinstance(solf, dict):
                    solf.setdefault('package', kwargs['package'])
                kwargs.pop('package')
            solf = self.create_component(solf, **kwargs)
        return solf

    def append(self, solf):
        r"""Add a dependency to the set of additional packages that will
        be installed at the same time as this one.

        Args:
            solf (ManagedDependencyBase): Dependency to append.

        Raises:
            DependencyError: If solf cannot be appended to this
                dependency.

        """
        solf = self.init_child(solf)
        assert isinstance(solf, ManagedDependencyBase)
        if isinstance(solf, DependencySet):
            for x in solf.members:
                self.append(x)
            return
        if not self.is_appendable(solf):
            raise DependencyError(f"Dependency ({solf}) cannot be "
                                  f"appended to this one ({self})")
        self.additional_packages.append(solf)
        self.additional_packages += solf.additional_packages
        solf.additional_packages = []

    @property
    def version_parts(self):
        r"""dict: Parts of parsed version string."""
        if self._version_parts is None:
            self._version_parts = parse_version_string(self.version)
        return self._version_parts

    @property
    def version_constraints(self):
        r"""list: Set of version constraints"""
        return self.version_parts.get('constraints', [])

    def format_constraint(self, ver=None, op=None):
        r"""Format a version constraint.

        Args:
            ver (str): Version number.
            op (str, optional): Version constraint operator.

        Returns:
            str: Formatted version constraint.

        """
        assert ver
        if not op:
            return ver
        return self.constraint_fstring.format(ver=ver, op=op)

    @property
    def formatted_version(self):
        r"""str: Version string with constraints indicators"""
        return self.constraint_sep.join(
            self.format_constraint(**x) for x in
            self.version_constraints)

    @property
    def version_max(self):
        parts = self.version_parts
        if 'strict' in parts:
            return parts['strict']
        if 'max' in parts:
            if parts.get('maxeq'):
                return parts['max']
            # TODO: Find next largest version?
            # else:
        return None

    @property
    def versioned_package(self):
        r"""str: Package name with version constraints"""
        out = self.package
        assert out
        ver = self.formatted_version
        if ver and self.versioned_fstring:
            out = self.versioned_fstring.format(package=out, ver=ver)
        if self.quoted_names:
            out = f"\"{out}\""
        return out
        
    def install_command(self, always_yes=_default_always_yes):
        r"""Get the command arguments for installing the package.

        Args:
            always_yes (bool, optional): If True, the installation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        out = self.command_prefix(conda_env=self.conda_env)
        if always_yes and self.args_yes:
            out += self.args_yes
        sourcedir = self.source_directory
        if sourcedir:
            out += [sourcedir]
        else:
            out += [self.versioned_package]
        out += [x.versioned_package for x in self.additional_packages]
        out += self.args_suffix_install
        if self.arguments:
            out += self.arguments
        return out

    def _install(self, **kwargs):
        cmd = self.install_command(**kwargs)
        self.run_command(cmd, context='install')
        self._install_called = True

    def install(self, always_yes=_default_always_yes, force=False):
        r"""Install the dependency.

        Args:
            always_yes (bool, optional): If True, the installation will
                not ask for user confirmation. Defaults to False.
            force (bool, optional): If True, the dependency will be
                reinstalled even if it is already installed.

        Raises:
            DependencyError: If the dependency is not valid.

        """
        self.install_manager(always_yes=always_yes)
        with self.error_accumulator(
                DependencyValidationError,
                DependencyError,
                f'Dependency {self.package} cannot be '
                f'installed via {self._package_manager}:'):
            self.check_validity()
        installed = self.is_installed
        if (not force) and installed:
            return
        if not installed:
            alt_installed = self.is_installed_by_other()
            if alt_installed:
                msg = (
                    f'Package {self.package} already installed as '
                    f'{alt_installed}. Installing with '
                    f'{self._package_manager} may result in conflicts. '
                    f'Installation with {self._package_manager} '
                )
                if force:
                    msg += 'forced by user'
                else:
                    msg += 'can be forced by passing `force=True`'
                warnings.warn(msg)
                if not force:
                    return
        if not (always_yes or self.args_yes):  # pragma: user input
            if not self.ask_user(f'Install {self.package} via '
                                 f'{self._package_manager}?'):
                return
        self.run_steps(self.pre_install_steps, context='pre-install')
        self._install(always_yes=always_yes)
        self.run_steps(self.post_install_steps, context='post-install')
        self.invalidate_cache()
        if self.double_check_install and (not self.is_installed):
            raise DependencyError(f'Failed to install {self.package} via '
                                  f'{self._package_manager}')

    def uninstall_command(self, always_yes=_default_always_yes):
        r"""Get the command arguments for uninstalling the package.

        Args:
            always_yes (bool, optional): If True, the uninstallation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        out = self.command_prefix(
            uninstall=True, conda_env=self.conda_env)
        if always_yes and self.args_yes:
            out += self.args_yes
        out += [self.package]
        out += [x.package for x in self.additional_packages]
        out += self.args_suffix_uninstall
        if self.arguments_uninstall:
            out += self.arguments_uninstall
        return out

    def _uninstall(self, **kwargs):
        cmd = self.uninstall_command(**kwargs)
        self.run_command(cmd, context='uninstall')
        self._install_called = False

    def uninstall(self, always_yes=_default_always_yes, force=False):
        r"""Uninstall the dependency.

        Args:
            always_yes (bool, optional): If True, the uninstallation will
                not ask for user confirmation. Defaults to False.
            force (bool, optional): If True, the dependency will be
                uninstalled even if it is not installed.

        """
        with self.error_accumulator(
                DependencyValidationError,
                DependencyError,
                f'Dependency {self.package} cannot be '
                f'uninstalled via {self._package_manager}:'):
            self.check_validity()
        if (not force) and self.is_uninstalled:
            return
        if not (always_yes or self.args_yes):  # pragma: user input
            if not self.ask_user(f'Uninstall {self.package} via '
                                 f'{self._package_manager}?'):
                return
        self.run_steps(self.pre_uninstall_steps, context='pre-uninstall')
        self._uninstall(always_yes=always_yes)
        self.run_steps(self.post_uninstall_steps, context='post-uninstall')
        self.invalidate_cache()
        if self.double_check_install and (not self.is_uninstalled):
            raise DependencyError(f'Failed to uninstall {self.package} via '
                                  f'{self._package_manager}')

    def run_command(self, cmd, **kwargs):
        r"""Run a command via subprocess.

        Args:
            cmd (list): List of arguments in the command.
            **kwargs: Additional keyword arguments are passed to
                run_command_class after adding values from the
                command_kwargs property that are not already present.
        
        """
        if not cmd:
            return
        kwargs = dict(self.command_kwargs, **kwargs)
        kwargs.setdefault('conda_env', self.conda_env)
        return self.run_command_class(cmd, **kwargs)

    @classmethod
    def invalidate_cache(cls):
        r"""Invalidate the cached results."""
        _cached_results.clear()

    @classmethod
    def run_command_class(cls, cmd, context='', return_output=False,
                          package='', invalidate_cache=True,
                          cache_key=None, conda_env=None, **kwargs):
        r"""Run a command via subprocess.

        Args:
            cmd (list): List of arguments in the command.
            context (str, optional): Description of the purpose of the
                command.
            return_output (bool, optional): If True, the output from the
                command will be returned.
            package (str, optional): Package name to use in error
                message.
            invalidate_cache (bool, optional): If True, invalidate any
                existing cached list and generate a new one. If False,
                use any existing cached result.
            cache_key (str, optional): Key that should be used to cache
                results from the command if return_output is True.
            conda_env (str, optional): Conda environment to activate
                before running the steps.
            **kwargs: Additional keyword arguments are passed to
                subprocess.check_call.
        
        """
        if not cmd:
            return
        if context and not context.endswith(' '):
            context += ' '
        if isinstance(cmd, str):
            cmd = cmd.split()
        if conda_env:
            kwargs['shell'] = True
            cmd = CondaDependency.command_run_in_env(conda_env) + cmd
        cmdstr = ' '.join(cmd)
        if kwargs.get('shell', False):
            cmd = cmdstr
        if cache_key is None:
            cache_key = cmdstr
        try:
            if return_output:
                if ((invalidate_cache
                     or cache_key not in _cached_results)):
                    # print(f"RUNNING: {cmdstr}")
                    _cached_results[cache_key] = (
                        subprocess.check_output(cmd, **kwargs))
                return _cached_results[cache_key]
            else:
                # print(f"RUNNING: {cmdstr}")
                subprocess.check_call(cmd, **kwargs)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if package:
                package = f'of "{package}" '
            else:
                package = ''
            raise DependencyError(f'Error occured during {context}'
                                  f'{package}via '
                                  f'{cls._package_manager}:\n'
                                  f'  command: {cmdstr}\n'
                                  f'  {type(e)}: {e}')

    def run_steps(self, steps, **kwargs):
                  
        r"""Run a set of steps via subprocess.

        Args:
            steps (list): Set of steps to run.
            **kwargs: Additional keyword arguments are passed to
                self.run_command.
        
        """
        if not steps:
            return
        kwargs = dict(self.command_kwargs, **kwargs)
        kwargs.setdefault('conda_env', self.conda_env)
        return self.run_steps_class(steps, **kwargs)

    @classmethod
    def run_steps_class(cls, steps, context='', package='',
                        invalidate_cache=True, cache_key=None,
                        conda_env=None, **kwargs):
        r"""Run a set of steps via subprocess.

        Args:
            steps (list): Set of steps to run.
            context (str, optional): Description of the purpose of the
                steps.
            package (str, optional): Package name to use in error
                message.
            invalidate_cache (bool, optional): If True, invalidate any
                existing cached list and generate a new one. If False,
                use any existing cached result.
            cache_key (str, optional): Key that should be used to cache
                results from the command if return_output is True.
            conda_env (str, optional): Conda environment to activate
                before running the steps.
            **kwargs: Additional keyword arguments are passed to
                GeneratedShellScript.run.
        
        """
        if not steps:
            return
        if context:
            context = f'{context.rstrip()} step '
        if conda_env:
            kwargs['shell'] = True
            run_prefix = ' '.join(
                CondaDependency.command_run_in_env(conda_env))
            steps = [
                f'{run_prefix} {x}'
                for x in steps
            ]
        script_file = tools.TemporaryGeneratedFile(
            steps, ext=None, cls=tools.GeneratedShellScript,
            exit_on_error=True)
        stepstr = '\n\t' + '\n\t'.join(steps)
        if cache_key is None:
            cache_key = stepstr
        try:
            if kwargs.get('return_output', False):
                if invalidate_cache:
                    _cached_results.pop(cache_key, None)
                if cache_key in _cached_results:
                    return _cached_results[cache_key]
            out = script_file.run(**kwargs)
            if kwargs.get('return_output', False):
                _cached_results[cache_key] = out
            return out
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if package:
                package = f'of "{package}" '
            else:
                package = ''
            raise DependencyError(f'Error occured during {context}'
                                  f'{package}via '
                                  f'{cls._package_manager}:\n'
                                  f'  steps: {stepstr}\n'
                                  f'  {type(e)}: {e}')
        # for x in steps:
        #     cls.run_command_class(x, context=context, **kwargs)


class DependencyCollectionBase(ManagedDependencyBase):
    r"""Base class for collection of dependencies. This class
    should not be used directly.

    Args:
        shared_properties (dict, optional): Properties that will be added
            to all members/options.
        default_package_manager (str, list, optional): Package manager(s)
            that should be used for members that do not have a
            package_manager property and cannot be determined from the
            provided properties. If a list is provided, the first
            package_manager that is installed will be used. If not
            provided, the default order will be based on the operating
            system:
                macos  : ['conda', 'brew', 'apt', 'choco', 'vcpkg']
                linux  : ['conda', 'apt', 'brew', 'choco', 'vcpkg']
                windows: ['conda', 'choco', 'vcpkg', 'apt', 'brew']
    
    """

    _collection_property = None
    _schema_properties = {
        'shared_properties': {
            'type': 'object',
        },
        'default_package_manager': {
            'type': 'array',
            'items': {
                '$ref': (
                    '#/definitions/dependency-subtype-base/properties/'
                    'package_manager'
                )
            },
            'allowSingular': True,
        },
    }

    def __init__(self, shared_properties=None, **kwargs):
        collection = kwargs.pop(self._collection_property, [])
        if shared_properties is None:
            shared_properties = {}
        for k, v in kwargs.items():
            if k != 'default_package_manager':
                shared_properties.setdefault(k, v)
        kwargs[self._collection_property] = []
        super(DependencyCollectionBase, self).__init__(
            shared_properties=shared_properties, **kwargs)
        if self.default_package_manager is not None:
            self.default_package_manager = self.select_installed(
                self.default_package_manager)
        for x in collection:
            self.append(x, init=True)

    def __str__(self):
        collection = ', '.join([
            str(x) for x in getattr(self, self._collection_property)])
        return f'{self._package_manager}[{collection}]'
    
    @classmethod
    def manager_executable(cls, **kwargs):
        r"""Executable used for installation command.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            str: Path to the installation executable.
        
        """
        raise NotImplementedError(f'{cls.__name__} does not have an '
                                  f'executable')

    @classmethod
    def manager_installed(cls, **kwargs):
        r"""Determine if the package manager is installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the package manager is installed.

        """
        return True

    def init_child(self, solf, **kwargs):
        r"""Add collection properties to a dependency in the collection.

        Args:
            solf (ManagedDependencyBase, dict): Dependency or dependency
                properties from which a child dependency should be
                created.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            ManagedDependencyBase: Updated/created child dependency.

        """
        if not isinstance(solf, ManagedDependencyBase):
            for k, v in self.shared_properties.items():
                kwargs.setdefault(k, v)
            kwargs.setdefault('default_package_manager',
                              self.default_package_manager)
        else:
            solf.update_component_properties(**self.shared_properties)
        return super(DependencyCollectionBase, self).init_child(
            solf, **kwargs)

    def append(self, solf, **kwargs):
        r"""Add a dependency to the set of additional packages that will
        be installed at the same time as this one.

        Args:
            solf (ManagedDependencyBase): Dependency to append.
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            DependencyError: If solf cannot be appended to this
                dependency.

        """
        raise NotImplementedError


class DependencySet(DependencyCollectionBase):
    r"""Set of related dependencies.

    Args:
        members (list): Dependencies in the set. All of the members will
            be installed with the set is installed.

    """

    _package_manager = 'set'
    _schema_subtype_description = "Set of related dependencies"
    _schema_properties = {
        'members': {
            'type': 'array',
            'items': {'$ref': '#/definitions/dependency'}
        },
    }
    _schema_excluded_from_inherit = ['package']
    _schema_required = ['members']
    _collection_property = 'members'

    def __init__(self, *args, **kwargs):
        self.package = None
        super(DependencySet, self).__init__(*args, **kwargs)

    def is_installed_by_other(self, *args, **kwargs):
        r"""Check if package is installed by another package manager.

        Args:
            *args, **kwargs: Arguments are passed to the equivalent
                method for each of the members.
        
        Returns:
            ManagedDependencyBase: Alternate instance of the package
                installed by another package manager if the package is
                installed, False otherwise.

        """
        out = [
            x.is_installed_by_other(*args, **kwargs) for x in self.members
        ]
        if any(out):
            for i in range(len(out)):
                if not out[i]:
                    out[i] = self.members[i]
            return DependencySet(members=out)
        return False

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the members.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        super(DependencySet, self).check_validity(**kwargs)
        for x in self.members:
            with self.error_accumulator(DependencyValidationError,
                                        f'Member {x} invalid:'):
                x.check_validity(**kwargs)
        
    def check_installed(self, **kwargs):
        r"""Check if the dependency is installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the members.

        Raises:
            DependencyInstalledError: If the dependency is not installed.

        """
        # super(DependencySet, self).check_installed(**kwargs)
        out = []
        for x in self.members:
            with self.error_accumulator(DependencyInstalledError,
                                        f'Member {x} not installed:'):
                out.append(x.check_installed(**kwargs))
        return out

    def check_uninstalled(self, **kwargs):
        r"""Check if the dependency is uninstalled.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the members.

        Raises:
            DependencyUninstalledError: If the dependency is not
                uninstalled.

        """
        # super(DependencySet, self).check_uninstalled(**kwargs)
        out = []
        for x in self.members:
            with self.error_accumulator(DependencyUninstalledError,
                                        f'Member {x} not uninstalled:'):
                out.append(x.check_uninstalled(**kwargs))
        return out

    def is_appendable(self, solf):
        r"""Determine if this dependency can be installed at the same
        time as another dependency.

        Args:
            solf (ManagedDependencyBase): Dependency to compare against.

        Returns:
            bool: True if solf can be appended to this dependency, False
                otherwise.

        """
        return True

    def append(self, solf, **kwargs):
        r"""Add a dependency to the set of additional packages that will
        be installed at the same time as this one.

        Args:
            solf (ManagedDependencyBase): Dependency to append.
            **kwargs: Additional keyword arguments are ignored.

        Raises:
            DependencyError: If solf cannot be appended to this
                dependency.

        """
        solf = self.init_child(solf)
        for x in self.members:
            try:
                x.append(solf)
                return
            except DependencyError:
                pass
        self.members.append(solf)
        
    def install(self, members=None, **kwargs):
        r"""Install the dependency set.

        Args:
            members (list, optional): Names of members that should be
                installed.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        """
        with self.error_accumulator(
                DependencyError,
                'One or more errors during installation of members:'):
            for x in self.members:
                if members is not None and x.package not in members:
                    continue
                with self.error_accumulator(DependencyError,
                                            f'Member {x}:'):
                    x.install(**kwargs)

    def uninstall(self, members=None, **kwargs):
        r"""Uninstall the dependency set.

        Args:
            members (list, optional): Names of members that should be
                installed.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        """
        with self.error_accumulator(
                DependencyError,
                'One or more errors during uninstallation of members:'):
            for x in self.members:
                if members is not None and x.package not in members:
                    continue
                with self.error_accumulator(DependencyError,
                                            f'Member {x}:'):
                    x.uninstall(**kwargs)


class DependencyOptions(DependencyCollectionBase):
    r"""Set of different options for installing a dependency

    Args:
        options (list): Different options for installing the dependency.
            The first valid option will be installed.

    """

    _package_manager = 'options'
    _schema_subtype_description = (
        "Set of different options for installing a dependency")
    _schema_properties = {
        'options': {
            'type': 'array',
            'items': {'$ref': '#/definitions/dependency'}
        },
    }
    _schema_required = ['package', 'options']
    _collection_property = 'options'

    def __init__(self, *args, **kwargs):
        self.selected_option = None
        super(DependencyOptions, self).__init__(*args, **kwargs)

    def is_installed_by_other(self, *args, **kwargs):
        r"""Check if package is installed by another package manager.

        Args:
            *args, **kwargs: Arguments are passed to the parent method
                after excluding all of the package managers in the set.
        
        Returns:
            ManagedDependencyBase: Alternate instance of the package
                installed by another package manager if the package is
                installed, False otherwise.

        """
        exclude = kwargs.pop('exclude', [])
        exclude = exclude + [x._package_manager for x in self.options]
        return super(DependencyOptions, self).is_installed_by_other(
            *args, exclude=exclude, **kwargs)

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the options.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        super(DependencyOptions, self).check_validity(**kwargs)
        if self.selected_option:
            self.selected_option.check_validity(**kwargs)
            return
        with self.error_accumulator(DependencyValidationError,
                                    'None of the options are valid:',
                                    error_count=len(self.options)):
            for x in self.options:
                with self.error_accumulator(DependencyValidationError,
                                            f'Option {x}:'):
                    x.check_validity(**kwargs)
        
    def check_installed(self, **kwargs):
        r"""Check if the dependency is installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the options.

        Raises:
            DependencyInstalledError: If the dependency is not installed.

        """
        # super(DependencyOptions, self).check_installed(**kwargs)
        if self.selected_option:
            return self.selected_option.check_installed(**kwargs)
        out = None
        with self.error_accumulator(DependencyInstalledError,
                                    'None of the options are installed:',
                                    error_count=len(self.options)):
            for x in self.options:
                with self.error_accumulator(DependencyInstalledError,
                                            f'Option {x}:'):
                    iout = x.check_installed(**kwargs)
                    if iout and out is None:
                        out = iout
        return out

    def check_uninstalled(self, **kwargs):
        r"""Check if the dependency is uninstalled.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the options.

        Raises:
            DependencyUninstalledError: If the dependency is not
                uninstalled.

        """
        # super(DependencyOptions, self).check_uninstalled(**kwargs)
        if self.selected_option:
            return self.selected_option.check_uninstalled(**kwargs)
        with self.error_accumulator(DependencyUninstalledError,
                                    'One or more options are not '
                                    'uninstalled:'):
            for x in self.options:
                with self.error_accumulator(DependencyUninstalledError,
                                            f'Option {x}:'):
                    x.check_uninstalled(**kwargs)

    def append(self, solf, require_all=False, init=False):
        r"""Add a dependency to the set of additional packages that will
        be installed at the same time as this one.

        Args:
            solf (ManagedDependencyBase): Dependency to append.
            require_all (bool, optional): If True, requires that solf be
                appended to all options. If False, solf will be appended
                to the all options it can be appended to and an error will
                be raised if it cannot be appended to any of the options.
            init (bool, optional): If True, solf will be added to
                the current set of options as a new option.

        Raises:
            DependencyError: If solf cannot be appended to any/all
                dependency options.

        """
        solf = self.init_child(solf)
        if init:
            self.options.append(solf)
            return
        errors = []
        with self.error_accumulator(DependencyError, registry=errors):
            for i, x in enumerate(self.options):
                with self.error_accumulator(DependencyError,
                                            f'Option {x}:'):
                    x.append(solf)
                if (not require_all) and (len(errors) < (i + 1)):
                    return
        if (not require_all) and (len(errors) != len(self.options)):
            return
        key = 'all' if require_all else 'any'
        raise DependencyError(ErrorRegistry.format_errors(
            f"Dependency ({solf}) cannot be appended "
            f"to {key} of the options in this set "
            f"({self.options}):", errors))
        
    def install(self, **kwargs):
        r"""Install the dependency.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyError: If none of the options can be installed.

        """
        if self.selected_option:
            self.selected_option.install(**kwargs)
            return
        with self.error_accumulator(DependencyError,
                                    f'Failed to install {self.package} '
                                    f'via any of the options:',
                                    error_count=len(self.options)):
            for x in self.options:
                with self.error_accumulator(DependencyError,
                                            f'Option {x}:'):
                    x.install(**kwargs)
                if x.is_installed:
                    self.selected_option = x
                    return

    def uninstall(self, **kwargs):
        r"""Uninstall the dependency.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyError: If none of the options can be installed.

        """
        if self.selected_option:
            self.selected_option.uninstall(**kwargs)
            self.selected_option = None
            return
        with self.error_accumulator(DependencyError,
                                    f'Failed to uninstall {self.package} '
                                    f'via any of the options:'):
            for x in self.options:
                with self.error_accumulator(DependencyError,
                                            f'Option {x}:'):
                    x.uninstall(**kwargs)


class CondaDependency(ManagedDependencyBase):
    r"""Dependency installed from conda

    Args:
        channel (str, optional): Conda channel that the package should be
            installed from.

    """

    _package_manager = 'conda'
    _schema_subtype_description = "Dependency installed from conda"
    _schema_properties = {
        'channel': {'type': 'string'},
    }
    args_yes = ['-y']
    args_prefix_install = ['install']
    args_prefix_uninstall = ['uninstall']
    args_prefix_list = ['list']
    args_prefix_search = ['list']
    quoted_names = False
    ignore_properties_appendable = ['package', 'version']
    affected_by_conda_env = True

    @classmethod
    def manager_executable(cls, **kwargs):
        r"""Executable used for installation command.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            str: Path to the installation executable.
        
        """
        if shutil.which('mamba'):
            return 'mamba'
        return 'conda'

    @classmethod
    def command_run_in_env(cls, conda_env):
        r"""Get the command prefix that should be used to run commands in
        a conda/mamba environment.

        Args:
            conda_env (str): Conda environment that the command prefix
                should run commands in.

        Returns:
            list: Command prefix.

        """
        executable = cls.manager_executable()
        out = [executable, 'run', '-n', conda_env]
        if 'mamba' not in executable:
            # Mamba2 doesn't support these
            # https://github.com/mamba-org/mamba/issues/3535
            out += ['--live-stream', '--']
        if platform._is_win:  # pragma: windows
            out.insert(0, 'call')
        return out

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        if not tools.get_conda_prefix():
            self.accumulate_error(
                DependencyValidationError,
                'Conda environment could not be located'
            )
        super(CondaDependency, self).check_validity(**kwargs)

    @classmethod
    def parse_list(cls, contents, dont_include_pypi=False):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.
            dont_include_pypi (bool, optional): If True, packages installed
                from PyPI will not be included.

        Returns:
            list: List of package information in dictionaries.

        """
        field_names = None
        end_header = None
        lines = contents.splitlines()
        if contents.startswith('#'):
            for i, x in enumerate(lines):
                if x.startswith('# Name'):
                    field_names = [v.strip().lower() for v in x[2:].split()]
                elif x.startswith('#'):
                    continue
                else:
                    end_header = i
                    break
        else:
            for i, x in enumerate(lines):
                x = x.strip()
                if x.startswith('Name'):
                    field_names = [v.strip().lower() for v in x.split()]
                elif field_names and x.startswith('----'):
                    end_header = i + 1
                    break
        if field_names is None:
            field_names = ['name', 'version', 'build', 'channel']
        out = super(CondaDependency, cls).parse_list(
            '\n'.join(lines[end_header:]), field_names=field_names)
        if dont_include_pypi:
            out = [x for x in out if out['channel'] != 'pypi']
        return out

    @classmethod
    def run_command_class(cls, cmd, conda_env=None, **kwargs):
        r"""Run a command via subprocess.

        Args:
            cmd (list): List of arguments in the command.
            conda_env (str, optional): Conda environment to activate
                before running the steps.
            **kwargs: Additional keyword arguments are passed to the
                parent method.
        
        """
        if ((cmd and isinstance(cmd, list)
             and cmd[0].endswith(cls.manager_executable()))):
            if conda_env:
                cmd = cmd[:2] + ['-n', conda_env] + cmd[2:]
            if platform._is_win:  # pragma: windows
                # Conda/mamba commands must be run on the shell on
                # windows as it is implemented as a batch script
                cmd.insert(0, 'call')
                kwargs['shell'] = True
        return super(CondaDependency, cls).run_command_class(
            cmd, **kwargs)

    def uninstall_command(self, **kwargs):
        r"""Get the command arguments for uninstalling the package.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            list: Set of command arguments.

        """
        packages = [self] + self.additional_packages
        installed = self.list(conda_env=self.conda_env)
        for x in packages:
            try:
                info = self.search(package=x.package,
                                   version=x.version,
                                   package_list=installed)
            except DependencyError:
                continue
            if info['channel'] == 'pypi':
                raise DependencyError(f'Cannot use conda/mamba to '
                                      f'uninstall "{x.package}", which '
                                      f'was installed from pypi. Use '
                                      f'"pip uninstall" instead')
        return super(CondaDependency, self).uninstall_command(**kwargs)


class PipDependency(ManagedDependencyBase):
    r"""Dependency installed from PyPI via pip"""

    _package_manager = 'pip'
    _schema_subtype_description = "Dependency installed from PyPI via pip"
    args_yes = ['-y']
    args_prefix = ['-m', 'pip']
    args_prefix_install = ['install']
    args_prefix_uninstall = ['uninstall']
    args_prefix_list = ['list']
    args_prefix_search = ['list']
    ignore_properties_appendable = ['package', 'version']
    affected_by_conda_env = True
    installable_from_source = ['setup.py', 'setup.cfg', 'pyproject.toml']
    manager_conda_package = 'python'
    manager_executable_name = 'python'
    language_specific = 'python'

    @classmethod
    def parse_list(cls, contents):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.

        Returns:
            list: List of package information in dictionaries.

        """
        field_names = None
        contents = contents.splitlines()
        end_header = None
        for i, x in enumerate(contents):
            if x.startswith('Package'):
                field_names = [v.strip().lower() for v in x.split()]
                field_names[0] = 'name'
            elif x.startswith('--'):
                end_header = i + 1
                break
        return super(PipDependency, cls).parse_list(
            '\n'.join(contents[end_header:]), field_names=field_names)

    def install_command(self, always_yes=_default_always_yes, **kwargs):
        r"""Get the command arguments for installing the package.

        Args:
            always_yes (bool, optional): If True, the installation will
                not ask for user confirmation. Defaults to False.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            list: Set of command arguments.

        """
        # -y only valid on uninstall
        if not always_yes:  # pragma: user input
            if not self.ask_user(f'Install {self.package} via '
                                 f'{self._package_manager}?'):
                return
        kwargs['always_yes'] = False
        return super(PipDependency, self).install_command(**kwargs)


class CRANDependency(ManagedDependencyBase):
    r"""Dependency installed from CRAN

    Args:
        repos (str, optional): Mirror that should be used to install the
            dependency from.
        r_install_steps (list, optional): Set of R commands that should
            be used to install the package if different from the
            standard 'install.packages()' method.

    """

    _package_manager = 'cran'
    _schema_subtype_description = "Dependency installed from CRAN"
    _schema_properties = {
        'repos': {
            'type': 'string',
            'default': 'http://cloud.r-project.org'
        },
        'r_install_steps': {
            'type': 'array',
            'items': {'type': 'string'},
        },
    }
    constraint_fstring = '{op} {ver}'
    constraint_sep = ', '
    affected_by_conda_env = True
    manager_executable_name = 'R'
    installable_from_source = [{'R', 'NAMESPACE', 'DESCRIPTION'}]
    args_prefix = ['-s', '-q']
    manager_conda_package = 'r-base'
    language_specific = 'R'

    @classmethod
    def manager_executable(cls, for_script=False, **kwargs):
        r"""Executable used for installation command.

        Args:
            for_script (bool, optional): If True, the Rscript executable
                is returned.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            str: Path to the installation executable.
        
        """
        out = super(CRANDependency, cls).manager_executable(**kwargs)
        if out and for_script:
            outdir = os.path.dirname(out)
            out = 'Rscript'
            if outdir:
                out = os.path.join(outdir, out)
        return out
            
    @classmethod
    def run_command_class(cls, cmd, is_R=False, **kwargs):
        r"""Run a command via subprocess.

        Args:
            cmd (list): List of arguments in the command.
            is_R (bool, optional): If True, the steps are R commands that
                should be written to an R script that can be executed.
            **kwargs: Additional keyword arguments are passed to
                the parent method.
        
        """
        script_file = None
        if is_R:
            return cls.run_steps_class(cmd, is_R=True, **kwargs)
        try:
            out = super(CRANDependency, cls).run_command_class(
                cmd, **kwargs)
        finally:
            if script_file:
                script_file.teardown()
        return out
        
    @classmethod
    def run_steps_class(cls, steps, is_R=False, cache_key=None, **kwargs):
                  
        r"""Run a set of steps via subprocess.

        Args:
            steps (list): Set of steps to run.
            is_R (bool, optional): If True, the steps are R commands that
                should be written to an R script that can be executed.
            cache_key (str, optional): Key that should be used to cache
                results from the command if return_output is True.
            **kwargs: Additional keyword arguments are passed to
                self.run_command_class.
        
        """
        script_file = None
        if is_R:
            script_file = tools.TemporaryGeneratedFile(steps, ext='.R')
            script_file.setup()
            if cache_key is None:
                cache_key = '\n'.join(steps)
            steps = [f'{cls.manager_executable(for_script=True)} '
                     f'{script_file.name}']
        try:
            return super(CRANDependency, cls).run_steps_class(
                steps, cache_key=cache_key, **kwargs)
        finally:
            if script_file:
                script_file.teardown()
        
    @classmethod
    def list(cls, package=None, invalidate_cache=False, conda_env=None,
             **kwargs):
        r"""List the packages installed by this package manager.

        Args:
            package (str, optional): Name of package to restrict list to.
            invalidate_cache (bool, optional): If True, invalidate any
                existing cached list and generate a new one. If False,
                use any existing cached result.
            conda_env (str, optional): Conda environment that executable
                should come from.
            **kwargs: Additional keyword arguments are passed to
                parse_list.

        Returns:
            list: List of package information in dictionaries.

        """
        if cls.manager_not_yet_installed(conda_env=conda_env):
            return []
        package_str = f'\"{package}\"' if package else ''
        cmd = [
            f'installed.packages()[{package_str}, '
            f'c("Package", "Version")]'
        ]
        if package:
            cmd = [
                f'if (!library({package_str}, character.only=TRUE, '
                f'logical.return=TRUE)) {{',
                '    quit(status=0, save=\'no\')',
                '}',
            ] + cmd
        out = cls.run_command_class(
            cmd, is_R=True, context='check', package=package,
            return_output=True, invalidate_cache=invalidate_cache,
            conda_env=conda_env
        ).decode('utf-8')
        return cls.parse_list(out, package=package, **kwargs)

    @classmethod
    def parse_list(cls, contents, package=None):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.
            package (str, optional): Name of package that list command
                was restricted to.

        Returns:
           list: List of package information in dictionaries.

        """
        field_names = []
        concat = []
        current_block = []

        def advance():
            if current_block:
                if concat:
                    assert len(current_block) == len(concat)
                    for i, x in enumerate(current_block):
                        concat[i] += '    ' + x
                else:
                    concat.extend(current_block)
                current_block.clear()

        for x in contents.splitlines():
            if x.startswith('>') or x.isspace():
                continue
            elif package:
                if not field_names:
                    field_names += x.split()
                else:
                    current_block.append(x)
            elif x.startswith(' '):
                field_names += x.split()
                advance()
            else:
                current_block.append(x.split(maxsplit=1)[-1])
        advance()
        out = super(CRANDependency, cls).parse_list(
            '\n'.join(concat), field_names=field_names)
        for x in out:
            x['name'] = x['Package'].strip('"')
            x['version'] = x['Version'].strip('"')
        return out

    def is_installed_by_other(self, include=None, **kwargs):
        r"""Check if package is installed by another package manager.

        Args:
            include (str, list, optional): Package manager(s) to
                check. If not provided, all installed package managers
                will be checked.
            **kwargs: Arguments are passed to the parent method.
        
        Returns:
            ManagedDependencyBase: Alternate instance of the package
                installed by another package manager if the package is
                installed, False otherwise.

        """
        if include == 'conda' or include == CondaDependency:
            kwargs.setdefault('package', f'r-{self.package.lower()}')
        return super(CRANDependency, self).is_installed_by_other(
            include=include, **kwargs)

    def format_constraint(self, ver=None, op=None):
        r"""Format a version constraint.

        Args:
            ver (str): Version number.
            op (str, optional): Version constraint operator.

        Returns:
            str: Formatted version constraint.

        """
        assert ver
        if not op:
            return ver
        return self.constraint_fstring.format(ver=ver, op=op)

    @property
    def formatted_version(self):
        r"""str: Version string with constraints indicators"""
        constraints = self.version_constraints
        if len(constraints) == 1 and constraints[0]['op'] == '==':
            return constraints[0]['ver']
        return super(CRANDependency, self).formatted_version

    def is_appendable(self, solf):
        r"""Determine if this dependency can be installed at the same
        time as another dependency.

        Args:
            solf (ManagedDependencyBase): Dependency to compare against.

        Returns:
            bool: True if solf can be appended to this dependency, False
                otherwise.

        """
        if not super(CRANDependency, self).is_appendable(solf):
            return False
        if self.version or solf.version:
            return False
        return True
        
    def _install(self, always_yes=_default_always_yes):
        r"""Get the command arguments for installing the package.

        Args:
            always_yes (bool, optional): If True, the installation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        kwargs = {'context': 'install', 'conda_env': self.conda_env}
        cmd = []
        if self.r_install_steps:
            print(f"USING r_install_steps = {self.r_install_steps}")
            kwargs['is_R'] = True
            cmd += self.r_install_steps
        elif self.source_directory:
            cmd += [
                self.manager_executable(),
                'CMD', 'INSTALL', self.source_directory
            ]
        else:
            kwargs['is_R'] = True
            if self.version:
                assert not self.additional_packages
                cmd += [
                    f'install.packages(\"remotes\", '
                    f'repos=\"{self.repos}\")',
                    'require(remotes)',
                    f'install_version(\"{self.package}\", dep=TRUE, '
                    f'version=\"{self.formatted_version}\", '
                    f'repos=\"{self.repos}\")',
                    f'if (!library(\"{self.package}\", '
                    f'character.only=TRUE, logical.return=TRUE)) {{',
                    '    quit(status=1, save=\'no\')',
                    '}',
                ]
            else:
                packages = [self.package]
                if self.additional_packages:
                    assert not self.version
                    assert not self.source_directory
                    packages += [x.package for x in
                                 self.additional_packages]
                packages = 'c(\"' + '\", \"'.join(packages) + '\")'
                cmd += [
                    f'packages = {packages}',
                    f'install.packages(packages, dep=TRUE, '
                    f'repos=\"{self.repos}\")',
                    'for (l in packages) {',
                    '    if (!library(l, character.only=TRUE, '
                    'logical.return=TRUE)) {',
                    '        quit(status=1, save=\'no\')',
                    '    }',
                    '}',
                ]
        return self.run_command(cmd, **kwargs)

    def _uninstall(self, always_yes=_default_always_yes):
        r"""Get the command arguments for uninstalling the package.

        Args:
            always_yes (bool, optional): If True, the uninstallation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        kwargs = {'context': 'uninstall', 'is_R': True,
                  'conda_env': self.conda_env}
        cmd = []
        package = self.package
        if self.additional_packages:
            assert not self.version
            packages = [package] + [x.package for x in
                                    self.additional_packages]
            package = 'c(\"' + '\", \"'.join(packages) + '\")'
        else:
            package = f'\"{package}\"'
        cmd.append(
            f'remove.packages({package})'
        )
        return self.run_command(cmd, **kwargs)


class AptDependency(ManagedDependencyBase):
    r"""Dependency installed from apt"""

    _package_manager = 'apt'
    _schema_subtype_description = "Dependency installed from apt"
    args_yes = ['-y']
    args_prefix_install = ['install']
    args_prefix_uninstall = ['uninstall']
    args_prefix_list = ['list', '--installed']
    args_prefix_search = ['show']
    ignore_properties_appendable = ['package', 'version']

    @classmethod
    def manager_installed(cls, **kwargs):
        r"""Determine if the package manager is installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            bool: True if the package manager is installed.

        """
        if not super(AptDependency, cls).manager_installed(**kwargs):
            return False
        return bool(shutil.which('apt-get'))

    @classmethod
    def command_prefix(cls, uninstall=False, **kwargs):
        r"""Prefix arguments for installation commands.

        Args:
            uninstall (bool, optional): If True, get the prefix for
                uninstallation.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Prefix arguments.
        
        """
        out = ['apt-get']
        if uninstall:
            out += cls.args_prefix_uninstall
        else:
            out += cls.args_prefix_install
        if _in_github_action:
            # Only enable sudo for testing, otherwise allow the user to
            # decide if they want to run yggdrasil with sudo, or just
            # install the dependencies themselves
            out.insert(0, 'sudo')
        return out

    @classmethod
    def parse_list(cls, contents):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.

        Returns:
            list: List of package information in dictionaries.

        """
        raise NotImplementedError(contents)


class HomebrewDependency(ManagedDependencyBase):
    r"""Dependency installed from homebrew"""

    _package_manager = 'brew'
    _schema_subtype_description = "Dependency installed from homebrew"
    args_prefix_install = ['install']
    args_prefix_uninstall = ['uninstall']
    args_prefix_list = ['ls', '--versions']
    ignore_properties_appendable = ['package']
    versioned_fstring = '{package}@{ver}'
    list_field_names = ['name', 'version']

    # def __init__(self, *args, **kwargs):
    #     super(HomebrewDependency, self).__init__(*args, **kwargs)
    #     if self.version:
    #         assert not self.additional_packages
    #         self.local_tap = f'$USER/local-{self.package}'
    #         self.pre_install_steps += [
    #             'set +e',
    #             f'brew tap-new {self.local_tap}',
    #             'set -e',
    #             f'brew extract --version={self.formatted_version} '
    #             f'{self.package} {self.local_tap}',
    #         ]

    def format_constraint(self, ver=None, op=None):
        r"""Format a version constraint.

        Args:
            ver (str): Version number.
            op (str, optional): Version constraint operator.

        Returns:
            str: Formatted version constraint.

        """
        assert ver
        if (not op) or (op == '=='):
            return ver
        return self.constraint_fstring.format(ver=ver, op=op)


class ChocoDependency(ManagedDependencyBase):
    r"""Dependency installed via chocolate"""

    _package_manager = 'choco'
    _schema_subtype_description = "Dependency installed via chocolate"
    args_yes = ['-y']
    args_prefix_install = ['install']
    args_prefix_uninstall = ['uninstall']
    args_prefix_list = ['list']
    args_prefix_search = ['search']
    ignore_properties_appendable = ['package', 'version']

    @classmethod
    def parse_list(cls, contents):
        r"""Parse the output of the list command.

        Args:
            contents (str): Output of list command.

        Returns:
            list: List of package information in dictionaries.

        """
        raise NotImplementedError(contents)


class VcpkgDependency(ManagedDependencyBase):
    r"""Dependency installed via vcpkg"""

    _package_manager = 'vcpkg'
    _schema_subtype_description = "Dependency installed via vcpkg"
    args_prefix_install = ['install', '--triplet', 'x64-windows']
    args_prefix_uninstall = ['uninstall', '--triplet', 'x64-windows']
    args_prefix_list = ['list']
    args_prefix_search = ['search']
    ignore_properties_appendable = ['package', 'version']
    list_field_names = ['name', 'version', 'description']

    # @classmethod
    # def manager_executable(cls, **kwargs):
    #     r"""Executable used for installation command.

    #     Args:
    #         **kwargs: Additional keyword arguments are ignored.

    #     Returns:
    #         str: Path to the installation executable.
        
    #     """
    #     return 'vcpkg.exe'


class SourceDependencyBase(ManagedDependencyBase):
    r"""Base class for dependency installed from source code

    Args:
        directory (str): Path to the directory that contains the source
            code to install.
        products (list, optional): Files that are required for the
            dependency to be considered installed. If relative paths
            are included, they will be taken as relative to
            install_prefix if provided, then the build directory if
            buildfile is specified and then directory otherwise.
        install_prefix (str, optional): Prefix for directory under which
            built packages should be installed. If not provided and
            conda_env set or run inside a conda environment, the conda
            environment prefix will be used.

    """

    _schema_properties = {
        'directory': {'type': 'string'},
        'install_prefix': {'type': 'string'},
    }
    _schema_required = ['package', 'directory']
    affected_by_conda_env = True

    def __init__(self, *args, **kwargs):
        super(SourceDependencyBase, self).__init__(*args, **kwargs)
        if not self.command_kwargs:
            self.command_kwargs = {}
        if not os.path.isabs(self.directory):
            self.directory = os.path.join(os.getcwd(), self.directory)
        self.command_kwargs.setdefault('cwd', self.directory)
        if self.install_prefix is None and self.conda_prefix:
            self.install_prefix = self.conda_prefix
        new_products = []
        for x in self.products:
            if not os.path.isabs(x):
                if self.install_prefix:
                    x = os.path.join(self.install_prefix, x)
                else:
                    x = os.path.join(self.directory, x)
            new_products.append(x)
        self.products = new_products

    @classmethod
    def list(cls, package=None, directory=None, **kwargs):
        r"""List the packages installed by this package manager.

        Args:
            package (str, optional): Name of package to restrict list to.
            directory (str, optional): Directory containing source.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: List of package information in dictionaries.

        """
        out = []
        if package and directory and os.path.isdir(directory):
            out.append({'name': package, 'directory': directory})
        return out

    def search(self, **kwargs):
        r"""Search for the current version of the dependency if one
        exists.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyError: If the package is not installed.

        Returns:
            dict: Parameters of package.

        """
        kwargs.setdefault('directory', self.directory)
        return super(SourceDependencyBase, self).search(**kwargs)

    def check_version(self, version, **kwargs):
        r"""Check if a version string satisfies the version constraints.

        Args:
            version (str): Version string to check against constraints.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if version satisfies the constraints, False
                otherwise.

        """
        return True

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        super(SourceDependencyBase, self).check_validity(**kwargs)
        parent = kwargs.get('parent', None)
        if (((not os.path.isdir(self.directory))
             and not (isinstance(self, GitDependency)
                      or isinstance(parent, GitDependency)))):
            # The GitDependency class will create the directory during
            # install via clone if it does not exist
            self.accumulate_error(
                DependencyValidationError,
                f'Directory "{self.directory}" does not exist'
            )

    def is_appendable(self, solf):
        r"""Determine if this dependency can be installed at the same
        time as another dependency.

        Args:
            solf (ManagedDependencyBase): Dependency to compare against.

        Returns:
            bool: True if solf can be appended to this dependency, False
                otherwise.

        """
        return False

    def _install(self, **kwargs):
        raise NotImplementedError

    def _uninstall(self, **kwargs):
        raise NotImplementedError


class SourceDependency(SourceDependencyBase):
    r"""Dependency installed from source code

    Args:
        install_method (str, optional): Method that should be used to
            install the package from the specified directory. If not
            provided, the directory will be inspected to try to determine
            how to install the package. Valid options include:
                'make' : make installation controlled via buildfile,
                         args_build & args_install.
                   make /path/to/buildfile args_build[0] ...
                   make install args_install[0] ...
                'cmake': cmake installation controlled via buildfile,
                         args_config, args_build & args_install.
                   cmake -S /path/to/buildfile -B build args_config[0] ...
                   cmake --build build args_build[0] ...
                   cmake --install build args_install[0] ...
                'pip':   pip installation from source controlled via
                         args_install.
                   pip install package args_install[0] ...
                         
                'cran':  R installation from source controlled via
                         args_install.
                    R CMD INSTALL /path/to/directory args_install[0] ...

    """

    _package_manager = 'source'
    _schema_subtype_description = "Dependency installed from source code"
    _schema_properties = {
        'install_method': {
            'enum': ['make', 'cmake', 'pip', 'cran'],
        }
    }
    prefered_install_method_order = [
        'pip', 'cran', 'cmake', 'make', 'command',
    ]

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration. These actions will still be performed if the environment
        variable YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        SourceDependencyBase.before_registration(cls)
        cls._schema_properties['install_method'] = {
            'enum': sorted(cls.prefered_install_method_order)
        }
        
    def __init__(self, *args, **kwargs):
        super(SourceDependency, self).__init__(*args, **kwargs)
        self._install_method_instance = None

    @classmethod
    def manager_installed(cls, **kwargs):
        r"""Determine if the package manager is installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the package manager is installed.

        """
        return True

    @property
    def install_method_instance(self):
        r"""ManagedDependencyBase: Dependency that should be used to
        install the source code."""
        if self._install_method_instance:
            return self._install_method_instance
        if self.install_method is None:
            self.install_method = self.determine_install_method()
        if isinstance(self.install_method, type):
            install_method_class = self.install_method
            self.install_method = install_method_class._package_manager
        else:
            install_method_class = import_component(
                'dependency', self.install_method)
        self._install_method_instance = self.alternate_manager_instance(
            install_method_class,
            dict(self.extra_kwargs, sourcedir=self.directory),
        )
        return self._install_method_instance

    def determine_install_method(self):
        r"""Determine what installation method should be used for this
        dependency.

        Returns:
            str, type: Installation method or package manager class.

        """
        buildfile = self.extra_kwargs.get('buildfile', None)
        if buildfile:
            if os.path.basename(buildfile) == 'CMakeLists.txt':
                return 'cmake'
            return 'make'
        classes = [
            x for x in get_component_classes('dependency')
            if x.installable_from_source
        ]
        valid_classes = []
        for x in classes:
            if x.is_source_dir(self.directory):
                valid_classes.append(x)
        if len(valid_classes) == 1:
            return valid_classes[0]
        valid_classes = {x._package_manager: x for x in valid_classes}
        for x in self.prefered_install_method_order:
            if x in valid_classes:
                return valid_classes[x]
        raise DependencySourceError(
            f'Cannot determine what method should be '
            f'used to install the package from the '
            f'source code contained in '
            f'"{self.directory}"')

    def install_manager(self, **kwargs):
        r"""Install the manager package.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        """
        super(SourceDependency, self).install_manager(**kwargs)
        try:
            self.install_method_instance.install_manager(**kwargs)
        except DependencySourceError:
            pass

    def search(self, **kwargs):
        r"""Search for the current version of the dependency if one
        exists.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyError: If the package is not installed.

        Returns:
            dict: Parameters of package.

        """
        return self.install_method_instance.search(**kwargs)

    def check_version(self, version, **kwargs):
        r"""Check if a version string satisfies the version constraints.

        Args:
            version (str): Version string to check against constraints.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if version satisfies the constraints, False
                otherwise.

        """
        try:
            return self.install_method_instance.check_version(
                version, **kwargs)
        except DependencySourceError:
            return False

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        super(SourceDependency, self).check_validity(**kwargs)
        kwargs.setdefault('parent', self)
        try:
            self.install_method_instance.check_validity(**kwargs)
        except DependencySourceError as e:
            self.accumulate_error(
                DependencyValidationError, str(e)
            )

    def _install(self, **kwargs):
        return self.install_method_instance._install(**kwargs)

    def _uninstall(self, **kwargs):
        return self.install_method_instance._uninstall(**kwargs)


class BuilderDependencyBase(SourceDependencyBase):
    r"""Dependency base class for build system package managers.

    Args:
        buildfile (str, optional): Path to buildfile (Makefile or
            CMakeLists.txt) that should be used to build the dependency.
            If a relative path is provided, it will be assumed to be
            relative to directory. If provided, a build will be attempted
            to install the dependency.
        args_build (list, optional): Arguments that should be passed to
            the build tool during the build step if buildfile is
            provided.
        args_install (list, optional): Arguments that should be passed to
            the build tool during the install step if buildfile is
            provided.

    """

    _schema_properties = {
        'buildfile': {'type': 'string'},
        'args_build': {
            'type': 'array',
            'items': {'type': 'string'},
        },
        'args_install': {
            'type': 'array',
            'items': {'type': 'string'},
        },
    }
    _buildfile = None

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration. These actions will still be performed if the environment
        variable YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        SourceDependencyBase.before_registration(cls)
        if cls._buildfile is not None:
            setattr(cls, 'installable_from_source', [cls._buildfile])
            cls.manager_conda_package = cls._package_manager

    def __init__(self, *args, **kwargs):
        args_install = kwargs.get('args_install', [])
        for i, x in enumerate(args_install):
            if x.startswith('--prefix'):
                if '=' in x:
                    new_install_prefix = x.split('=')[-1].strip()
                else:
                    new_install_prefix = args_install[i + 1]
                if 'install_prefix' in kwargs:
                    warnings.warn(
                        f'Installation prefix '
                        f'"{kwargs["install_prefix"]}" '
                        f'overridden by an install_arg '
                        f'"{new_install_prefix}"')
                kwargs['install_prefix'] = new_install_prefix
                break
        super(BuilderDependencyBase, self).__init__(*args, **kwargs)
        if not self.args_build:
            self.args_build = []
        if not self.args_install:
            self.args_install = []
        if not self.buildfile:
            self.buildfile = self._buildfile
        if not os.path.isabs(self.buildfile):
            self.buildfile = os.path.join(self.directory, self.buildfile)
        assert not hasattr(self, 'sourcedir')
        self.sourcedir = os.path.dirname(self.buildfile)
        self.builddir = os.path.join(self.directory, 'yggbuild')
        self.install_manifest = os.path.join(
            self.builddir, 'install_manifest.txt')
        if not self.products:
            self.products.append(self.install_manifest)
            self.products.append(self.builddir)
        if self.install_prefix and not any(x.startswith('--prefix')
                                           for x in self.args_install):
            self.args_install += ['--prefix', self.install_prefix]

    @property
    def build_steps(self):
        r"""list: Steps to run to complete the build & installation"""
        raise NotImplementedError  # pragma: unreachable

    def _install(self, **kwargs):
        if not os.path.isdir(self.builddir):
            os.mkdir(self.builddir)
        build_steps = self.build_steps
        self.run_steps(build_steps, context='build', cwd=self.builddir)

    def _uninstall(self, **kwargs):
        if os.path.isfile(self.install_manifest):
            files = open(self.install_manifest, 'r').read().splitlines()
            for x in files:
                if os.path.isfile(x):
                    os.remove(x)
        if os.path.isdir(self.builddir):
            shutil.rmtree(self.builddir)


class MakeDependency(BuilderDependencyBase):
    r"""Dependency installed from source code via make."""

    _package_manager = 'make'
    _schema_subtype_description = (
        "Dependency installed from source code via make")
    _buildfile = 'Makefile'

    @property
    def build_steps(self):
        r"""list: Steps to run to complete the build & installation"""
        return [
            f'make {self.sourcedir} {" ".join(self.args_build)}',
            f'make install {" ".join(self.args_install)}',
        ]


class CMakeDependency(BuilderDependencyBase):
    r"""Dependency installed from source code via cmake.

    Args:
        args_config (list, optional): Arguments that should be passed to
            the build tool during the configuration step (only used when
            buildfile is a CMakeLists.txt file).

    """

    _package_manager = 'cmake'
    _schema_subtype_description = (
        "Dependency installed from source code via cmake")
    _schema_properties = {
        'args_config': {
            'type': 'array',
            'items': {'type': 'string'},
        },
    }
    _buildfile = 'CMakeLists.txt'

    def __init__(self, *args, **kwargs):
        super(CMakeDependency, self).__init__(*args, **kwargs)
        if not self.args_config:
            self.args_config = []

    @property
    def build_steps(self):
        r"""list: Steps to run to complete the build & installation"""
        return [
            f'cmake -S {self.sourcedir} -B {self.builddir} '
            f'{" ".join(self.args_config)}',
            f'cmake --build {self.builddir} '
            f'{" ".join(self.args_build)}',
            f'cmake --install {self.builddir} '
            f'{" ".join(self.args_install)}',
        ]


class GitDependency(SourceDependency):
    r"""Dependency installed from a git respository

    Args:
        repository (str): URL address to the repository.
        commit (str, optional): Commit that should be checked out.
        tag (str, optional): Tag that should be checked out. Ignored if
            commit provided. If version is provided, but tag is not, the
            tag will be set using fstring_tag. If version is a min, max,
            or range, the maximum valid tag will be used.
        branch (str, optional): Branch that should be checked out. Ignored
            if commit or tag provided.
        fstring_tag (str, optional): Format string that should be used
            to turn versions into tags. Defaults to 'v{version}'
        is_private (bool, optional): If True, the repository is private
            and the user may be asked for credentials when cloning the
            repository.
        overwrite (bool, optional): If True, any existing instance of the
            repository in directory will be overwritten. overwrite will
            automatically set to True if directory is not provided and
            the repository is cloned into a temporary directory.
        preserve (bool, optional): If True, uninstall will only uninstall
            the dependency installation and the git repository will not
            be removed. preserve will automatically set to False if
            directory is not provided and the repository is cloned into
            a temporary directory.

    """

    _package_manager = 'git'
    _schema_subtype_description = ("Dependency installed from a git "
                                   "respository")
    _schema_properties = {
        'repository': {'type': 'string'},
        'commit': {'type': 'string'},
        'tag': {'type': 'string'},
        'branch': {'type': 'string'},
        'fstring_tag': {'type': 'string', 'default': 'v{version}'},
        'is_private': {'type': 'boolean', 'default': False},
        'overwrite': {'type': 'boolean', 'default': False},
        'preserve': {'type': 'boolean', 'default': False},
    }
    _schema_required = ['package', 'repository']
    manager_conda_package = 'git'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('repository', kwargs['package'])
        if not kwargs.get('directory', None):
            repository = kwargs['repository']
            repo_name = os.path.splitext(repository.split('/')[-1])[0]
            kwargs['directory'] = os.path.join(tempfile.gettempdir(),
                                               repo_name)
            # Don't preserve repositories checked out into temporary
            # directories
            kwargs.update(overwrite=True, preserve=False)
        super(GitDependency, self).__init__(*args, **kwargs)

    @classmethod
    def manager_installed(cls, **kwargs):
        r"""Determine if the package manager is installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the package manager is installed.

        """
        return (git is not None)

    @classmethod
    def list(cls, **kwargs):
        r"""List the packages installed by this package manager.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            list: List of package information in dictionaries.

        """
        fstring_tag = kwargs.pop('fstring_tag', None)
        out_unchecked = super(GitDependency, cls).list(**kwargs)
        out = []
        for x in out_unchecked:
            if not ('version' in x or cls.is_git_repo(x['directory'])):
                continue
            if 'version' not in x:
                x['version'] = cls.find_version_commit(
                    x['directory'], fstring_tag=fstring_tag)
            out.append(x)
        return out

    @classmethod
    def is_git_repo(cls, directory):
        r"""Check if a directory contains a valid git repository.

        Args:
            directory (str): Directory to check for a git repository.

        Returns:
            bool, git.Repo: git.Repo instance if directory contains a git
                respository, False otherwise.

        """
        if isinstance(directory, git.Repo):
            return directory
        if not os.path.isdir(directory):
            return False
        try:
            return git.Repo(directory)
        except git.InvalidGitRepositoryError:
            return False

    @classmethod
    def find_version_commit(cls, repo, version=None,
                            fstring_tag='v{version}'):
        r"""Find a commit in a repository corresponding to a version.

        Args:
            repo (str, git.Repo): Git repository or path to directory
                containing a git respository.
            version (str, optional): Version to find a corresponding
                commit for. If not provided, the most recent commit will
                be used.
            fstring_tag (str, optional): Format string that should be
                used to turn versions into tags. Defaults to 'v{version}'

        Returns:
            str: Commit hash.

        """
        open_repo = isinstance(repo, str)
        if open_repo:
            repo = git.Repo(repo)
        if version is None:
            out = repo.commit().hexsha
        else:
            try:
                out = repo.commit(version).hexsha
            except git.BadName:
                tag = fstring_tag.format(version=version)
                out = repo.commit(tag).hexsha
                print('find_version_commit', version, tag, out)
                import pdb
                pdb.set_trace()
        if open_repo:
            repo.close()
        return out

    def determine_install_method(self):
        r"""Determine what installation method should be used for this
        dependency.

        Returns:
            str, type: Installation method or package manager class.

        """
        try:
            if 'buildfile' not in self.extra_kwargs:
                self._clone_repo()
        except DependencyError:
            pass
        return super(GitDependency, self).determine_install_method()

    def check_validity(self, **kwargs):
        r"""Check if the dependency can be installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyValidationError: If the dependency cannot be
                installed.

        """
        if (((not self.overwrite) and os.path.isdir(self.directory)
             and (not self.is_git_repo(self.directory)))):
            self.accumulate_error(
                DependencyValidationError,
                f'Directory "{self.directory}" already exists, but it is '
                f'not a valid git respository and overwrite is not set'
            )
        super(GitDependency, self).check_validity(**kwargs)

    def search(self, **kwargs):
        r"""Search for the current version of the dependency if one
        exists.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Raises:
            DependencyError: If the package is not installed.

        Returns:
            dict: Parameters of package.

        """
        kwargs.setdefault('fstring_tag', self.fstring_tag)
        kwargs.setdefault('directory', self.directory)
        return super(GitDependency, self).search(**kwargs)

    @property
    def version_commit(self):
        r"""str: Version commit for the dependency repository"""
        if not hasattr(self, '_version_commit'):
            if self.commit:
                self._version_commit = self.commit
            else:
                self._version_commit = self.find_version_commit(
                    self.directory, version=self.version,
                    fstring_tag=self.fstring_tag)
        return self._version_commit

    @property
    def version_parts(self):
        r"""dict: Parts of parsed version string."""
        out = super(GitDependency, self).version_parts
        if not all('ver_orig' in x for x in out.get('constraints', [])):
            repo = self.is_git_repo(self.directory)
            if repo:
                for x in out.get('constraints', []):
                    x['ver_orig'] = x['ver']
                    x['ver'] = self.find_version_commit(
                        repo, x['ver_orig'], fstring_tag=self.fstring_tag)
                repo.close()
        return out

    @classmethod
    def compare_versions(cls, a, b, op='==', repo=None, **kwargs):
        r"""Compare two commit hash strings.

        Args:
            a (str): Commit has string.
            b (str): Commit has string.
            op (str, optional): Operator to use for comparison.
            repo (git.Repo): Git repository object containing the two
                commit.
            **kwargs: Additional keyword arguments are passed to
                compare_versions.
        
        Returns:
            bool: True if the comparison is true, False otherwise. For
                the commits, commit 'a' is considered greater than commit
                'b' if 'b' is an ancestor to a.

        """
        assert repo
        if '=' in op and a == b:
            return True
        if '>' in op:
            return repo.is_ancestor(b, a)
        return repo.is_ancestor(a, b)

    def check_version(self, version, base_version=None, repo=None,
                      fstring_tag=None, **kwargs):
        r"""Check if a version string satisfies the version constraints.

        Args:
            version (str): Version string to check against constraints.
            base_version (str, optional): Alternate version string that
                version should be compared against for equality.
            repo (str, git.Repo, optional): Git repository or path to
                directory containing a git respository that should be
                used to get the commit corresponding to version. If not
                provided, the instance repository will be used.
            fstring_tag (str, optional): Format string that should be used
                to turn version into a tag that can be searched for in
                repo. Defaults to the instance property of the same name.
            **kwargs: Additional keyword arguments are passed to the
                parent method.

        Returns:
            bool: True if version satisfies the constraints, False
                otherwise.

        """
        if not (self.version and version):
            return True
        if repo is None:
            repo = self.directory
        repo = self.is_git_repo(self.directory)
        if not repo:
            return False
        if fstring_tag is None:
            fstring_tag = self.fstring_tag
        version_commit = self.find_version_commit(
            repo, version, fstring_tag=fstring_tag)
        if base_version:
            base_version = self.find_version_commit(
                repo, base_version)
        out = super(GitDependency, self).check_version(
            version_commit, base_version=base_version,
            repo=repo, **kwargs)
        repo.close()
        return out

    def _clone_repo(self, context=None):
        if ((self.overwrite and os.path.isdir(self.directory)
             and not self.is_git_repo(self.directory))):
            if context != 'install':
                if not self.ask_user(f'Overwrite existing directory '
                                     f'"{self.directory}" so that '
                                     f'{self.package} can be cloned via '
                                     f'{self._package_manager}?'):
                    return
            shutil.rmtree(self.directory)
            self.overwrite = False
        maxver = None
        if self.version and not (self.tag or self.commit):
            maxver = self.version_max
            if maxver:
                self.tag = self.fstring_tag.format(version=maxver)
                maxver = None
            elif 'max' in self.version_parts:
                maxver = self.version_parts['max']
            else:
                self.tag = True
        try:
            repo = yamlfile.clone_github_repo(
                self.repository,
                commit=self.commit, branch=self.branch, tag=self.tag,
                repository_dir=self.directory, return_repo=True,
                is_private=self.is_private,
            )
        except git.GitCommandError as e:
            raise DependencyError(
                f'Failed to clone {self.repository}. Error:\n{e}')
        if maxver:
            self.tag = sorted(
                repo.tags, key=lambda t: t.commit.committed_datetime)[-1]
            repo.git.checkout(self.tag)
        self._version_commit = self.find_version_commit(
            repo, fstring_tag=self.fstring_tag
        )
        repo.close()

    def _install(self, **kwargs):
        self._clone_repo(context='install')
        super(GitDependency, self)._install(**kwargs)

    def _uninstall(self, **kwargs):
        super(GitDependency, self)._uninstall(**kwargs)
        if not os.path.isdir(self.directory):
            raise DependencyError(f'Cannot uninstall {self.directory} '
                                  f'because it does not exist')
        if (not self.preserve) and os.path.isdir(self.directory):
            shutil.rmtree(self.directory)


class CommandDependency(ManagedDependencyBase):
    r"""Dependency installed via a user defined command.

    Args:
        command (list): Command arguments.
        command_uninstall (list, optional): Command arguments used to
            uninstall the dependency.

    """

    _package_manager = 'command'
    _schema_subtype_description = (
        "Dependency installed via user supplied command")
    _schema_properties = {
        'command': {
            'type': 'array',
            'items': {'type': 'string'},
        },
        'command_uninstall': {
            'type': 'array',
            'items': {'type': 'string'},
        }
    }
    _schema_required = ['package', 'command']
    installable_from_source = True

    @classmethod
    def manager_executable(cls, **kwargs):
        r"""Executable used for installation command.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            str: Path to the installation executable.
        
        """
        raise NotImplementedError

    @classmethod
    def manager_installed(cls, **kwargs):
        r"""Determine if the package manager is installed.

        Args:
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the package manager is installed.

        """
        return True

    @classmethod
    def list(cls, package=None, invalidate_cache=False, **kwargs):
        r"""List the packages installed by this package manager.

        Args:
            package (str, optional): Name of package to restrict list to.
            invalidate_cache (bool, optional): If True, invalidate any
                existing cached list and generate a new one. If False,
                use any existing cached result.
            **kwargs: Additional keyword arguments are passed to
                parse_list.

        Returns:
            list: List of package information in dictionaries.

        """
        if package:
            return [{'name': package}]
        return []
        
    def check_installed(self, **kwargs):
        r"""Check if the dependency is installed.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent method and the method of the members.

        Raises:
            DependencyInstalledError: If the dependency is not installed.

        """
        out = super(CommandDependency, self).check_installed(**kwargs)
        if not (self.products or self._install_called):
            self.accumulate_error(
                DependencyInstalledError,
                'No products identified and install not called during '
                'this session'
            )
        return out

    def is_appendable(self, solf):
        r"""Determine if this dependency can be installed at the same
        time as another dependency.

        Args:
            solf (ManagedDependencyBase): Dependency to compare against.

        Returns:
            bool: True if solf can be appended to this dependency, False
                otherwise.

        """
        return False

    def check_version(self, version, base_version=None, **kwargs):
        r"""Check if a version string satisfies the version constraints.

        Args:
            version (str): Version string to check against constraints.
            base_version (str, optional): Alternate version string that
                version should be compared against for equality.
            **kwargs: Additional keyword arguments are passed to
                compare_versions.

        Returns:
            bool: True if version satisfies the constraints, False
                otherwise.

        """
        return True

    def install_command(self, always_yes=_default_always_yes):
        r"""Get the command arguments for installing the package.

        Args:
            always_yes (bool, optional): If True, the installation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        out = copy.deepcopy(self.command)
        if self.arguments:
            out += self.arguments
        return out

    def uninstall_command(self, always_yes=_default_always_yes):
        r"""Get the command arguments for uninstalling the package.

        Args:
            always_yes (bool, optional): If True, the uninstallation will
                not ask for user confirmation. Defaults to False.

        Returns:
            list: Set of command arguments.

        """
        if not self.command_uninstall:
            raise DependencyError(f'Uninstall command not provided for '
                                  f'package {self.package}')
        out = copy.deepcopy(self.command_uninstall)
        if self.arguments_uninstall:
            out += self.arguments_uninstall
        return out
