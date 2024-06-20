import os
import re
import six
import copy
import glob
import logging
import subprocess
import shutil
import sysconfig
import warnings
import pprint
import uuid
import itertools
from collections import OrderedDict
from yggdrasil import platform, tools, scanf, constants
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.components import import_component, ComponentMeta


logger = logging.getLogger(__name__)
if platform._is_win:
    logger.setLevel(level=logging.DEBUG)
_tool_types = [
    'compiler', 'linker', 'archiver', 'disassembler',
    'builder', 'configurer',
]
_all_toolsets = [
    'gnu', 'msvc', 'llvm',
]
_default_libtype = 'static'
_conda_prefix = tools.get_conda_prefix()
_venv_prefix = tools.get_venv_prefix()
_system_suffix = ""
if _conda_prefix is not None:
    _system_suffix += '_' + os.path.basename(_conda_prefix)
if _venv_prefix is not None:
    _system_suffix += '_' + os.path.basename(_venv_prefix)
_library_types = ['include', 'static', 'shared', 'windows_import']


def get_OSX_SYSROOT():
    r"""Determin the path to the OSX SDK.

    Returns:
        str: Full path to the SDK directory if one is located. None
            otherwise.

    """
    fname = None
    if platform._is_mac:
        from yggdrasil.config import ygg_cfg
        try:
            xcode_dir = subprocess.check_output(
                'echo "$(xcode-select -p)"', shell=True).decode("utf-8").strip()
        except BaseException:  # pragma: debug
            xcode_dir = None
        fname_try = []
        cfg_sdkroot = ygg_cfg.get('c', 'macos_sdkroot', None)
        if cfg_sdkroot:
            fname_try.append(cfg_sdkroot)
        if os.environ.get('SDKROOT', False):
            fname_try.append(os.environ['SDKROOT'])
        if xcode_dir is not None:
            bases_try = [
                os.path.join(xcode_dir, 'SDKs', 'MacOSX%s.sdk'),
                os.path.join(xcode_dir, 'Platforms',
                             'MacOSX.platform', 'Developer',
                             'SDKs', 'MacOSX%s.sdk')]
            vers_try = ['11.0', '']  # 11.0 used by conda-forge
            if os.environ.get('MACOSX_DEPLOYMENT_TARGET', False):
                vers_try.insert(0, os.environ['MACOSX_DEPLOYMENT_TARGET'])
            for v in vers_try:
                fname_try += [x % v for x in bases_try]
        for fcheck in fname_try:
            if os.path.isdir(fcheck):
                fname = fcheck
                break
    return fname


_osx_sysroot = get_OSX_SYSROOT()


class CompilationToolError(Exception):
    r"""Class for errors related to compilation tools"""
    pass


class InvalidCompilationTool(CompilationToolError):
    r"""Class for invalid compilation tools"""
    pass


class CompilationToolRegistry(object):

    sorting_keys = ['tooltype', 'language', 'toolset']

    def __init__(self):
        for k in self.sorting_keys + ['aliases']:
            setattr(self, k, OrderedDict(
                [(k, OrderedDict()) for k in _tool_types]))
        self._bases = {}

    def _init_languages(self, languages, driver=None):
        if not isinstance(languages, list):
            languages = [languages]
        for x in languages:
            if driver and x == driver.language:
                continue
            if x not in self.language:
                import_component('model', x)

    def _check_toolname(self, tooltype, toolname):
        if toolname in self.tooltype[tooltype]:
            return toolname
        return self.aliases[tooltype].get(toolname, toolname)

    def _toolnames(self, tooltype, toolname):
        out = [toolname, os.path.basename(toolname),
               os.path.splitext(os.path.basename(toolname))[0]]
        if platform._is_win:
            out += [x.lower() for x in out.copy()]
        out = list(set([self._check_toolname(tooltype, x) for x in out]))
        return out

    def _check_tooltype(self, tooltype, driver=None):
        if tooltype == 'basetool':
            if driver:
                tooltype = driver.basetool
        if tooltype not in _tool_types:
            raise InvalidCompilationTool(f"tooltype '{tooltype}' is not "
                                         f"supported. This keyword must "
                                         f"be one of {_tool_types}")
        return tooltype

    def _check_driver(self, language=None, driver=None,
                      skip_driver=False):
        if driver and language and language != driver.language:
            driver = None
        elif driver:
            language = driver.language
            if not language:
                raise InvalidCompilationTool(f"Driver {driver} does not "
                                             f"does not have a language "
                                             f"set")
        if language and (not skip_driver) and (not driver):
            driver = import_component('model', language)
        return (language, driver)

    def _check_return(self, tooltype, out,
                      default=tools.InvalidDefault(), **kwargs):
        if out is not None and self._matches(out, **kwargs):
            return out
        if not isinstance(default, tools.InvalidDefault):
            return default
        raise InvalidCompilationTool(
            f"Could not locate a {tooltype} that matches {kwargs}.\n"
            f"Available tools:\n{pprint.pformat(self.tooltype)}")

    def _sorting_kws(self, tooltype, toolname=None, language=None,
                     toolset=None,
                     only_installed=None, dont_check_executable=None,
                     compatible_with=None):
        out = dict(toolname=toolname,
                   language=language,
                   toolset=toolset,
                   only_installed=only_installed,
                   dont_check_executable=dont_check_executable)
        out = {k: v for k, v in out.items() if v is not None}
        if compatible_with:
            assert not toolset
            if isinstance(compatible_with, str):
                if not isinstance(tooltype, list):
                    tooltype = [tooltype]
                compatible_tooltypes = list(tooltype)
                compatible_tooltypes += [
                    k for k in _tool_types
                    if k not in compatible_tooltypes]
                compatible_with = self.tool(
                    compatible_tooltypes, toolname=compatible_with,
                    only_installed=only_installed)
            out['toolset'] = compatible_with.toolset
        return out

    def _key2attr(self, cls, key):
        key2attr = {
            'tooltype': 'tooltype',
            'language': ('build_language' if cls.is_build_tool
                         else 'languages'),
            'toolset': 'compatible_toolsets',
        }
        src = getattr(cls, key2attr[key])
        return src if isinstance(src, list) else [src]

    def _register(self, cls, key):
        dst = getattr(self, key)
        if key != 'tooltype':
            dst = dst[cls.tooltype]
        src = self._key2attr(cls, key)
        for x in src:
            dst.setdefault(x, OrderedDict())
            if cls.toolname in dst[x]:
                raise CompilationToolError(
                    f"{cls.tooltype.title()} toolname {cls.toolname} "
                    f"already register for {key} '{x}' "
                    f"(class = {cls}, existing = "
                    f"{dst[x][cls.toolname]})")
            dst[x][cls.toolname] = cls

    def _matches(self, cls, toolname=None, only_installed=False,
                 dont_check_executable=False, **kwargs):
    
        def _log(name, exp, act):
            logger.debug(f"NO MATCH {cls} [{name}]: {act} vs. {exp}")
    
        if not cls:
            return False
        tooltype = kwargs.get('tooltype', cls.tooltype)
        if toolname and cls.toolname not in self._toolnames(tooltype,
                                                            toolname):
            _log("toolname", self._toolnames(tooltype, toolname),
                 cls.toolname)
            return False
        if platform._platform not in cls.platforms:
            _log("platform", platform._platform, cls.platforms)
            return False
        if only_installed and not cls.is_installed():
            _log("only_installed", only_installed, cls.is_installed())
            return False
        for k, v in kwargs.items():
            if k not in self.sorting_keys:
                print("UNSUPORTED KEY", k, v)
                continue
            if isinstance(v, list):
                if not (set(v) & set(self._key2attr(cls, k))):
                    _log(k, set(v), set(self._key2attr(cls, k)))
                    return False
            elif v and v not in self._key2attr(cls, k):
                _log(k, v, self._key2attr(cls, k))
                return False
        if ((toolname and (not dont_check_executable)
             and (os.path.isfile(toolname) or shutil.which(toolname)))):
            outnames = [cls.toolname,
                        cls.get_executable(),
                        cls.get_executable(full_path=True)]
            if platform._is_win:
                outnames += [x.lower() for x in outnames.copy()]
            toolname_version = cls.tool_version(executable=toolname)
            cls_version = cls.tool_version()
            if ((toolname not in outnames
                 and not (platform._is_win
                          and (toolname.lower() in
                               [x.lower() for x in outnames]))
                 and (toolname_version != cls_version))):
                _log("executable", toolname, outnames)
                raise CompilationToolError(
                    f"Provided executable ({toolname}) "
                    f"conflicts with the class-defined executable "
                    f"({cls.get_executable()})\n"
                    f"Provided version:\n{toolname_version}\n"
                    f"Class version:\n{cls_version}")
        return True

    def _lookup(self, tooltype, return_all=False, **kwargs):
        matches = set(self.tooltype[tooltype].keys())
        for k, v in kwargs.items():
            if k not in self.sorting_keys:
                continue
            reg = getattr(self, k)[tooltype].get(v, {})
            matches &= set(reg.keys())
        out = None
        if return_all:
            out = []
        if matches:
            for k in matches:
                v = self.tooltype[tooltype][k]
                if self._matches(v, **kwargs):
                    if return_all:
                        out.append(v)
                    else:
                        return v
        return out

    def _toolname(self, tooltype, driver):
        out = getattr(driver, tooltype, None)
        if not out:
            out = getattr(driver, f'default_{tooltype}', None)
        return out

    def _flags(self, tooltype, driver):
        out = getattr(driver, f'{tooltype}_flags', None)
        if out is None:
            out = getattr(driver, f'default_{tooltype}_flags', None)
        return out

    def tooltypes(self, basetool):
        r"""Determine the tooltypes given a base tool type.

        Args:
            basetool (str): Base tool type.

        Returns:
            list: All tooltypes involved with a base tool.

        """
        out = [basetool]
        out += self._bases[basetool].associated_tooltypes
        return out

    def invalid_tooltypes(self, basetool):
        r"""Determine the tools that are invalid given a base tool type.

        Args:
            basetool (str): Base tool type.

        Returns:
           list: All tooltypes not involved with a base tool.

        """
        tooltypes = self.tooltypes(basetool)
        return [x for x in _tool_types if x not in tooltypes]

    def register(self, cls):
        r"""Register a compilation class.

        Args:
            cls (CompilationToolBase): Tool class to register.

        """
        if cls.toolname is None:
            if cls.tooltype not in self._bases:
                self._bases[cls.tooltype] = cls
            return
        cls.before_registration(cls)
        if cls._dont_register:
            return
        if cls.toolname in cls.aliases:  # pragma: debug
            raise CompilationToolError(
                f"The name '{cls.toolname}' for class {cls} is also "
                f"in its list of aliases: {cls.aliases}")
        for k in cls.aliases:
            self.aliases[cls.tooltype][k] = cls.toolname
        for k in self.sorting_keys:
            self._register(cls, k)

    def registry(self, tooltype, languages=[]):
        r"""Return the registry containing compilation tools of the
        specified type.

        Args:
            tooltype (str): Type of tool. Valid values include 'compiler',
                'linker', 'archiver', 'disassembler', 'builder', and
                 'configurer'.
            languages (list, optional): List of languages that should be
                imported prior to returning the registry, thereby
                populating the compilation tools for that language.

        Returns:
            collections.OrderedDict: Registry for specified type.

        Raises:
            InvalidCompilationTool: If tooltype is not a valid value (i.e.
                'compiler', 'linker', 'archiver', 'disassembler',
                'builder', and 'configurer').

        """
        tooltype = self._check_tooltype(tooltype)
        self._init_languages(languages)
        if isinstance(languages, list):
            for x in languages:
                if x not in self.language[tooltype]:
                    import_component('model', x)
        return self.tooltype[tooltype]

    def toolname(self, tooltype, language=None, driver=None,
                 skip_driver=False, **kwargs):
        r"""Locate a tool that matches the specified parameters,
        prioritizing classes according to configuration parameters.

        Args:
            tooltype (str, list): Type of tool that should be located.
                If a list is provided, they each will be searched for in
                order with the first match returned.
            language (str): Language that the located tool should handle.
            driver (CompilationModelDriver, optional): Driver that should
                be used to help locate the tool.
            skip_driver (bool, optional): If True, don't load the driver
                for the specified language to prevent circular imports.
            **kwargs: Additional keyword arguments are passed to self.tool

        Returns:
            str: Name of the tool matching the provided parameters.

        Raises:
            InvalidCompilationTool: If an invalid tooltype is provided.
            InvalidCompilationTool: If a tool cannot be located that
                matches the specified parameters and default is not
                provided.
            CompilationToolError: If dont_check_executable is False and
                the executable indicated by toolname does not match the
                executable associated with the returning class.

        """
        language, driver = self._check_driver(
            language=language, driver=driver, skip_driver=skip_driver)
        out = self.tool(tooltype, language=language, driver=driver,
                        skip_driver=skip_driver, **kwargs)
        if isinstance(out, (CompilationToolMeta,
                            CompilationToolBase)):
            out = out.toolname
        return out

    def tool_flags(self, tooltype, toolname=None, language=None,
                   driver=None, skip_driver=False, **kwargs):
        r"""Get the flags associated with the tool matching the provided
        parameters.

        Args:
            tooltype (str, list): Type of tool that should be located.
                If a list is provided, they each will be searched for in
                order with the first match returned.
            toolname (str, optional): Name of tool to locate.
            language (str, optional): Language that the located tool
                should handle.
            driver (CompilationModelDriver, optional): Driver that should
                be used to help locate the tool.
            skip_driver (bool, optional): If True, don't load the driver
                for the specified language to prevent circular imports.
            **kwargs: Additional keyword arguments will be based to
                tool_instance.
        Returns:
            list: Flags associated with the tool.

        """
        language, driver = self._check_driver(
            language=language, driver=driver, skip_driver=skip_driver)
        out = self.tool_instance(tooltype, toolname=toolname,
                                 language=language, driver=driver,
                                 skip_driver=skip_driver, **kwargs)
        if isinstance(out, CompilationToolBase):
            out = getattr(out, 'flags', [])
        return out

    def tool_instance(self, tooltype, toolname=None, language=None,
                      toolset=None, only_installed=False,
                      driver=None, skip_driver=False,
                      compatible_with=None,
                      default=tools.InvalidDefault(),
                      dont_check_executable=False, **kwargs):
        r"""Locate a tool that matches the specified parameters,
        prioritizing classes according to configuration parameters and
        create an instance.

        Args:
            tooltype (str, list): Type of tool that should be located.
                If a list is provided, they each will be searched for in
                order with the first match returned.
            toolname (str, optional): Name of tool to locate.
            language (str, optional): Language that the located tool
                should handle.
            toolset (str, optional): Toolset that the located tool
                should be compatible with.
            only_installed (bool, optional): If True, only installed
                tools should be returned.
            driver (CompilationModelDriver, optional): Driver that should
                be used to help locate the tool.
            skip_driver (bool, optional): If True, don't load the driver
                for the specified language to prevent circular imports.
            compatible_with (CompilationToolBase, optional): Tool that
                the located tool should be compatible with.
            default (object, optional): Value that should be returned if
                a tool cannot be located.
            dont_check_executable (bool, optional): If True and an
                executable is provided by toolname, don't raise an error
                if the returned class's executable does not match the
                one provided.
            **kwargs: Additional keyword arguments are used to initialize
                the instance.

        Returns:
            CompilationToolBase: Compilation tool instance.

        Raises:
            InvalidCompilationTool: If an invalid tooltype is provided.
            InvalidCompilationTool: If a tool cannot be located that
                matches the specified parameters and default is not
                provided.

        """
        language, driver = self._check_driver(
            language=language, driver=driver, skip_driver=skip_driver)
        sorting_kws = self._sorting_kws(
            tooltype, toolname=toolname, language=language,
            toolset=toolset, only_installed=only_installed,
            dont_check_executable=None,
            compatible_with=compatible_with)
        out = None
        if driver:
            out = getattr(driver, f'{tooltype}_tool', None)
            if not self._matches(
                    out, dont_check_executable=dont_check_executable,
                    **sorting_kws):
                out = None
                if not toolname:
                    toolname = self.toolname(
                        tooltype, driver=driver, skip_driver=skip_driver,
                        default=None, **sorting_kws)
                    if toolname:
                        sorting_kws['toolname'] = toolname
        if not out:
            out = self.tool(tooltype,
                            driver=driver, skip_driver=skip_driver,
                            default=None, dont_check_executable=True,
                            **sorting_kws)
        if isinstance(out, CompilationToolMeta):
            if driver:
                kwargs.setdefault('flags', self._flags(tooltype, driver))
                if toolname and not kwargs.get('executable', None):
                    if hasattr(driver, 'cfg'):
                        kwargs['executable'] = driver.cfg.get(
                            language, f'{toolname}_executable', None)
                    else:
                        kwargs['executable'] = None
                for k in out.associated_tooltypes:
                    kwargs.setdefault(k, self._toolname(k, driver))
                    kwargs.setdefault(f'{k}_flags',
                                      self._flags(k, driver))
            if ((toolname and not kwargs.get('executable', None)
                 and (os.path.isfile(toolname)
                      or shutil.which(toolname)))):
                kwargs['executable'] = toolname
            out = out(**kwargs)
        return self._check_return(
            tooltype, out, default=default,
            dont_check_executable=dont_check_executable,
            **sorting_kws)

    def tool(self, tooltype, toolname=None, language=None,
             toolset=None, only_installed=False,
             driver=None, skip_driver=False,
             compatible_with=None, dont_check_executable=False,
             default=tools.InvalidDefault()):
        r"""Locate a tool that matches the specified parameters.

        Args:
            tooltype (str, list): Type of tool that should be located.
                If a list is provided, they each will be searched for in
                order with the first match returned.
            toolname (str, optional): Name of tool to locate.
            language (str, optional): Language that the located tool
                should handle.
            toolset (str, optional): Toolset that the located tool
                should be compatible with.
            only_installed (bool, optional): If True, only installed
                tools should be returned.
            driver (CompilationModelDriver, optional): Driver that should
                be used to help locate the tool.
            skip_driver (bool, optional): If True, don't load the driver
                for the specified language to prevent circular imports.
            compatible_with (CompilationToolBase, optional): Tool that
                the located tool should be compatible with.
            dont_check_executable (bool, optional): If True and an
                executable is provided by toolname, don't raise an error
                if the returned class's executable does not match the
                one provided.
            default (object, optional): Value that should be returned if
                a tool cannot be located.

        Returns:
            CompilationToolBase: Compilation tool class.

        Raises:
            InvalidCompilationTool: If an invalid tooltype is provided.
            InvalidCompilationTool: If a tool cannot be located that
                matches the specified parameters and default is not
                provided.
            CompilationToolError: If dont_check_executable is False and
                the executable indicated by toolname does not match the
                executable associated with the returning class.

        """
        language, driver = self._check_driver(
            language=language, driver=driver, skip_driver=skip_driver)
        sorting_kws = self._sorting_kws(
            tooltype, toolname=toolname, language=language,
            toolset=toolset, only_installed=only_installed,
            dont_check_executable=dont_check_executable,
            compatible_with=compatible_with)
        out = None
        if isinstance(tooltype, list):
            for x in tooltype:
                out = self.tool(x, default=None,
                                driver=driver, skip_driver=skip_driver,
                                **sorting_kws)
                if out:
                    return out
            return self._check_return(tooltype, out, default=default,
                                      **sorting_kws)
        tooltype = self._check_tooltype(tooltype, driver=driver)
        if language and not skip_driver:
            self._init_languages([language], driver=driver)
        # Direct search for a specific tool
        if toolname:
            for x in self._toolnames(tooltype, toolname):
                if x in self.tooltype[tooltype]:
                    out = self.tooltype[tooltype][x]
                    break
            return self._check_return(tooltype, out, default=default,
                                      **sorting_kws)
        # Check attributes on the associated driver which will include
        # configuration values
        if (not out) and driver and (not toolname):
            driver_toolname = self._toolname(tooltype, driver)
            if driver_toolname:
                out = self.tool(tooltype, toolname=driver_toolname,
                                driver=driver, default=None,
                                **sorting_kws)
        # Look for the base tool and use it's attributes
        if (not out) and self._bases[tooltype].basetooltype:
            base = self.tool(self._bases[tooltype].basetooltype,
                             driver=driver, skip_driver=skip_driver,
                             default=None, **sorting_kws)
            if base and getattr(base, f'default_{tooltype}', None):
                out = self.tool(tooltype,
                                getattr(base, f'default_{tooltype}'),
                                driver=driver, skip_driver=skip_driver,
                                default=None, **sorting_kws)
        # Brute force search for a matching tool
        if not out:
            out = self._lookup(tooltype, **sorting_kws)
        return self._check_return(tooltype, out, default=default,
                                  **sorting_kws)


_tool_registry = CompilationToolRegistry()


def get_tool_registry(languages=None):
    r"""Get the global tool registry.

    Args:
        languages (list, optional): Languages that should be initialized
            before returning the registry.

    Returns:
        CompilationToolRegistry: Global tool registry.
    
    """
    global _tool_registry
    if languages:
        _tool_registry._init_languages(languages)
    return _tool_registry


def is_windows_import(fname, **kwargs):
    r"""Check if a library is a windows import library.

    Args:
        fname (str): Full path to file to check.

    Returns:
        bool: True if fname is a windows import, False otherwise.

    """
    assert os.path.isfile(fname)
    if not fname.endswith('.lib'):
        return fname.endswith('.dll.a')
    base = os.path.splitext(os.path.basename(fname))[0] + '.dll'
    return bool(DumpBinDisassembler.find_component(
        fname, base, component_types='imported_libraries', **kwargs))


def create_windows_import(dll, dst=None, for_gnu=False, overwrite=False,
                          directory=None):
    r"""Convert a window's .dll library into a static library.

    Args:
        dll (str): Full path to .dll library to convert.
        ext (str): Extension of the file to create.
        dst (str, optional): Full path to location where the new
            library should be saved. Defaults to None and will be
            set based on lib and will be placed in specified directory
            (or the same directory as dll if directory not provided).
        for_gnu (bool, optional): If True, a GNU compatible windows import
            library with extension .dll.a will be created. Defaults to
            False.
        overwrite (bool, optional): If True, the static file will
            be created even if it already exists. Defaults to False.
        directory (str, optional): Full path to the directory that the
            result should be placed in. If not provided, the directory
            containing the dll will be used.

    Returns:
        str: Full path to new .a static library.

    """
    # https://sourceforge.net/p/mingw-w64/wiki2/
    # Answer%20generation%20of%20DLL%20import%20library/
    if for_gnu:
        ext = '.dll.a'
    else:
        ext = '.lib'
    assert ext in ['.dll.a', '.lib']
    base = DependencyRegistry.splitext(os.path.basename(dll))[0]
    if dst is None:
        libbase = base
        if ext == '.dll.a' and not libbase.startswith('lib'):
            libbase = 'lib' + libbase
        elif ext == '.lib' and libbase.startswith('lib'):
            libbase = libbase[3:]
        if directory is None:
            directory = os.path.dirname(dll)
        dst = os.path.join(directory, libbase + ext)
    logger.info(f"create_windows_import: Creating a {dst} from {dll}")
    if (not os.path.isfile(dst)) or overwrite:
        gendef = shutil.which("gendef")
        dlltool = shutil.which("dlltool")
        if gendef and dlltool:
            subprocess.check_call([gendef, dll])
            subprocess.check_call(
                [dlltool, '-D', dll, '-d', f'{base}.def', '-l', dst])
            assert os.path.isfile(dst)
            logger.info(f"create_windows_import: Created {dst}")
        else:
            warnings.warn(f"create_windows_import: gendef ({gendef}) or "
                          f"dlltool ({dlltool}) missing. Cannot create "
                          f"windows import library for {dll}")
            dst = None
    return dst


class DependencyRegistry(object):
    r"""Container for language dependencies.

    Args:
        language (str): Language associated with the registry.
        internal (dict, optional): Internal dependencies.
        external (dict, optional): External dependencies.
        standard (dict, optional): Standard dependencies.
        **kwargs: Additional keyword arguments are passed to add_group for
           each group of dependencies.

    """

    def __init__(self, language, internal=None, external=None,
                 standard=None, **kwargs):
        self.specialization = DependencySpecialization()
        self.language = language
        self.cfg = kwargs.get('cfg', None)
        self.libraries = OrderedDict()
        self._driver = kwargs.get('driver', None)
        self._basetool = kwargs.get('basetool', None)
        if isinstance(self._basetool, str):
            self._basetool = None
        self.add_group('internal', internal, **kwargs)
        self.add_group('external', external, **kwargs)
        self.add_group('standard', standard, **kwargs)

    @property
    def driver(self):
        r"""CompilerModelDriver: Driver associated with this registry's
        language."""
        if self._driver is None:
            self._driver = import_component('model', self.language)
        return self._driver

    def add_group(self, origin, group, **kwargs):
        r"""Add libraries from a group to the registry.

        Args:
            origin (str): String describing if the group contains
                libraries that are a language standard, external, or
                yggdrasil internal library.
            group (dict, optional): Mapping of libraries in a group.
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency for each dependency.

        """
        if not group:
            return
        for k, v in group.items():
            if platform._platform not in v.get(
                    'platforms', platform._supported_platforms):
                continue
            v['origin'] = origin
            v.setdefault('name', k)
            v.setdefault('language', self.language)
            self[k] = dict(kwargs, **v)

    def keys(self):
        r"""iterable: Keys in the registry."""
        return self.libraries.keys()

    def values(self):
        r"""iterable: Values in the registry."""
        return self.libraries.values()

    def items(self):
        r"""iterable: Key/value pairs in the registry."""
        return self.libraries.items()

    def __len__(self):
        return len(self.libraries)

    def __str__(self):
        return str(self.libraries)

    def __repr__(self):
        return f"DependencyRegistry({str(self)})"

    def __contains__(self, value):
        if isinstance(value, CompilationDependency):
            for v in self.libraries.values():
                if value == v:
                    return True
            return False
        elif isinstance(value, tuple) and value[0] == self.language:
            return value[1] in self.libraries
        return value in self.libraries

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def set(self, key, value, only_installed=False, only_enabled=False):
        r"""Add a dependency to the registry if it's not already present.

            key (str): Key to assign value to in the registry.
            value (dict, CompilationDependency): Dependency or dependency
                parameters to add.
            only_installed (bool, optional): If True, only add dep if it
                is installed.
            only_enabled (bool, optional): If True, only add dep if it is
                enabled for the current specialization.

        """
        if isinstance(value, dict):
            value.setdefault('name', key)
            value.setdefault('language', self.language)
            value = CompilationDependency(**value)
        if not self.specialization.is_empty:
            value = value.specialized(**self.specialization.subspec)
        if value in self:
            return
        if only_installed and not value.is_installed:
            return
        if only_enabled and value.is_disabled:
            warnings.warn(f"{value} disabled")
            return
        self.libraries[value.name] = value

    def get(self, name, default=tools.InvalidDefault()):
        r"""Get the class associated with a dependency.

        Args:
            name (str): Name of the dependency to return.
            default (obj, optional): Default to return if the dependency
                cannot be located.

        Returns:
            :class:CompilationDependency: Dependency information.

        """
        if isinstance(name, CompilationDependency):
            return name
        language = self.language
        if isinstance(name, tuple):
            language, name = name
        key = os.path.basename(self.splitext(name)[0])
        if key.startswith('lib'):
            key = key[3:]
        if '.' in key:
            key = key.split('.')[0]
        if key in self.libraries:
            return self.libraries[key]
        if language != self.language:
            key = (language, key)
            drv = import_component('model', language)
            spec_libs = drv.libraries.specialized(
                **self.specialization.subspec)
            return spec_libs.get(key[1], default=default)
        if self.add_compiler_libraries():
            return self.get(name, default=default)
        if not isinstance(default, tools.InvalidDefault):
            return default
        raise KeyError(f"Could not locate a {self.language} dependency "
                       f"with the name {key} (libraries = "
                       f"{list(self.libraries.keys())})")

    def getfile(self, name, filetype=None, default=tools.InvalidDefault(),
                **kwargs):
        r"""Get a library file path for a dependency.

        Args:
            name (str): Name of the dependency to get a file for.
            filetype (str, optional): Type of file to return. If not
                provided, the compilation file will be returned.
            default (str, optional): Value that should be returned if a
                library path does not exist.
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency.get.

        Returns:
            str: Library file path.

        """
        info = self.get(name, default=default)
        if info == default:
            return info
        return info.get(filetype=filetype, default=default, **kwargs)

    def get_group(self, origin):
        r"""Select libraries from the registry that have the requested
        origin.

        Args:
            origin (str): Origin of libraries that should be returned.

        Return:
            dict: Mapping of libraries in the requested group.

        """
        return {k: v for k, v in self.libraries.items()
                if v.origin == origin}

    @classmethod
    def splitext(cls, fname):
        r"""Split a file extension, taking special care for the .dll.a
        windows import extension.

        Args:
            fname (str): File path to split extension for.

        Returns:
            tuple(str, str): File base name and extension.

        """
        if fname.endswith('.dll.a'):
            ext = '.dll.a'
            return fname.rsplit(ext, 1)[0], ext
        base, ext = os.path.splitext(fname)
        while ext and ext.startswith('.') and ext[1:].isnumeric():
            base, ext2 = os.path.splitext(base)
            ext = ext2 + ext
        return (base, ext)

    @property
    def internal(self):
        r"""dict: Mapping of internal libraries."""
        return self.get_group('internal')

    @property
    def external(self):
        r"""dict: Mapping of external libraries."""
        return self.get_group('external')

    @property
    def standard(self):
        r"""dict: Mapping of standard libraries."""
        return self.get_group('standard')

    @property
    def basetool(self):
        r"""CompilationToolBase: Tool associated with this language."""
        if self._basetool is None:
            for v in self.libraries.values():
                if v.language == self.language:
                    self._basetool = v.basetool
                    break
            else:
                self._basetool = False
        return self._basetool

    def add_compiler_libraries(self, basetool=None):
        r"""Add the standard library for the compiler.

        Returns:
            bool: True if any libraries are added, False otherwise.

        """
        if basetool is None:
            basetool = self.basetool
        libs_added = False
        if basetool:
            stdlib = basetool.standard_library
            if stdlib and stdlib not in self:
                kws = {basetool.tooltype: basetool.toolname,
                       'basetool': basetool.toolname}
                self[stdlib] = CompilationDependency(
                    stdlib, 'language', self.language,
                    cfg=self.cfg, driver=self.driver,
                    libtype=basetool.standard_library_type, **kws)
                libs_added = True
            for k, v in basetool.libraries.items():
                if v.get("name", k) not in self:
                    v['cfg'] = self.cfg
                    v.setdefault('origin', 'standard')
                    self[k] = v
                    libs_added = True
        return libs_added

    def specialized(self, **kwargs):
        r"""Return a copy of this record specialized to a specific tool.

        Args:
            **kwargs: Keyword arguments are passed to the specialize
                method for the elements of the copy.

        Returns:
            DependencyList: Specialized copy.

        """
        self.add_compiler_libraries()
        spec = DependencySpecialization(self.specialization, **kwargs)
        out = type(self)(self.language, driver=self.driver, cfg=self.cfg,
                         basetool=kwargs.get('basetool', self.basetool))
        out.specialization = spec
        for k, v in self.libraries.items():
            out[k] = v
        out.add_compiler_libraries()
        return out


class DependencySpecialization(object):
    r"""Storage class for dependency specialization.

    Args:
        base (DependencySpecialization, CompilationDependency, optional):
            Specialization that this specialization should be built upon.
        **kwargs: Additional keyword arguments are parsed for
            specialization parameters.

    """

    store_complete = False
    defaults = OrderedDict([
        ('basetool', None),
        ('compiler', None),
        ('linker', None),
        ('archiver', None),
        ('disassembler', None),
        ('builder', None),
        ('configurer', None),
        ('with_asan', False),
        ('with_omp', False),
        ('disable_python_c_api', False),
        ('logging_level', False),
        ('commtype', None),
        ('generalized_suffix', False),
        ('libtype', None),
    ])
    tooltypes = ['basetool'] + _tool_types
    target_param = [
        'with_asan', 'with_omp', 'disable_python_c_api', 'logging_level',
        'commtype',
    ]
    command_line_param = [
        'with_asan', 'with_omp', 'disable_python_c_api', 'logging_level',
        'commtype', 'dry_run',
    ]
    command_line_options = [
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': "Compile with address sanitizer if available."}),
        (('--with-omp', ),
         {'action': 'store_true',
          'help': "Compile with OpenMP if available."}),
        (('--commtype', ),
         {'type': str,
          'help': ("Type of communicator that compilation should "
                   "use.")}),
        (('--logging-level', ),
         {'type': int,
          'help': ("Level of logging that should be performed by "
                   "the compiled executable.")}),
        (('--dry-run', ),
         {'action': 'store_true',
          'help': ("Don't actually compile anything, including "
                   "dependencies when generating flags")}),
    ]

    def __init__(self, base=None, toolname=None, **kwargs):
        if isinstance(base, CompilationDependency):
            base = getattr(base, 'specialization', None)
        self.values = {}
        self.update(base=base, toolname=toolname, **kwargs)
        
    def update(self, dep=None, base=None, toolname=None, **kwargs):
        if toolname:
            assert kwargs.get('basetool', toolname) == toolname
            kwargs['basetool'] = toolname
        if isinstance(base, DependencySpecialization):
            kwargs = dict(base.values, **kwargs)
        elif isinstance(base, dict):
            kwargs = dict(base, **kwargs)
        for k, v in self.defaults.items():
            if self.store_complete or k in kwargs:
                if k in self.tooltypes:
                    self.settool(k, kwargs.get(k, v), dep=dep)
                else:
                    self.values[k] = kwargs.get(k, v)
        if dep is not None and self['basetool'] is not None:
            basetool = dep.tool('basetool')
            added_tools = [basetool.tooltype] + basetool.associated_tooltypes
            for k in added_tools:
                if self[k] is None:
                    self.settool(k, dep.tool(k).toolname)
            if self['libtype']:
                dep.libtype = self['libtype']
            for k in self.tooltypes:
                if self[k]:
                    dep._library_toolnames[k] = self[k]
        if (not self.is_empty) and self['commtype'] is None:
            self.values['commtype'] = tools.get_default_comm()

    @property
    def is_empty(self):
        r"""bool: True if the speciailization is empty."""
        return all(self[k] == v for k, v in self.defaults.items()
                   if k != 'libtype')

    @property
    def subspec(self):
        r"""dict: Specialization parameters for dependencies."""
        return {k: v for k, v in self.values.items()
                if k not in ['libtype']}

    @property
    def compspec(self):
        r"""dict: Specialization parameters for compilation."""
        return {k: v for k, v in self.values.items()
                if k not in self.tooltypes}

    def __getitem__(self, key):
        return self.values.get(key, self.defaults[key])

    def get(self, key, default=tools.InvalidDefault()):
        r"""Get a specialization value.

        Args:
            key (str): Specialization parameter to return.
            default (object, optional): Value that should be returned if
                a parameter does not exist and the standard default should
                not be used.

        """
        if ((key not in self.values
             and (not isinstance(default, tools.InvalidDefault)))):
            return default
        return self[key]

    def settool(self, key, value, dep=None):
        r"""Initialize a tool parameter.

        Args:
            key (str): Tool parameter name.
            value (str, CompilationToolBase): Tool or tool name.
            dep (CompilationDependency, optional): Dependency that this
                specialization is associated with and should be used to
                locate the appropriate tool.

        """
        assert key in self.tooltypes
        tool = None
        if ((isinstance(value, CompilationToolBase)
             or (isinstance(value, type)
                 and issubclass(value, CompilationToolBase)))):
            tool = value
            value = value.toolname
        assert isinstance(value, (str, type(None)))
        if value and dep is not None:
            if tool is not None:
                if value in dep._updated_tools[key]:
                    assert tool == dep._updated_tools[key][value]
                else:
                    dep._updated_tools[key][value] = tool
            value = dep.locate_tool(key, value).toolname
        if key not in self.values or dep.is_rebuildable:
            self.values[key] = value

    def __eq__(self, other):
        if isinstance(other, dict):
            other = DependencySpecialization(**other)
        if not isinstance(other, DependencySpecialization):
            return False
        return hash(self) == hash(other)

    def check(self, other):
        r"""Check if this dependency would remain unchanged by a set of
        new parameters.

        Args:
            other (dict): New parameters.

        Returns:
            bool: True if the new parameters would not modify the
                specialization, False otherwise.

        """
        other = DependencySpecialization(self, **other)
        out = (other == self)
        # if not out:
        #     logger.info(f"SPECIALIZATION DIFFERS:\n"
        #                 f"EXISTING: {self}\n"
        #                 f"UPDATED:  {other}")
        return out

    @property
    def _tuple(self):
        r"""tuple: Ordered set of parameter values."""
        return tuple([self[k] for k in self.defaults.keys()])

    @classmethod
    def split(cls, kwargs):
        r"""Split the keyword arguments into specification parameters and
        non-specification parameters.

        Args:
            kwargs (dict): Keyword arguments to parse.

        Returns:
            tuple(dict, dict): Specification parameters and
                non-specification parameters.

        """
        spec = {}
        non_spec = {}
        for k, v in kwargs.items():
            if k in cls.defaults:
                spec[k] = v
            else:
                non_spec[k] = v
        return spec, non_spec

    @classmethod
    def select(cls, kwargs, no_remainder=False, no_tools=False,
               for_target=False):
        r"""Select keyword arguments that are specification parameters.

        Args:
            kwargs (dict): Keyword arguments to parse.
            no_remainder (bool, optional): If True, assert that there are
                not any non-parameter keyword arguments present.
            no_tools (bool, optional): If True, don't include tools.
            for_target (bool, optional): If True, only select parameters
                that are preserved for build targets.
            prune_original (bool, optional):

        Returns:
            dict: Keyword arguments that are parameters.

        """
        if no_remainder:
            rem = cls.remainder(kwargs)
            if rem:  # pragma: debug
                pprint.pprint(rem)
            assert not cls.remainder(kwargs)
        if for_target:
            kwargs = {k: v for k, v in kwargs.items()
                      if k in cls.target_param}
        out = {k: kwargs[k] for k in cls.defaults.keys()
               if k in kwargs and ((not no_tools)
                                   or k not in cls.tooltypes)}
        if (not no_tools) and 'toolname' in kwargs:
            assert 'basetool' not in kwargs
            out['basetool'] = kwargs['toolname']
        return out

    @classmethod
    def select_attr(cls, obj, no_tools=False, use_target=False):
        r"""Select object attributes that are specification parameters.

        Args:
            obj (object): Object to take attributes from.
            no_tools (bool, optional): If True, don't include tools.
            use_target (bool, optional): If True, check for target tools.

        Returns:
            dict: Keyword arguments that are parameters.

        """
        keymap = {'logging_level': 'numeric_logging_level'}
        out = {k: getattr(obj, keymap.get(k, k), None)
               for k in cls.defaults.keys()
               if hasattr(obj, keymap.get(k, k))
               and k not in cls.tooltypes}
        if not no_tools:
            if use_target and obj.is_build_tool:
                tooltypes = obj.target_tooltypes
            else:
                tooltypes = obj.tooltypes
            for k in tooltypes:
                if use_target and obj.is_build_tool:
                    out[k] = getattr(obj, f'target_{k}')
                else:
                    out[k] = obj.get_tool_instance(k)
        return out

    @classmethod
    def remainder(cls, kwargs, remove_parameters=False):
        r"""Select keyword arguments that are not specification parameters

        Args:
            kwargs (dict): Keyword arguments to parse.
            remove_parameters (bool, optional): If True, dependency
                parameters will also be removed.

        Returns:
            dict: Keyword arguments that are not parameters.

        """
        out = {k: v for k, v in kwargs.items() if
               (k not in cls.defaults and k != 'toolname')}
        if remove_parameters:
            out = {
                k: v for k, v in out.items() if k not in
                remove_parameters
                + list(CompilationDependency.aliased_parameters.keys())
            }
        return out

    def __str__(self):
        return str({k: self[k] for k in self.defaults.keys()})

    def __repr__(self):
        return f"DependencySpecialization({str(self)})"

    def __hash__(self):
        return hash(self._tuple)

    @classmethod
    def from_command_args(cls, args, ignore=None):
        r"""Get keyword arguments based on parsed command line arguments.

        Args:
            args (Namespace): Parsed command line argument namespace.
            ignore (list, optional): Parameters to ignore.

        Returns:
            dict: Keyword arguments.

        """
        return {k: getattr(args, k, None) for k in
                cls.command_line_param
                if ((getattr(args, k, None) is not None)
                    and ((not ignore) or k not in ignore))}

    @classmethod
    def as_command_flags(cls, kwargs):
        r"""Convert specialization parameter keyword arguments to command
        line flags.

        Args:
            kwargs (dict): Keyword arguments.

        Returns:
            str: Command line flags.

        """
        out = ''
        for k in cls.command_line_param:
            if k not in kwargs:
                continue
            if k in ['logging_level', 'commtype']:
                out += f" --{k.replace('_', '-')}={kwargs[k]}"
            elif kwargs[k]:
                out += f" --{k.replace('_', '-')}"
        return out.strip()


class DependencyList(DependencyRegistry):
    r"""Class for managing a list of dependencies.

    Args:
        language (str): Language associated with the list.
        libraries (list, optional): Libraries that should be added to
            the list.
        driver (CompiledModelDriver, optional): Driver that should be
            associated with the list.

    """

    def __init__(self, language, libraries=None, driver=None):
        if libraries is None:
            libraries = []
        if ((isinstance(language, CompiledModelDriver)
             or (isinstance(language, type)
                 and issubclass(language, CompiledModelDriver)))):
            assert not driver
            driver = language
            language = driver.language
        elif isinstance(language, DependencyList):
            assert not libraries
            libraries = language
            language = libraries.language
            if driver is None:
                driver = libraries.driver
        super(DependencyList, self).__init__(language, driver=driver)
        for k in libraries:
            self.append(k)

    def __str__(self):
        members = [str(x) for x in self]
        return str(members)

    def __repr__(self):
        return f'DependencyList({str(self)})'
        
    def __iter__(self):
        return iter(self.libraries.values())

    def __add__(self, other):
        out = DependencyList(self.language, self,
                             driver=self.driver)
        out += other
        return out

    def __iadd__(self, other):
        for x in other:
            self.append(x)
        return self

    def append(self, dep, with_dependencies=False, **kwargs):
        r"""Add a dependency to the list if it's not already present.

        Args:
            dep (str, tuple, CompilationDependency): Dependency to add.
            with_dependencies (bool, optional): If True, add dep and its
                dependencies.
            **kwargs: Additional keyword arguments are passed to set.

        """
        if isinstance(dep, (str, tuple)):
            dep = self.driver.libraries.get(dep)
        assert isinstance(dep, CompilationDependency)
        if with_dependencies:
            dep = dep.specialized(**self.specialization.subspec)
            min_dep = len(self)
            sub_deps = dep.dependency_order()
            new_deps = DependencyList(self.driver)
            for sub_d in sub_deps:
                if sub_d in self:
                    min_dep = min(min_dep, self.index(sub_d))
                else:
                    new_deps.append(sub_d)
            self.insert(min_dep, new_deps, **kwargs)
            return
        self.set(dep.name, dep, **kwargs)

    def insert(self, index, dep, **kwargs):
        r"""Insert a dependency in the list at the desired index.

        Args:
            index (int): Index to insert the dependency at.
            dep (str, tuple, list, CompilationDependency, DependencyList):
                Dependency to insert.
            **kwargs: Additional keyword arguments are passed to append.

        """
        prefix = []
        suffix = []
        for i, (k, v) in enumerate(self.libraries.items()):
            if i < index:
                prefix.append((k, v))
            else:
                suffix.append((k, v))
        self.libraries = OrderedDict(*prefix)
        if not isinstance(dep, (list, DependencyList)):
            dep = [dep]
        for d in dep:
            self.append(d, **kwargs)
        for k, v in suffix:
            self.append(v, **kwargs)

    def index(self, dep):
        r"""Get the index of a dependency.

        Args:
            dep (str, tuple, CompilationDependency): Dependency to get the
                index of.

        Returns:
            int: Index.

        """
        if isinstance(dep, tuple) and dep[0] == self.language:
            dep = self[dep[1]]
        elif not isinstance(dep, CompilationDependency):
            dep = self[dep]
        for i, v in enumerate(self.libraries.values()):
            if dep == v:
                return i
        raise KeyError

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.libraries.values())[key]
        elif isinstance(key, slice):
            return DependencyList(self.language,
                                  list(self.libraries.values())[key],
                                  driver=self.driver)
        return super(DependencyList, self).__getitem__(key)

    def getall(self, key, to_update=None, **kwargs):
        r"""Get a type of key for all dependencies in the list.

        Args:
            key (str): Type of parameter to get.
            to_update (list, dict, optional): Existing list or dictionary
                that should be updated with values for each dependency.
            **kwargs: Additional keyword arguments are passed to get for
                each dependency.

        Returns:
            list, dict: Accumulated properties for all dependencies.

        """
        out = []
        kwargs['default'] = None
        if to_update is None:
            if key in CompilationDependency.dict_parameters:
                to_update = {}
                if key.endswith('env'):
                    to_update.update(os.environ)
            elif key in CompilationDependency.list_parameters:
                to_update = []
        for v in self:
            iout = v.get(key, to_update=to_update, **kwargs)
            if iout:
                out.append(iout)
        if isinstance(to_update, (dict, list)):
            return to_update
        return out

    def specialized(self, **kwargs):
        r"""Return a copy of this record specialized to a specific tool.

        Args:
            **kwargs: Keyword arguments are passed to the specialize
                method for the elements of the copy.

        Returns:
            DependencyList: Specialized copy.

        """
        spec = DependencySpecialization(self.specialization, **kwargs)
        out = DependencyList(self.language, driver=self.driver)
        out.specialization = spec
        for dep in self:
            out.append(dep, only_enabled=True)
        return out


class CompilationDependency(object):
    r"""Class for managing compilation dependencies.

    Args:
        name (str): Library name.
        origin (str): String describing if the library is a language
            standard, external, or yggdrasil internal library.
        language (str): Language that the library is written in.
        cfg (CisConfigParser, optional): Configuration class containing
            cached file paths that should be used to initialize the files.
        driver (CompiledModelDriver, optional): Driver responsible for
            this dependency.
        platform_specifics (dict, optional): Mapping of parameters
            specific to operating systems. Only those for the current
            OS will be selected.
        for_model (bool, optional): If True, the appropriate
            interface library will be added to the dependencies for
            the target.
        skip_interface_flags (bool, optional): If True, the interface
            flags will not be included for the target.
        instance (CompiledModelDriver, optional): Driver instance
            that specialization parameters should be taken from.
        **kwargs: Additional keyword arguments will be parsed as
            dependency parameters. Available parameters are described
            below.

    Parameters:
        libtype (str, optional): File type that should be used for
            compilation by default.
        source (str, optional): Path to source file that should be used
            to build the dependency.
        include (str, optional): Path to include file for the dependency.
        directory (str, optional): Directory that should be used as the
            root for generated path names.
        include_dirs (str, optional): Additional directories that should
            be included for compilation.
        platforms (list, optional): The operating systems that the
            library is available on.
        standard (bool, optional): If True, the library can be treated as
            standard in link calls without the full path.
        toolname (str, optional): Compilation tool associated with the
            library.
        internal_dependencies (list, optional): Yggdrasil dependencies
            required to build this dependency.
        external_dependencies (list, optional): External dependencies
            required to build this dependency.
        compiler_flags (list, optional): Flags that should passed to the
            compiler during compilation.
        linker_flags (list, optional): Flags that should passed to the
            linker during linking.
        archiver_flags (list, optional): Flags that should passed to the
            archiver during build.
        linker_language (str, optional): Language that should be used for
            linking if different from the compilation language.
        specialization (str, optional): Specialization key that must be
            True for the dependency to be enabled.
        exclude_specialization (str, optional): Specialization key that
            must be False for the dependency to be enabled.
        toolsets (list, optional): Names of toolsets that the library is
            valid for.
        dep_executable_flags (list, optional): Flags that should be used
            when compiling an executable that depends on this dependency.
        dep_shared_flags (list, optional): Flags that should be used when
            compiling a library that depends on this dependency.
        compiler_env (dict, optional): Environmental variables that should
            be set when building the dependency.
        runtime_env (dict, optional): Environmental variables that should
            be set when running an executable that links against this
            dependency.
        preload (bool, optional): If True, this library should be
            preloaded when running an executable that links against it.

    """

    valid_origins = [
        'language', 'standard', 'external', 'internal', 'user',
    ]
    cached_files = [
        'libtype', 'include', 'shared', 'static', 'windows_import',
        'generated_windows_import',
    ]
    built_files = [
        'object', 'static', 'shared', 'windows_import', 'library',
        'dependency_order', 'library_base', 'executable', 'output',
        'build', 'builddir', 'configfile',
    ]
    compiled_files = [
        'object', 'shared', 'windows_import', 'executable', 'static',
    ]
    result_files = [
        'shared', 'windows_import', 'executable', 'static', 'build',
    ]
    linked_files = [
        'shared', 'windows_import', 'executable',
    ]
    archived_files = [
        'static',
    ]
    header_files = [
        'include', 'header', 'header_only',
    ]
    library_files = [
        'static', 'shared', 'windows_import',
    ]
    always_generated = (
        ['dep_kwargs']
        + [f'dep_{k}_kwargs' for k in _tool_types]
        + [f'{k}_input' for k in _tool_types]
        + [f'{k}_output' for k in _tool_types])
    fully_specialized = [
        'global_env', 'compiler_env', 'runtime_env', 'output',
        'dependency_order',
    ]
    tool2libtype = {'linker': ['shared', 'windows_import', 'executable'],
                    'archiver': ['static'],
                    'builder': ['build']}
    libtype2tool = {'shared': 'linker',
                    'windows_import': 'linker',
                    'executable': 'linker',
                    'static': 'archiver',
                    'build': 'builder'}
    tool_specific_parameters = ['flags', 'language']
    ignored_parameters = [
        'dry_run', 'products', 'use_ccache',
        'skip_defaults', 'dont_skip_env_defaults',
        'flags', 'env', 'overwrite',
        'use_library_path_internal', 'use_library_path',
        'skip_library_libs',
        'build_library', 'libraries',
        'allow_error', 'no_additional_stages',
        'additional_args', 'additional_objs',
    ]
    passed_parameters = [
        'verbose'
    ]
    scalar_parameters = [
        'name', 'origin', 'language', 'working_dir', 'libtype',
        'source', 'include', 'directory', 'suffix', 'no_suffix',
        'object', 'shared', 'static', 'windows_import', 'output',
        'is_standard', 'toolname', 'preload', 'platform_specifics',
        'specialization', 'exclude_specialization', 'target_dep',
        'env_compiler', 'env_compiler_flags',
        'env_linker', 'env_linker_flags', 'flags_in_env', 'build_driver',
        'builddir', 'buildfile', 'configfile',
    ]
    dict_parameters = [
        'global_env', 'compiler_env', 'linker_env', 'archiver_env',
        'builder_env', 'configurer', 'runtime_env', 'dep_kwargs',
        'dep_compiler_kwargs', 'dep_linker_kwargs', 'dep_archiver_kwargs',
        'dep_builder_kwargs', 'dep_configurer_kwargs',
    ]
    list_parameters = [
        'compiler_flags', 'linker_flags', 'include_dirs', 'definitions',
        'dependencies', 'internal_dependencies', 'external_dependencies',
        'dep_compiler_flags', 'dep_executable_flags',
        'dep_shared_flags', 'dep_static_flags', 'toolsets', 'platforms',
    ]
    aliased_parameters = {
        'out': 'output',
    }
    name_source = [
        'output', 'target', 'source',
    ]
    target_inherited = [
        'output', 'source', 'directory', 'working_dir',
        'suffix', 'no_suffix',
    ]

    def __init__(self, name, origin, language, cfg=None, driver=None,
                 for_model=False, skip_interface_flags=False,
                 instance=None, in_driver_registration=False, **kwargs):
        assert origin in self.valid_origins
        self.parameters = {
            'name': name,
            'origin': origin,
            'language': language,
        }
        if '-fopenmp' in kwargs.get('compiler_flags', []):
            kwargs.setdefault('with_omp', True)
        self._parent_driver = driver
        self._driver = None
        self._all_parameters = None
        if driver and driver.language == self.language:
            self._driver = driver
        self._library_toolnames = {}
        self._updated_tools = {
            k: {} for k in DependencySpecialization.tooltypes}
        self.unused_kwargs = {}
        if ((for_model and not skip_interface_flags
             and self.driver.interface_library)):
            kwargs.setdefault('dependencies', [])
            kwargs['dependencies'].append(self.driver.interface_library)
            kwargs.setdefault("linker", None)
            kwargs.setdefault("linker_language", "c++")
        if for_model:
            kwargs.setdefault('libtype',
                              self.parent_driver.default_model_libtype)
        spec, kwargs = DependencySpecialization.split(kwargs)
        kwargs = CompilationDependency.standardize_parameters(origin,
                                                              kwargs)
        target_kwargs = dict(
            DependencySpecialization.select(spec, for_target=True),
            **self.extract_target_parameters(kwargs))
        self.parameters.update(kwargs)
        if not self.name:
            for k in self.name_source:
                iname = self._basename(self.parameters.get(k, None))
                if iname:
                    self.parameters['name'] = iname
                    break
        if instance:
            spec = dict(
                DependencySpecialization.select_attr(
                    instance,
                    use_target=(instance.is_build_tool
                                and not self.parent_driver.is_build_tool)),
                **spec)
        if self.parent_driver.is_build_tool:
            target_kwargs.setdefault('build_driver', self.parent_driver)
            target_kwargs.setdefault('instance', instance)
            target_kwargs.setdefault('for_model', for_model)
            target_kwargs.setdefault('skip_interface_flags',
                                     skip_interface_flags)
            for k in self.target_inherited:
                if self.parameters.get(k, None) is not None:
                    target_kwargs.setdefault(k, self.parameters[k])
            target_dep = self.parameters.get('target_dep', False)
            if target_dep:
                target_dep = target_dep.specialized(**target_kwargs)
            else:
                if not (target_kwargs.get('language', False)
                        or target_kwargs.get('driver', False)):
                    target_kwargs['language'] = (
                        self.parent_driver.get_language_for_source(
                            target_kwargs['source'], **self.parameters))
                target_dep = CompilationDependency(self.name,
                                                   self.origin,
                                                   **target_kwargs)
            self.parameters['target_dep'] = target_dep
        self.files = {}
        self.generated = []
        self.specialization = DependencySpecialization()
        self.specialization.update(self, **spec)
        assert self.specialization['libtype'] in [
            'shared', 'static', 'windows_import',
            'object', 'header_only', 'executable',
            'include', 'build', 'builddir', None]
        self.from_cache(cfg)
        # Parse parameters
        all_parameters = self.all_parameters(
            generalize=in_driver_registration)
        overlap = (set(all_parameters)
                   & set(self.ignored_parameters))
        if overlap:
            logger.error(f"Ignored parameters overlap with the "
                         f"supported parameters for {self.name}: "
                         f"{overlap}")
            assert not overlap
        invalid_kwargs = {}
        for k, v in self.parameters.items():
            if k in all_parameters:
                if isinstance(v, str) and os.path.isfile(v):
                    self.files.setdefault(k, v)
                if k in self.passed_parameters:
                    self.unused_kwargs[k] = v
            elif k in self.ignored_parameters:
                self.unused_kwargs[k] = v
            else:
                invalid_kwargs[k] = v
        if invalid_kwargs:
            logger.error(f"Unsupported parameters provided for "
                         f"{self.name}:\n"
                         f"{pprint.pformat(invalid_kwargs)}")
            assert not invalid_kwargs

    @property
    def name(self):
        r"""str: Name of the dependency."""
        return self.parameters['name']

    @property
    def origin(self):
        r"""str: Origin of the dependency."""
        return self.parameters['origin']

    @property
    def language(self):
        r"""str: Language that the dependency is written in."""
        return self.parameters['language']

    def display(self):
        r"""Display the dependency parameters."""
        print(f"Dependency {self.name}, {self.specialization}\n"
              f"{pprint.pformat(self.parameters)})")

    def all_parameters(self, generalize=False, only_active=False):
        r"""Get the set of all parameters valid for this dependency.

        Args:
            generalize (bool, optional): If True, use general parameters.
            only_active (bool, optional): If True, only include parameters
                for active tools.

        Returns:
            list: Parameter names.

        """
        if self._all_parameters is None:
            out = (self.scalar_parameters + self.list_parameters
                   + self.dict_parameters + self.passed_parameters)
            if generalize:
                tooltypes = _tool_types
            elif only_active:
                tooltypes = self.active_tools()
            elif self.basetool:
                tooltypes = [self.basetool.tooltype]
                tooltypes += self.basetool.associated_tooltypes
            else:
                tooltypes = []
            for k in tooltypes:
                out += self.tool_parameters(k, generalize=generalize)
            if generalize or only_active:
                return out  # Don't cache
            self._all_parameters = out
        return self._all_parameters

    @classmethod
    def extract_target_parameters(cls, kwargs, preserve_original=False):
        r"""Select parameters corresponding to a target dependency.

        Args:
            kwargs (dict): Dictionary of keyword arguments to extract
                parameters from.
            preserve_original (bool, optional): If True, extracted
                parameters will be left in kwargs.

        Returns:
            dict: Extracted parameters.

        """
        out = {}
        for k in list(kwargs.keys()):
            if k.startswith('target_') and k != 'target_dep':
                kt = k.split('target_', 1)[-1]
                out[kt] = kwargs[k]
                if not preserve_original:
                    kwargs.pop(k)
        return out

    @classmethod
    def standardize_parameters(cls, origin, kwargs):
        r"""Make substitution and adjustments to keyword arguments.

        Args:
            origin (str): Origin for dependency that kwargs belongs to.
            kwargs (dict): Keyword arguments to standardize.

        Returns:
            dict: Standardized keyword arguments.

        """
        for k, v in kwargs.get('platform_specifics', {}).get(
                platform._platform, {}).items():
            if k in cls.list_parameters:
                if not isinstance(v, list):
                    v = [v]
                kwargs[k] = kwargs.get(k, []) + [x for x in v if x not in
                                                 kwargs.get(k, [])]
            elif k in cls.dict_parameters:
                assert isinstance(v, dict)
                kwargs[k] = dict(kwargs.get(k, {}), **v)
            elif v is not None:
                assert not (isinstance(v, (list, dict))
                            or isinstance(kwargs.get(k, None),
                                          (list, dict)))
                kwargs[k] = v
        if origin == 'internal':
            kwargs.setdefault('linker_language', 'c++')
        kwargs.setdefault(
            'platforms', copy.deepcopy(platform._supported_platforms))
        for k, v in cls.aliased_parameters.items():
            if k in kwargs:
                kwargs[v] = kwargs.pop(k)
        return DependencySpecialization.remainder(kwargs)

    @classmethod
    def call_target(cls, method, driver, source=None, **kwargs):
        r"""Create a dependency and call a method on it.

        Args:
            method (str): Method that should be called.
            driver (CompiledModelDriver): Driver that target should be
                associated with.
            source (str, list, optional): Full path to source file(s).
                If not provided, a dummy source file will be used.
            **kwargs: Additional keyword arguments will be passed to
                create_target.

        Returns:
            object: Result of method call.

        """
        dep = cls.create_target(driver, source=source, **kwargs)
        return getattr(dep, method)(**dep.unused_kwargs)

    @classmethod
    def create_target(cls, driver, name=None, language=None, **kwargs):
        r"""Create a dependency.

        Args:
            driver (CompiledModelDriver): Driver that target should be
                associated with.
            name (str, optional): Name to give the target. If not
                provided, one will be generated based on other inputs.
            language (str, optional): Language of new target if different
                from the provided driver.
            **kwargs: Additional keyword arguments will be passed to the
                class constructor.

        Returns:
            CompilationDependency: New dependency.

        """
        if language is not None and ((not driver)
                                     or language != driver.language):
            driver = import_component('model', language)
        if language is None:
            assert driver is not None
            language = driver.language
        origin = kwargs.pop('origin', 'user')
        out = cls(name, origin, language, driver=driver, **kwargs)
        return out

    @classmethod
    def compilation_parameters(cls):
        r"""list: Compilation parameters"""
        out = []
        for tool in DependencySpecialization.tooltypes:
            out += [f"{tool}_{k}" for k in cls.tool_specific_parameters]
        return out

    @property
    def mixed_toolset(self):
        r"""bool: True if the linker is from a different toolset than
        the compiler."""
        next_tool = self.next_tool(self.basetool, self['libtype'])
        return (next_tool
                and (self.basetool.languages[0] not in next_tool.languages
                     or next_tool.toolset != self.basetool.toolset))

    @property
    def requires_fullpath(self):
        r"""bool: True if the full path is required."""
        return (not (self.get('is_standard', False)
                     or self.origin in ['standard', 'language']))

    @property
    def is_standard(self):
        r"""bool: True if the library is standard, False otherwise."""
        return (self.get('is_standard', False)
                or self.origin in ['standard', 'language'])

    @property
    def required_files(self):
        r"""list: Types of files required for the library definition to
        be complete."""
        out = ['libtype']
        libtype = self.get('libtype', False)
        if self.is_rebuildable:
            out += self.basetool.input_filetypes
        if self.origin in ['external']:
            out += ['include']
        if not libtype:
            out += ['shared', 'static']
        elif libtype not in self.header_files:
            out += [libtype]
        if 'build' in out:
            out += ['target_output']
        if platform._is_win and 'shared' in out:  # pragma: windows
            out += ['windows_import']
        return out

    @property
    def missing(self):
        r"""list: List of missing configuration values with descriptions"""
        out = []
        for k in self.required_files:
            if not self.get(k, False, dont_generate=True):
                opt = self.cache_key(k)
                if k in self.header_files:
                    desc_end = f'{self.name} headers'
                elif k in self.library_files:
                    desc_end = f'{self.name} {k} library'
                else:  # pragma: completion
                    desc_end = f'{self.name} {k}'
                desc = f'The full path to the {desc_end}.'
                out.append((self.language, opt, desc))
        return out

    @property
    def result(self):
        r"""str: Final result for the dependency."""
        return self['output']

    @property
    def is_complete(self):
        r"""bool: True if all of the required files have been identified."""
        return os.path.isfile(self.result)

    @property
    def is_installed(self):
        r"""bool: True if all of the required files exist"""
        return (self.is_rebuildable
                or all(self.get(k, False) for k in self.required_files))

    @property
    def is_interface(self):
        r"""bool: True if the library is an interface library."""
        return (self.origin == 'internal'
                and self.name == self.parent_driver.interface_library)

    @property
    def is_disabled(self):
        r"""bool: True if the library is disabled by specialization."""
        return (
            (not self.specialization.get(
                self.parameters.get('specialization', None), True))
            or self.specialization.get(
                self.parameters.get('exclude_specialization', None), False))

    @property
    def is_internal(self):
        r"""bool: True if the dependency can be rebuilt from sources."""
        return (self.origin in ['internal', 'user'])

    @property
    def is_rebuildable(self):
        r"""bool: True if the dependency can be rebuilt from sources."""
        return (self.origin in ['internal', 'user']
                and (self.specialization['libtype']
                     not in ['header_only', 'include']))

    @property
    def buildfile(self):
        r"""str: Full path to the file that should be used in builds."""
        return self.get()

    @property
    def suffix(self):
        r"""str: Suffix associated with the specialization for the
        dependency."""
        if (((not self.is_rebuildable)
             or self.parameters.get('no_suffix', False))):
            return ''
        if self.specialization['generalized_suffix']:
            return self.specialization['generalized_suffix']
        out = self.parameters.get('suffix', '')
        if self.driver.is_build_tool:
            return out
        out += _system_suffix
        if self.specialization['disable_python_c_api']:
            out += '_nopython'
        if self.specialization['with_asan']:
            out += '_asan'
        if self.specialization['with_omp']:
            out += '_omp'
        commtype = self.specialization['commtype']
        if commtype is None:
            commtype = tools.get_default_comm()
        out += f"_{commtype[:3].lower()}"
        return out

    @property
    def parent_driver(self):
        r"""CompilerModelDriver: Driver responsible for this dependency."""
        if self._parent_driver is None:
            self._parent_driver = self.driver
        return self._parent_driver
    
    @property
    def driver(self):
        r"""CompilerModelDriver: Driver associated with this library's
        language."""
        if self._driver is None:
            self._driver = import_component('model', self.language)
        return self._driver

    @property
    def basetool(self):
        r"""CompilationToolBase: Tool associated with the library."""
        return self.tool('basetool')

    @property
    def nexttool(self):
        r"""CompilationToolBase: Tool associated with the next stage."""
        return self.tool('nexttool')

    def toolname(self, libtype):
        r"""Get the name of the tool that will produce a file.

        Args:
            libtype (str): File type.

        Returns:
            str: Tool name.

        """
        return self.tool(libtype).toolname

    def locate_tool(self, tooltype, toolname):
        r"""Locate a tool based on the cache.

        Args:
            tooltype (str): Type of tool to locate.
            toolname (str): Name of tool to locate.

        Returns:
            CompilationToolBase: Compilation tool.

        """
        out = self._updated_tools[tooltype].get(toolname, None)
        if not out:
            tooltype0 = tooltype
            if tooltype == 'basetool':
                tooltype0 = self.parent_driver.basetool
            elif tooltype == 'nexttool':
                tooltype0 = self.basetool.libtype_next_stage.get(
                    self['libtype'], None)
            if tooltype0 is None:
                out = None
            elif (tooltype0 != 'compiler'
                  and self.origin in ['language', 'standard']):
                out = self.tool('compiler').get_tool(tooltype0)
            else:
                language = self.parameters.get(f"{tooltype0}_language",
                                               self.language)
                global _tool_registry
                out = _tool_registry.tool_instance(
                    tooltype0, language=language,
                    driver=self.parent_driver,
                    compatible_with=toolname,
                    only_installed=True, default=None)
            self._updated_tools[tooltype][toolname] = out
            if out and out.toolname not in self._updated_tools[tooltype]:
                self._updated_tools[tooltype][out.toolname] = out
            if out and tooltype in ['basetool', 'nexttool']:
                self._updated_tools[out.tooltype][toolname] = out
                if out.toolname not in self._updated_tools[out.tooltype]:
                    self._updated_tools[out.tooltype][out.toolname] = out
        return out

    def active_tools_class(cls, basetool, libtype=None, **kwargs):
        r"""list: Tool types required to produce the desired result."""
        if libtype in [None, 'library', 'output']:
            libtype = basetool.default_libtype
        out = []
        if ((libtype not in basetool.input_filetypes
             and kwargs.get(basetool.input_filetypes[0], None) is not None)):
            out.append(basetool.tooltype)
        if libtype in basetool.libtype_next_stage:
            out.append(basetool.libtype_next_stage[libtype])
        return out

    def active_tools(self, libtype=None):
        r"""list: Tool types required to produce the desired result."""
        if libtype in [None, 'library', 'output']:
            libtype = self['libtype']
        kws = {'source': self.get('source', None)}
        if libtype not in self.basetool.input_filetypes:
            kws[self.basetool.input_filetypes[0]] = self.get(
                self.basetool.input_filetypes[0], None)
        return self.active_tools_class(self.basetool, libtype, **kws)

    def tool(self, libtype):
        r"""Get the appropriate tool for producing a file.

        Args:
            libtype (str): File type or tooltype.

        Returns:
            CompilationToolBase: Compilation tool.

        """
        if libtype in DependencySpecialization.tooltypes:
            out = self.locate_tool(libtype, self.specialization[libtype])
            if not out:
                logger.info(f"MISSING TOOL: {self.name}, {libtype}:\n"
                            f"{pprint.pformat(self._updated_tools[libtype])}")
            return out
        elif libtype in self.linked_files:
            return self.tool('linker')
        elif libtype in self.archived_files:
            return self.tool('archiver')
        elif libtype in self.compiled_files + ['include']:
            return self.tool('compiler')
        elif libtype == 'configuration':
            return self.tool('configurer')
        elif libtype == 'build':
            return self.tool('builder')
        raise ValueError(f"Unsupported libtype: {libtype}")

    def next_tool(self, basetool, libtype):
        r"""Get the appropriate tool for the next stage in producing
        a file.

        Args:
            basetool (CompilationToolBase): Compilation tool used for
                the previous stage.
            libtype (str): File type or tooltype.

        Returns:
            CompilationToolBase: Compilation tool.

        """
        next_tooltype = basetool.libtype_next_stage.get(libtype, None)
        if not next_tooltype:
            return None
        return self.tool(next_tooltype)

    def suffix_tools(self, libtype, skip_basetool=False):
        r"""Determine the appropriate suffix for a file type.

        Args:
            libtype (str): File type.
            skip_basetool (bool, optional): If True, don't include the
                base tool name.

        Returns:
            str: Suffix.

        """
        if self.parameters.get('no_suffix', False):
            return ''
        tools = []
        if self.is_rebuildable and not self.specialization['generalized_suffix']:
            if (not skip_basetool) and libtype in self.built_files:
                tools.append(self.basetool)
            if libtype in self.library_files:
                tools.append(self.tool(libtype))
        out = ""
        for tool in tools:
            if '%s' in tool.tool_suffix_format:
                out += tool.tool_suffix_format % tool.toolname
            else:
                out += tool.tool_suffix_format
        return out

    def prefix(self, libtype):
        r"""Determine the appropriate prefix for a file type.

        Args:
            libtype (str): File type.

        Returns:
            str: Prefix.

        """
        return self.tool(libtype).libtype_prefix.get(libtype, "")

    def extension(self, libtype, return_all=False):
        r"""Determine the appropriate extension for a file type.

        Args:
            libtype (str): File type.
            return_all (bool, optional): If True, all of the possible
                options are returned. Defaults to False.

        Returns:
            str, list: File extension(s).

        """
        if libtype in self.header_files:
            out = copy.copy(self.tool('compiler').include_exts)
        else:
            out = [self.tool(libtype).libtype_ext.get(libtype, "")]
        if return_all:
            return out
        return out[0]

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return (self.get(key, None) is not None)
        
    def __eq__(self, other):
        if not isinstance(other, CompilationDependency):
            return False
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.name, self.specialization))

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return (f"CompilationDependency({self.name}, "
                f"driver={self.parent_driver.language})")

    def logInfo(self, level=logging.INFO, tooltype='basetool'):
        r"""Display info abou the dependency as an info level log message."""
        specinfo = pprint.pformat({k: self.specialization[k] for k in
                                   self.specialization.defaults.keys()})
        specinfo = specinfo.replace('\n', '\n' + 16 * ' ')
        toolinfo = pprint.pformat({k: self.toolname(k) for k in
                                   self.active_tools()})
        toolinfo = toolinfo.replace('\n', '\n' + 16 * ' ')
        tool = self.tool(tooltype)
        src = self.get(f'{tool.tooltype}_input')
        logger.log(level,
                   f"\n"
                   f"    dependency: {self.name}\n"
                   f"    driver:     {self.parent_driver.language}\n"
                   f"    spec:       {specinfo}\n"
                   f"    libtype:    {self['libtype']}\n"
                   f"    input:      {src}\n"
                   f"    output:     {self.result}\n"
                   f"    tooltypes:  {toolinfo}")

    def set(self, filetype, value, key=None):
        r"""Set a library file path.

        Args:
            filetype (str): Type of file to set.
            value (str): Library file path.
            key (str, optional): Key that should be used. If None, one
                will be generated.

        """
        assert filetype not in self.always_generated
        if key is None:
            key = self.key(filetype)
        self.files[key] = value

    def getall(self, key, **kwargs):
        r"""Get accumulated values for this dependency and its sub-deps.

        Args:
            key (str): Type of parameter to get.
            **kwargs: Additional keyword arguments are passed to get for
                each dependency.

        Returns:
            list, dict: Accumulated properties for all dependencies.

        """
        return self.dependency_order().getall(key, **kwargs)

    @classmethod
    def _update(cls, lhs, rhs):
        if isinstance(rhs, dict):
            for k, v in rhs.items():
                if isinstance(v, (list, dict, DependencyList)) and k in lhs:
                    cls._update(lhs[k], v)
                else:
                    lhs[k] = v
        else:
            lhs += [x for x in rhs if x not in lhs]

    def get(self, filetype=None, default=tools.InvalidDefault(),
            dont_generate=False, **kwargs):
        r"""Get a library file path, generating it if it does not already
        exist.

        Args:
            filetype (str, optional): Type of file to return. If not
                provided, the compilation file will be returned.
            default (str, optional): Value that should be returned if a
                library path does not exist.
            dont_generate (bool, optional): If True, any missing files
                will not be generated.
            **kwargs: Additional keyword arguments are passed to generate
                if it is called.

        Returns:
            str: Library file path.

        """
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).get(
                default=default, filetype=filetype,
                dont_generate=dont_generate,
                **self.specialization.remainder(kwargs))
        if filetype is None:
            filetype = self.get('libtype')
        key = self.key(filetype)
        if (((not dont_generate)
             and ((key not in self.files)
                  or (filetype in self.always_generated)
                  or (key in self.generated
                      and key in self.files
                      and not os.path.isfile(self.files[key]))))):
            self.generate(filetype, **kwargs)
        if key in self.files and self.files[key] not in [None, False]:
            if isinstance(self.files[key], (list, dict, DependencyList)):
                if ((isinstance(kwargs.get('to_update', None),
                                (list, dict, DependencyList))
                     and not kwargs.get('dont_update_return', False))):
                    self._update(kwargs['to_update'], self.files[key])
                    return kwargs['to_update']
                return type(self.files[key])(self.files[key])
            assert isinstance(self.files[key], (str, bool,
                                                CompilationDependency,
                                                CompilationToolBase,
                                                CompiledModelDriver,
                                                ComponentMeta))
            return self.files[key]
        if not isinstance(default, tools.InvalidDefault):
            return default
        raise KeyError(f"Could not determine location of "
                       f"{filetype} for {self.name}")

    def tool_specific_cache(self, filetype):
        r"""Determine if the path for a library file should be cached
        for individual compilers.

        Args:
            filetype (str): Type of file to check.

        Returns:
            list: List of tool types that should be included in the cache
                key if one should be included, False otherwise.

        """
        if filetype in ['configuration', 'build']:
            return []
        if self.is_rebuildable and filetype in self.built_files:
            return self.active_tools(filetype)
        if ((self.origin in ['standard', 'language']
             or (filetype == 'windows_import'
                 and not self.is_rebuildable))):
            return ['linker']
        return []

    def key(self, filetype, use_regex=False):
        r"""Get the key for a library file.

        Args:
            filetype (str): Type of file to get cache key for.
            use_regex (bool, optional): If True and a toolname is not
                provided, but is required, a regex will be used instead.

        Returns:
            str: Key.

        """
        if filetype == 'header_only':
            filetype = 'include'
        if (((self.is_rebuildable
              and filetype in ['library', 'libtype', 'definitions'])
             or filetype in self.fully_specialized)):
            return (filetype, self.specialization._tuple)
        if filetype in self.always_generated:
            return filetype
        key = filetype
        if use_regex:
            key = tools.escape_regex(key)
        for tooltype in self.tool_specific_cache(filetype):
            toolname = self.specialization[tooltype]
            if use_regex:
                if toolname is None:
                    toolname = '.+'
                else:
                    toolname = tools.escape_regex(toolname)
            if toolname is None:
                toolname = self.tool(tooltype).toolname
            assert toolname is not None
            key += f"_{toolname}"
        suffix = self.suffix
        if suffix and filetype in self.built_files:
            if use_regex:
                key += tools.escape_regex(suffix)
            else:
                key += suffix
        return key

    def cache_key(self, filetype, **kwargs):
        r"""Get the cache key for a library file.

        Args:
            filetype (str): Type of file to get cache key for.
            **kwargs: Additional keyword arguments are passed to self.key

        Returns:
            str: Cache key.

        """
        name = self.name
        if kwargs.get('use_regex', False):
            name = tools.escape_regex(name)
        return f"{name}_{self.key(filetype, **kwargs)}"

    def check_parameters(self, kwargs):
        r"""Check if there are differing parameters in the provided
        dictionary.

        Args:
            kwargs (dict): Dictionary of parameters to check.

        Returns:
            bool: True if the parameters match, False otherwise.

        """
        if kwargs:
            kwargs = CompilationDependency.standardize_parameters(
                self.origin, dict(self.parameters, **kwargs))
            target_kwargs = {}
            for k, v in kwargs.items():
                if ((k in ['name', 'language', 'origin']
                     and v != getattr(self, k))):
                    return False
                if ((k in self.all_parameters()
                     and v != self.parameters.get(k, None))):
                    return False
                if k.startswith('target_') and k != 'target_dep':
                    target_kwargs[k.split('target_', 1)[-1]] = v
                elif (k in self.target_inherited
                      and f'target_{k}' not in kwargs):
                    target_kwargs[k] = v
            target_dep = self.parameters.get('target_dep', False)
            if target_dep and not target_dep.check_parameters(target_kwargs):
                return False
        return True

    def specialized(self, **kwargs):
        r"""Return a copy of this record specialized to a specific tool.

        Args:
            **kwargs: Keyword arguments are passed to the specialize
                method for the shallow copy.

        Returns:
            CompilationDependency: Shallow copy with the updated toolname.

        """
        kwargs.update(self._library_toolnames)
        if not self.check_parameters(kwargs):
            kwargs = dict(self.parameters, **kwargs)
            kwargs = dict(self.specialization.values, **kwargs)
            language = kwargs.pop('language', self.language)
            assert kwargs.pop('name', self.name) == self.name
            assert kwargs.pop('origin', self.origin) == self.origin
            assert kwargs.pop('driver', self.parent_driver) == self.parent_driver
            return CompilationDependency(self.name, self.origin,
                                         language, cfg=self.cfg,
                                         driver=self.parent_driver,
                                         **kwargs)
        target_dep = self.parameters.get('target_dep', False)
        target_kws = {}
        if target_dep:
            target_kws = DependencySpecialization.select(
                kwargs, for_target=True)
        if ((self.specialization.check(kwargs)
             and ((not target_dep)
                  or target_dep.specialization.check(target_kws)))):
            return self
        out = copy.copy(self)
        out._all_parameters = None
        out.specialization = DependencySpecialization(self)
        out.specialization.update(out, **kwargs)
        if out.origin == 'language':
            assert out.name == out.basetool.standard_library
        if target_dep:
            out.parameters['target_dep'] = target_dep.specialized(
                **target_kws)
        return out

    def from_cache(self, cfg):
        r"""Update the parameters from a configuration file.

        Args:
            cfg (CisConfigParser): Configuration class containing cached
                file paths.

        """
        self.cfg = cfg
        if self.is_internal or cfg is None:
            return
        self.generated += [
            x for x in cfg.get(self.language,
                               f'{self.name}_generated', [])
            if x not in self.generated]
        for k in self.cached_files:
            cache_key = self.cache_key(k, use_regex=True)
            cached = cfg.get_regex(self.language, cache_key,
                                   return_all=True)
            cached = {kk.split('_', 1)[-1]: v
                      for kk, v in cached.items()}
            self.files.update(cached)

    def update_cache(self, cfg):
        r"""Update the configuration file with library file paths.

        Args:
            cfg (CisConfigParser): Configuration class containing cached
                file paths.

        """
        if self.is_internal:
            return
        self.generate()
        if self.generated:
            cfg.set(self.language, f'{self.name}_generated',
                    sorted(self.generated))
        for k, v in self.files.items():
            if not (v and isinstance(k, str)
                    and k.startswith(tuple(self.cached_files))):
                continue
            assert '_' not in self.name  # So that key can be loaded
            cfg.set(self.language, f"{self.name}_{k}", v)

    def generate(self, filetype=None, overwrite=False, **kwargs):
        r"""Generate the path for a library file.

        Args:
            filetype (str): Type of file to generate.
            overwrite (bool, optional): If True, overwrite the existing
                file path.
            **kwargs: Additional keyword arguments are passed to
                specialize and the correct method for file generation
                based on filetype.

        """
        if filetype is None:
            for k in self.required_files:
                self.generate(k, overwrite=overwrite, **kwargs)
            return
        if filetype in self.always_generated:
            overwrite = True
        key = self.key(filetype)
        if ((key in self.generated and key in self.files
             and not os.path.isfile(self.files[key]))):
            kwargs['previous'] = self.files.pop(key)
        if key in self.files and not overwrite:
            return self.files[key]
        aliases = {'header_only': 'include'}
        filetype = aliases.get(filetype, filetype)
        if hasattr(self, f'_{filetype}'):
            out = getattr(self, f'_{filetype}')(**kwargs)
        elif filetype == 'input':
            if self['libtype'] in self.built_files:
                out = self.get(self.basetool.input_filetypes[0],
                               default=None, **kwargs)
            else:
                out = self.get(self['libtype'], default=None, **kwargs)
        elif filetype == 'output':
            out = self.get(self['libtype'], default=None, **kwargs)
        elif filetype == 'library':
            libtype = kwargs.pop('libtype', None)
            if libtype is None:
                libtype = self.get('libtype', **kwargs)
            out = self.get(libtype, **kwargs)
        elif filetype == 'library_base':
            libtype = kwargs.pop('libtype', None)
            if libtype is None:
                libtype = self.get('libtype', **kwargs)
            out = self._build_output_base(libtype, **kwargs)
        elif filetype in self.result_files:
            out = self._result(filetype=filetype, **kwargs)
        elif filetype in DependencySpecialization.tooltypes:
            out = self.tool(filetype, **kwargs)
        elif filetype in [f'{k}_path' for k in
                          DependencySpecialization.tooltypes]:
            tooltype = filetype.rsplit('_path', 1)[0]
            tool = self.tool(tooltype, **kwargs)
            out = None
            if tool:
                out = tool.get_executable(full_path=True)
        elif filetype in [f'{lang}_{k}' for lang, k in
                          itertools.product(
                              constants.LANGUAGES['compiled'],
                              DependencySpecialization.tooltypes)]:
            language, tooltype = filetype.split('_', 1)
            out = self.get(tooltype, **kwargs)
            if (not out) or (language not in out.languages):
                global _tool_registry
                out = _tool_registry.tool_instance(
                    tooltype, language=language,
                    compatible_with=self.basetool,
                    only_installed=True, default=None, **kwargs)
        elif filetype in [f'{lang}_{k}_path' for lang, k in
                          itertools.product(
                              constants.LANGUAGES['compiled'],
                              DependencySpecialization.tooltypes)]:
            tooltype = filetype.rsplit('_', 1)[0]
            out = None
            tool = self.get(tooltype, None, **kwargs)
            if tool:
                out = tool.get_executable(full_path=True)
        elif filetype in [f'{k}_env' for k in
                          DependencySpecialization.tooltypes]:
            out = self._build_env(filetype, **kwargs)
        elif filetype in [f'{k}_input' for k in
                          DependencySpecialization.tooltypes]:
            out = self._tool_input(filetype.rsplit('_input', 1)[0],
                                   **kwargs)
        elif filetype in [f'{k}_output' for k in
                          DependencySpecialization.tooltypes]:
            out = self._tool_output(filetype.rsplit('_output', 1)[0],
                                    **kwargs)
        elif filetype in [f'{k}_flags' for k in
                          DependencySpecialization.tooltypes]:
            out = self.tool_flags(filetype.rsplit('_flags', 1)[0],
                                  **kwargs)
        elif filetype in [f'{k}_kwargs' for k in
                          DependencySpecialization.tooltypes]:
            out = self.tool_kwargs(filetype.rsplit('_flags', 1)[0],
                                   **kwargs)
        elif filetype == 'dep_kwargs':
            out = dict(kwargs.pop('to_update', {}))
            for k in self.active_tools():
                self.get(f'dep_{k}_kwargs', to_update=out, **kwargs)
        elif filetype in ['dep_builder_kwargs', 'dep_configurer_kwargs']:
            out = {}
        elif filetype in [f'dep_{k}_kwargs' for k in
                          ['linker', 'archiver', 'libtool']]:
            out = self._dep_libtool_kwargs(filetype, **kwargs)
        elif filetype.startswith('target_') and filetype != 'target_dep':
            target_dep = self.parameters.get('target_dep', False)
            out = None
            if target_dep:
                out = target_dep.get(
                    filetype.split('target_', 1)[-1], None)
        else:
            out = self.parameters.get(filetype, None)
        if out in [None, False] and hasattr(self, f'_generated_{filetype}'):
            out = getattr(self, f'_generated_{filetype}')(**kwargs)
            if out is not None:
                self.generated.append(key)
        # logger.debug(f"GENERATE: {self.name}, {key}, {out}")
        self.files[key] = out

    def _libtype(self, search_order=['shared', 'static'], **kwargs):
        if self.specialization['libtype']:
            return self.specialization['libtype']
        elif self.is_rebuildable:
            if self.driver.is_build_tool:
                return 'build'
            return _default_libtype
        elif self.origin == 'language':
            if platform._is_win:  # pragma: windows
                return 'windows_import'
            else:
                return 'shared'
        out = False
        for k in search_order:
            lib = self.get(k, default=False)
            if lib:
                out = k
                break
        if platform._is_win and out == 'shared':  # pragma: windows
            out = 'windows_import'
        return out

    def _directory(self, **kwargs):
        out = self.parameters.get(
            'directory', self.parameters.get('working_dir', False))
        if self.origin == 'internal':
            if not out:
                out = self.parent_driver.get_language_dir()
            elif not os.path.isabs(out):
                out = os.path.join(self.parent_driver.get_language_dir(),
                                   out)
        return out

    def _include(self, **kwargs):
        if (('include' not in self.parameters
             and self.get('libtype', False) == 'header_only')):
            out = self.parameters.get('source', False)
        else:
            out = self.parameters.get('include', False)
        out = self._relative_to_directory(out)
        if out and isinstance(out, str) and not os.path.isfile(out):
            out = self._search('include')
        return out

    def _include_dirs(self, **kwargs):
        out = []
        root = False
        if self.is_rebuildable:
            compiler = self.tool('compiler')
            if isinstance(compiler.search_path_env, list):
                out += [os.path.join(iprefix, ienv)
                        for iprefix in compiler.get_env_prefixes()
                        for ienv in compiler.search_path_env]
        if self.origin == 'external':
            include = self.get('include', False)
            if include:
                if os.path.isfile(include):
                    include = os.path.dirname(include)
                out += [include]
        elif self.origin in ['user', 'internal']:
            root = self.get('directory', False)
            if not root:
                src = self.get('source', False)
                if src and isinstance(src, list):
                    src = src[0]
                if src and os.path.isabs(src):
                    root = os.path.dirname(src)
            if root:
                out.append(root)
        param_val = self.parameters.get('include_dirs', [])
        if not isinstance(param_val, list):
            param_val = [param_val]
        out += param_val
        if self.is_rebuildable and root:
            out = self._relative_to_directory(out, directory=root)
        return list(set(out))

    def _definitions(self, **kwargs):
        out = copy.deepcopy(self.parameters.get('definitions', []))
        if self.origin == 'internal':
            out += [
                f'{c[:3].upper()}INSTALLED' for c in
                tools.get_installed_comm(
                    language=self.parent_driver.language)]
            commtype = self.specialization['commtype']
            if commtype is None:
                commtype = tools.get_default_comm()
            out.append(f'{commtype[:3].upper()}DEF')
        if self.is_interface:
            out += ['WITH_YGGDRASIL', '_USE_MATH_DEFINES']
            from yggdrasil import __version__
            yggver = __version__.split('+')[0].split('v')[-1].split('.')
            if len(yggver) > 0:
                out.append(f'YGGVER_MAJOR={yggver[0]}')
            logging_level = self.specialization['logging_level']
            if logging_level is not None:
                out.append(f'YGG_DEBUG={logging_level}')
        if ((self.specialization['disable_python_c_api']
             and not self.basetool.is_build_tool)):
            out.append('YGGDRASIL_DISABLE_PYTHON_C_API')
        return out

    def _basename(self, out):
        if isinstance(out, list):
            if len(out) > 0:
                return self._basename(out[0])
        elif out:
            return os.path.basename(os.path.splitext(out)[0])
        return None

    def _dirname(self, out):
        if isinstance(out, list):
            if len(out) > 0:
                out = [self._dirname(x) for x in out]
                if all(x == out[0] for x in out):
                    return out[0]
        elif out:
            return os.path.dirname(out)
        return None

    def _relative_to_directory(self, out, directory=None,
                               default_directory=False):
        if directory is None:
            directory = self.get('directory', default_directory)
        if out and directory:
            if isinstance(out, list):
                out = [self._relative_to_directory(x, directory=directory)
                       for x in out]
            elif not os.path.isabs(out):
                out = os.path.join(directory, out)
        return out

    def _source(self, **kwargs):
        if not self.is_rebuildable:
            return self.get('include', None)
        out = self.parameters.get('source', False)
        if out is False:
            out = self.name
            if out and self.driver.language_ext:
                out += self.driver.language_ext[0]
        return self._relative_to_directory(out)

    def _object(self, **kwargs):
        if not self.is_rebuildable:
            return None
        out = self._relative_to_directory(
            self.parameters.get('object', False))
        if out:
            return out
        return self._build_output('object', **kwargs)

    def _sourcedir(self, **kwargs):
        out = self.parameters.get('sourcedir', False)
        if not out:
            out = self._dirname(self.get('source', False))
        return self._relative_to_directory(out)

    def _builddir(self, **kwargs):
        if not self.is_rebuildable:
            return None
        out = self.parameters.get(
            'builddir',
            getattr(self.basetool, 'default_builddir', False))
        return self._relative_to_directory(out)

    def _configfile(self, **kwargs):
        if not self.is_rebuildable:
            return None
        out = self.parameters.get(
            'configfile',
            getattr(self.basetool, 'default_configfile', False))
        return self._relative_to_directory(
            out, directory=self.get('builddir', None))

    def _result(self, **kwargs):
        if self.origin in ['external', 'standard', 'language']:
            return self._search(**kwargs)
        return self._build_output(**kwargs)

    def _generated_windows_import(self, previous=None, **kwargs):
        out = None
        dll = self.get('shared', default=None, **kwargs)
        # TODO: temp
        logger.info(f"GENERATED_WINDOWS_IMPORT [{self.name}]: {dll} "
                    f"(previous = {previous}")
        if dll:
            directory = self.parent_driver.get_language_dir()
            out = create_windows_import(
                dll, dst=previous, directory=directory,
                for_gnu=self.tool('linker').is_gnu)
        return out

    def _tool_input(self, tooltype, **kwargs):
        assert self.is_rebuildable
        tool = self.tool(tooltype)
        assert len(tool.input_filetypes) == 1
        kwargs.pop('libtype', None)
        out = self.get(tool.input_filetypes[0], None, **kwargs)
        if isinstance(out, str):
            out = [out]
        return out

    def _tool_output(self, tooltype, **kwargs):
        assert self.is_rebuildable
        tool = self.tool(tooltype)
        out = None
        if self['libtype'] in tool.output_filetypes:
            out = self.get(self['libtype'], None, **kwargs)
        else:
            assert len(tool.output_filetypes) == 1
            out = self.get(tool.output_filetypes[0], None, **kwargs)
        if isinstance(out, str):
            out = [out]
        return out

    def _build_output(self, filetype=None, src=None, **kwargs):
        if filetype is None:
            filetype = self.get('libtype', **kwargs)
        skip_basetool = False
        if filetype == 'build':
            assert self.parameters.get('target_dep', None)
            if self.parameters.get('target', False) == 'clean':
                return 'clean'
            return self.parameters['target_dep']['output']
        if 'output' in self.parameters and (filetype == self['libtype']):
            out = self.parameters.get('output', None)
        else:
            out = self.parameters.get(filetype, None)
        if not out:
            if src is None:
                if filetype in self.library_files:
                    src = self.name
                else:
                    src = self.get('source', None)
            if src and isinstance(src, list):
                if filetype == 'object':
                    return [
                        self._build_output(filetype, src=isrc, **kwargs)
                        for isrc in src]
                else:
                    return self._build_output(filetype, src=src[0],
                                              **kwargs)
            if not src:
                return False
            src_dir, src_base = os.path.split(src)
            src_base, src_ext = os.path.splitext(src_base)
            prefix = self.prefix(filetype)
            ext = self.extension(filetype)
            suffix = (self.suffix
                      + self.suffix_tools(filetype,
                                          skip_basetool=skip_basetool))
            if ((self.is_rebuildable and src_ext
                 and not self.parameters.get('no_suffix', False))):
                suffix = f'_{src_ext[1:]}{suffix}'
            out = f'{prefix}{src_base}{suffix}{ext}'
            builddir = self.get('builddir', None)
            if not builddir:
                builddir = src_dir
            if builddir:
                out = os.path.join(builddir, out)
        return self._relative_to_directory(out)

    def _build_output_base(self, **kwargs):
        out = self._build_output(**kwargs)
        if out:
            out = os.path.basename(out)
        return out

    def _dependency_order(self, **kwargs):
        spec_kws = dict(self.specialization.subspec)
        spec_kws[self.basetool.tooltype] = self.basetool.toolname
        out = DependencyList(self.parent_driver).specialized()
        new_deps = DependencyList(out.driver).specialized()
        min_dep = len(out)
        alldeps = (self.get('dependencies', [])
                   + self.get('internal_dependencies', [])
                   + self.get('external_dependencies', []))
        if self.is_interface:
            for k, v in self.parent_driver.supported_comm_options.items():
                if ('libraries' in v) and self.parent_driver.is_comm_installed(k):
                    alldeps += v['libraries']
        if ((self.specialization['with_asan']
             and 'asan' in self.basetool.libraries
             and self.is_rebuildable
             and self.name != 'asan')):
            self.driver.libraries.add_compiler_libraries(self.basetool)
            alldeps.append((self.basetool.languages[0], 'asan'))
        if ((self.specialization['with_omp']
             and self['libtype'] in self.compiled_files
             and self.name != 'omp')):
            alldeps.append(('c', 'omp'))
        if ((self['libtype'] in self.compiled_files
             and self.basetool.standard_library
             and self.is_rebuildable
             and self.name != self.basetool.standard_library
             and self.mixed_toolset)):
            self.driver.libraries.add_compiler_libraries(self.basetool)
            alldeps.append((self.basetool.languages[0],
                            self.basetool.standard_library))
        if ((self['libtype'] in self.linked_files
             and self.tool('linker').standard_library
             and self.is_rebuildable
             and self.name != self.tool('linker').standard_library
             and self.mixed_toolset)):
            linker = self.tool('linker')
            drv = import_component('model', linker.languages[0])
            drv.libraries.add_compiler_libraries(linker)
            alldeps.append((linker.languages[0], linker.standard_library))
        spec_libs = self.parent_driver.libraries.specialized(**spec_kws)
        for d in alldeps:
            dep = spec_libs.get(d)
            sub_deps = dep.dependency_order()
            for sub_d in sub_deps:
                if sub_d in out:
                    min_dep = min(min_dep, out.index(sub_d))
                else:
                    new_deps.append(sub_d)
        if self in out:
            dpos = out.index(self)
            assert dpos <= min_dep
            min_dep = dpos
        elif self not in new_deps:
            new_deps.insert(0, self)
        out = out[:min_dep] + new_deps + out[min_dep:]
        return out

    def dependency_order(self, internal_only=False, for_build=False,
                         exclude_self=False, **kwargs):
        r"""Get the order of dependencies.

        Args:
            internal_only (bool, optional): If True, only internal
                dependencies will be considered.
            for_build (bool, optional): If True, the dependencies for
                building this dependency will be returned.
            exclude_self (bool, optional): If True, exclude this dependency
                from the returned list.
            **kwargs: Additional keyword arguments are used to specialize
                the dependencies.

        Returns:
            DependencyList: Dependencies of this dependency (including
                itself).

        """
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).dependency_order(
                internal_only=internal_only, for_build=for_build,
                exclude_self=exclude_self,
                **self.specialization.remainder(kwargs))
        out = self.get('dependency_order')
        
        def select_dep(x):
            return ((not x.is_disabled)
                    and ((not internal_only) or x.origin == 'internal')
                    and (((for_build or exclude_self) and x != self)
                         or ((not for_build)
                             and (x['libtype'] != 'object'
                                  or x == self))))

        return DependencyList(self.parent_driver,
                              [x for x in out if select_dep(x)])

    @classmethod
    def tool_parameters_class(self, tool):
        r"""Get the parameters associated with a tool.

        Args:
            tool (str, CompilationToolBase): Tool or type of tool to get
                parameters for.

        Returns:
            list: Parameter names.

        """
        if tool is None:
            return []
        out = ['working_dir']
        if isinstance(tool, str):
            global _tool_registry
            tool = _tool_registry._bases[tool]
        out += list(tool.flag_options.keys())
        out += tool.build_params
        for k in self.tool_specific_parameters:
            out.append(f"{tool.tooltype}_{k}")
        return out

    def tool_parameters(self, tooltype, generalize=False):
        r"""Get the parameters associated with a tool.

        Args:
            tooltype (str): Type of tool to get parameters for.
            generalize (bool, optional): If True, use general parameters.

        Returns:
            list: Parameter names.

        """
        if isinstance(tooltype, str) and not generalize:
            tooltype = self.tool(tooltype)
        return self.tool_parameters_class(tooltype)

    def tool_kwargs(self, tooltype='basetool', toolname=None,
                    no_env=False, **kwargs):
        r"""Get the keyword arguments for executing a step in the build
        process for this dependency.

        Args:
            tooltype (str, optional): Type of tool to get arguments for.
            toolname (str, optional): Name of tool to use for the base
                tool.
            no_env (bool, optional: If True, don't include environment
                variables in the keyword arguments.
            **kwargs: Additional keyword arguments are parsed for
                specialization or alternate parameters and then added
                to the returned dictionary.

        Returns:
            dict: Keyword arguments.

        """
        assert self.is_rebuildable
        if tooltype == 'basetool':
            tooltype = self.tool(tooltype).tooltype
        if toolname:
            assert kwargs.get(tooltype, toolname) == toolname
            kwargs[tooltype] = toolname
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).tool_kwargs(
                tooltype, no_env=no_env,
                **self.specialization.remainder(kwargs))
        kwargs = self.specialization.remainder(kwargs)
        libtype = self['libtype']
        if 'products' not in kwargs:
            kwargs['products'] = tools.IntegrationPathSet(
                overwrite=kwargs.get('overwrite', False))
        dependencies = self.dependency_order(for_build=True)
        if self.is_rebuildable and not kwargs.get('dry_run', False):
            self.build_dependencies(dependencies=dependencies,
                                    local_products=kwargs['products'])
        tool = self.tool(tooltype)
        assert 'out' not in kwargs
        out = self.get(f'{tool.tooltype}_output', default=None, **kwargs)
        kwargs.update({
            'language': self.language,
            'libtype': libtype,
        })
        if out:
            kwargs['out'] = out
        for k in self.tool_parameters(tooltype):
            if k in [f'{tool.tooltype}_flags']:
                v = self.parameters.get(k, None)
            else:
                v = self.get(k, None)
            if isinstance(v, list):
                kwargs.setdefault(k, [])
                kwargs[k] = kwargs[k] + v
            elif v is not None:
                kwargs[k] = v
        suffix = self.suffix
        if suffix:
            kwargs['suffix'] = suffix
        kwargs = dependencies.getall(
            f'dep_{tool.tooltype}_kwargs', to_update=kwargs,
            dep_libtype=libtype)
        if not no_env:
            if not kwargs.get('env', None):
                kwargs['env'] = {}
                kwargs['env'].update(os.environ)
            kwargs['env'] = self.get(
                f'{tool.tooltype}_env', to_update=kwargs.get('env', None),
                for_build=True)
        next_tool = self.next_tool(tool, libtype)
        if ((next_tool
             and kwargs.get('force_simultaneous_next_stage', False))):
            next_kws = self.specialization.remainder(
                kwargs, remove_parameters=self.all_parameters())
            next_kws.pop('out', None)
            kwargs.update(
                self.tool_kwargs(next_tool.tooltype, **next_kws))
            kwargs[next_tool.tooltype] = next_tool
        return kwargs

    def tool_flags(self, tooltype='basetool', no_additional_stages=False,
                   **kwargs):
        r"""Get the flags for calling a tool.

        Args:
            tooltype (str, optional): Type of tool to get flags for.
            no_additional_stages (bool, optional): If True, only perform
                the first stage in the build process for the specified
                tooltype.
            **kwargs: Keyword arguments are passed to tool_kwargs.

        Returns:
            list: Flags for the tool.

        """
        kwargs['no_env'] = True
        assert self.is_rebuildable
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).tool_flags(
                tooltype, no_additional_stages=no_additional_stages,
                **self.specialization.remainder(kwargs))
        kwargs = self.tool_kwargs(tooltype, **kwargs)
        tool = self.tool(tooltype)
        out = tool.get_flags(**kwargs)
        next_tool = self.next_tool(tool, self['libtype'])
        if ((next_tool
             and not (no_additional_stages
                      or kwargs.get('force_simultaneous_next_stage', False)))):
            next_kws = self.specialization.remainder(
                kwargs, remove_parameters=self.all_parameters())
            next_kws.pop('out', None)
            out += self.tool_flags(next_tool.tooltype, **next_kws)
        return out

    def build(self, tooltype='basetool', no_additional_stages=False,
              **kwargs):
        r"""Call a tool to build part of this dependency.

        Args:
            tooltype (str, optional): Type of tool to use in build.
            no_additional_stages (bool, optional): If True, only perform
                the first stage in the build process for the specified
                tooltype.
            **kwargs: Keyword arguments are passed to the tool's call
                method after being updated by tool_kwargs.

        Returns:
            str: Output from the build command.

        """
        assert self.is_rebuildable
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).build(
                tooltype, no_additional_stages=no_additional_stages,
                **self.specialization.remainder(kwargs))
        tool = self.tool(tooltype)
        src = self.get(f'{tool.tooltype}_input', **kwargs)
        if ((self['libtype'] not in self.built_files
             or self['libtype'] in tool.input_filetypes)):
            return src
        if 'products' not in kwargs:
            kwargs['products'] = tools.IntegrationPathSet(
                overwrite=kwargs.get('overwrite', False))
        build_driver = kwargs.pop('build_driver',
                                  self.get('build_driver', None))
        exported_builds = kwargs.pop('exported_builds', [])
        if self.is_interface and build_driver:
            exported_builds.append(
                build_driver.create_exports(self, **kwargs))
            kwargs['overwrite'] = False
        if ((self.is_complete and (not kwargs.get('overwrite', False))
             and (not kwargs.get('dry_run', False)))):
            kwargs['products'].append(self.result)
            logger.debug(f"Result already exists, skipping "
                         f"compilation: {self.result}")
            return [self.result]
        try:
            kwargs = self.tool_kwargs(tooltype, **kwargs)
            if not kwargs.get('dry_run', False):
                kwargs['products'].setup(tag='build_time')
            out = tool.call(src, **kwargs)
        except BaseException:  # pragma: debug
            # Recursion can occur if the dependencies are not actually
            # being compiled or there is a mismatch in the path to
            # a compiled dependency and the path used by dependents
            self.logInfo(level=logging.ERROR)
            kwargs['products'].teardown(tag='build_time')
            kwargs['products'].teardown()
            raise
        next_tool = None
        if not (no_additional_stages
                or kwargs.get('force_simultaneous_next_stage', False)):
            next_tool = self.next_tool(tool, self['libtype'])
        if next_tool:
            next_kws = self.specialization.remainder(
                kwargs, remove_parameters=self.all_parameters())
            next_kws.pop('out', None)
            out = self.build(next_tool.tooltype, **next_kws)
        elif not (kwargs.get('dry_run', False)
                  or kwargs.get('no_file_produced', False)
                  or kwargs.get('target', False) == 'clean'):
            if out != kwargs['out']:
                raise AssertionError(f"Returned output ({out}) does "
                                     f"not matched the expected output "
                                     f"{kwargs['out']}")
            out0 = out[0] if isinstance(out, list) else out
            assert os.path.isfile(out0) or os.path.isdir(out0)
        if not kwargs.get('dry_run', False):
            kwargs['products'].teardown(tag='build_time')
        return out

    def build_dependencies(self, dependencies=None, exported_builds=None,
                           local_products=None, **kwargs):
        r"""Build the dependencies required to build this target.

        Args:
            dependencies (DependencyList, optional): Set of dependencies
                to build. If not provided, dependency_order for build
                will be used.
            exported_builds (list, optional): List that build export info
                should be appended to.
            local_products (tools.IntegratedPathSet, optional): Path set
                to update with products local to this dependency.
            **kwargs: Keyword arguments are passed to the build command
                for each of the dependencies.

        """
        assert self.is_rebuildable
        if not self.specialization.check(kwargs):
            return self.specialized(**kwargs).build_dependencies(
                dependencies=dependencies,
                exported_builds=exported_builds,
                local_products=local_products,
                **self.specialization.remainder(kwargs))
        if exported_builds is None:
            exported_builds = []
        if self.driver.is_build_tool:
            self['target_dep'].build_dependencies(
                exported_builds=exported_builds, build_driver=self.driver,
                **kwargs)
            if exported_builds and self.get('target', None) != 'clean':
                self.driver.create_imports(self, exported_builds[0],
                                           products=local_products,
                                           **kwargs)
        if dependencies is None:
            dependencies = self.dependency_order(for_build=True)
        for x in dependencies:
            if x.parent_driver == self.parent_driver and x.is_rebuildable:
                x.build(exported_builds=exported_builds, **kwargs)
        
    def products(self, products=None, include_dependencies=False):
        r"""Get the set of products produced by this dependency.

        Args:
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products should be appended to.
            include_dependencies (bool, optional): If True, include
                dependencies associated with the same driver as this one.

        Returns:
            tools.IntegrationPathSet: Updated product list.

        """
        if products is None:
            suffix = str(uuid.uuid4())[:13]
            products = tools.IntegrationPathSet(
                generalized_suffix=suffix)
        if self.is_rebuildable:
            self.build(dry_run=True, products=products)
        for k in self.generated:
            products.append_compilation_product(self.files[k])
        if include_dependencies:
            for x in self.dependency_order(for_build=True):
                if x.parent_driver == self.parent_driver:
                    x.products(products)
        return products

    def compile(self, **kwargs):
        r"""Compile a library.

        Args:
            **kwargs: Keyword arguments are passed to call_compiler.

        Returns:
            str: Output from the compilation command.

        """
        return self.build('compiler', **kwargs)

    def _dep_compiler_kwargs(self, to_update=None, **discard):
        if to_update is None:
            to_update = {}
        out = copy.deepcopy(
            self.parameters.get('dep_compiler_kwargs', {}))
        keymap = {'dep_compiler_flags': 'compiler_flags'}
        for k in ['include_dirs', 'definitions', 'dep_compiler_flags']:
            kd = keymap.get(k, k)
            out[kd] = to_update.get(kd, [])
            out[kd] += [x for x in self.get(k, []) if x not in out[kd]]
        if ((self['libtype'] in self.library_files + ['object']
             and self.requires_fullpath
             and not to_update.get('dry_run', False))):
            dep_lib = self.result
            if self.is_rebuildable and not os.path.isfile(dep_lib):
                dep_lib_result = self.build()[0]
                assert dep_lib == dep_lib_result
            if not os.path.isfile(dep_lib):
                raise RuntimeError(f"Library for {self.name} dependency "
                                   f"does not exist: '{dep_lib}'.")
        return out

    def _dep_libtool_kwargs(self, key, to_update=None, dep_libtype=None,
                            use_library_path_internal=False, **discard):
        if to_update is None:
            to_update = {}
        out = copy.deepcopy(self.parameters.get(key, {}))
        if dep_libtype is None:
            dep_libtype = 'executable'
        elif dep_libtype == 'windows_import':
            dep_libtype = 'shared'
        if ((self['libtype'] in self.library_files + ['object']
             and self.requires_fullpath
             and not to_update.get('dry_run', False))):
            dep_lib = self.result
            if self.is_rebuildable and not os.path.isfile(dep_lib):
                dep_lib_result = self.build()[0]
                assert dep_lib == dep_lib_result
            if not os.path.isfile(dep_lib):
                raise RuntimeError(f"Library for {self.name} dependency "
                                   f"does not exist: '{dep_lib}'.")
        if ((self['libtype'] in self.library_files
             and dep_libtype != 'static')):
            libkey = 'libraries'
            if use_library_path_internal and self.origin == 'internal':
                if to_update.get('skip_library_libs', False):
                    if isinstance(use_library_path_internal, bool):
                        libkey = 'library_flags'
                    else:
                        libkey = use_library_path_internal
                else:
                    libkey = 'flags'
            out[libkey] = to_update.get(libkey, [])
            if self['library'] not in out[libkey]:
                out[libkey].append(self['library'])
        elif self['libtype'] in ['object']:
            out['additional_objs'] = to_update.get('additional_objs', [])
            if self['object'] not in out['additional_objs']:
                out['additional_objs'].append(self['object'])
        tooltype = self.libtype2tool.get(dep_libtype, None)
        if tooltype:
            keymap = {f'dep_{dep_libtype}_flags': f'{tooltype}_flags'}
            for k in [f'dep_{dep_libtype}_flags']:
                kd = keymap.get(k, k)
                out[kd] = to_update.get(kd, [])
                out[kd] += [x for x in self.get(k, [])
                            if x not in out[kd]]
        return out

    def _shared_path_env(self, to_update=None, out=None,
                         paths_to_add=None, add_to_front=False,
                         env_var=None, add_linker_paths=False,
                         dont_update_return=False):
        if to_update is None:
            to_update = {}
            to_update.update(os.environ)
        if out is None:
            out = {}
        elif dont_update_return:
            to_update = dict(to_update, **out)
        else:
            to_update.update(out)
        if env_var is None:
            if platform._is_linux:
                env_var = 'LD_LIBRARY_PATH'
            elif platform._is_win:
                env_var = 'PATH'
            # else:
            #     env_var = 'DYLD_LIBRARY_PATH'
        if paths_to_add is None:
            paths_to_add = []
        if self['libtype'] in ['shared', 'windows_import']:
            paths_to_add.append(os.path.dirname(self.get('shared')))
        if add_linker_paths:
            paths_to_add += self.tool('linker').get_search_path(
                env_only=True)
        if env_var and paths_to_add:
            path_list = []
            prev_path = to_update.get(env_var, '')
            prev_path_list = []
            if prev_path:
                prev_path_list += prev_path.split(os.pathsep)
                path_list.append(prev_path)
            for x in paths_to_add:
                if x and x not in prev_path_list:
                    if add_to_front:
                        path_list.insert(0, x)
                    else:
                        path_list.append(x)
            if path_list:
                out[env_var] = os.pathsep.join(path_list)
        return out

    @classmethod
    def _update_env_val(cls, k, v, out, to_update=None):
        if to_update is None:
            to_update = out
        append_char = None
        overwrite = False
        if isinstance(v, dict):
            append_char = v.get('append', None)
            overwrite = v.get('overwrite', False)
            v = v['value']
        if not v:
            return
        if overwrite or k not in to_update:
            out[k] = v
        elif append_char:
            out[k] = to_update[k] + append_char + v

    def _update_env(self, vals, to_update=None, out=None,
                    dont_update_return=False):
        if to_update is None:
            to_update = {}
            to_update.update(os.environ)
        if out is None:
            out = {}
        elif dont_update_return:
            to_update = dict(to_update, **out)
        else:
            to_update.update(out)
        for k, v in vals.items():
            self._update_env_val(k, v, out, to_update=to_update)
        return out

    def _generic_env(self, key, to_update=None, for_build=False,
                     dont_update_return=False, **kwargs):
        if to_update is None:
            to_update = {}
            to_update.update(os.environ)
        out = self._shared_path_env(
            to_update=to_update, dont_update_return=dont_update_return,
            **kwargs)
        self._update_env(self.parameters.get('global_env', {}),
                         to_update=to_update, out=out,
                         dont_update_return=dont_update_return)
        self._update_env(self.parameters.get(key, {}),
                         to_update=to_update, out=out,
                         dont_update_return=dont_update_return)
        kws = dict(kwargs, dont_update_return=True, to_update=to_update)
        for x in self.dependency_order(for_build=for_build):
            if x != self:
                out.update(x.get(key, **kws))
        if ((self.parent_driver.is_build_tool
             and self.parameters.get('target_dep', False))):
            target_dep = self.parameters['target_dep']
            out.update(target_dep.get(key, **kws))
            for k in target_dep.active_tools():
                out.update(
                    target_dep.get(f'{k}_env', for_build=for_build, **kws))
        return out

    def _build_env(self, key, to_update=None,
                   for_build=False, **kwargs):
        if to_update is None:
            to_update = {}
            to_update.update(os.environ)
        out = self._generic_env(key, to_update=to_update,
                                for_build=for_build, **kwargs)
        if for_build:
            k = key.split('_env', 1)[0]
            tool = self.tool(k)
            tool.set_env(existing=out)
            if self.parameters.get('flags_in_env', False):
                kenv = self.parameters.get(
                    f'env_{k}', tool.default_executable_env)
                out[kenv] = tool.get_executable(full_path=True)
                if self.parameters.get('build_driver', False):
                    out[kenv] = self.parameters['build_driver'].fix_path(
                        out[kenv], for_env=True)
                kenv = self.parameters.get(
                    f'env_{k}_flags', tool.default_flags_env)
                out[kenv] = ' '.join(
                    self.get(f'{k}_flags', dry_run=True,
                             no_additional_stages=True,
                             skip_no_additional_stages_flag=True))
                for k in tool.additional_flags_env:
                    out[k] = ''
        return out
    
    def _runtime_env(self, to_update=None, **kwargs):
        if to_update is None:
            to_update = {}
            to_update.update(os.environ)
        out = self._generic_env('runtime_env', to_update=to_update,
                                **kwargs)
        if self.parameters.get('preload', False):
            lib = self['shared']
            if lib:
                self.tool('linker').preload_env(lib, out)
        return out

    def _search(self, filetype=None, **kwargs):
        if filetype is None:
            filetype = self.get('libtype', **kwargs)
        if filetype == 'header_only':
            filetype = 'include'
        kwargs['verbose'] = True  # TODO: Temporary
        out = False
        search_param = self._search_param(libtype=filetype)
        if ((filetype in ['shared', 'windows_import']
             and self.origin in ['standard', 'language'])):
            out = self._search_linked(search_param=search_param,
                                      libtype=filetype, **kwargs)
        if not out:
            out = self._search_brute(search_param=search_param,
                                     libtype=filetype, **kwargs)
        if (((not out) and self.origin in ['standard', 'language']
             and filetype in self.library_files)):
            out = self._build_output_base(filetype=filetype, **kwargs)
        if out:
            out = os.path.normpath(out)
        return out

    @classmethod
    def _search_regex(cls, fname_base, fname_ext):
        return (r'(?:(?:^)|(?:\s))(?:\@rpath'
                + tools.escape_regex(os.path.sep)
                + r')?(?P<path>(?P<base>(?:\S*[^a-zA-Z\s])?(?:lib)?'
                + tools.escape_regex(
                    fname_base[3:] if fname_base.startswith('lib')
                    else fname_base)
                + r'(?:[^a-zA-Z\.\s])*)(?P<ext>'
                + r'(?:[^a-zA-Z\s]\S*)?'
                + tools.escape_regex(fname_ext)
                + r'(?:[^a-zA-Z\s]\S*)?))'
                + r'(?:(?:$)|(?:\s))')

    def _search_param(self, fname=None, libtype=None):
        if libtype is None:
            libtype = self.get('libtype')
        if fname is None:
            if self.name == 'python':
                fname = tools.get_python_c_library(allow_failure=True,
                                                   libtype=libtype)
            elif self.name == 'numpy':
                fname = tools.get_numpy_c_library(allow_failure=True,
                                                  libtype=libtype)
            else:
                fname = self.parameters.get(libtype, self.name)
        fname_base, fname_ext = DependencyRegistry.splitext(fname)
        if not fname_ext:
            fname_base = self.prefix(libtype) + fname
            fname_ext = self.extension(libtype)
            fname = fname_base + fname_ext
        else:
            expected_ext = self.extension(libtype, return_all=True)
            if (((fname_ext not in expected_ext)
                 and not fname_ext.startswith(tuple(expected_ext)))):
                fname = fname_base + expected_ext[0]
                fname_ext = expected_ext[0]
        if os.path.isfile(fname):
            return [(fname_base, fname_ext, fname, None)]
        fname_base = os.path.basename(fname_base)
        fname_try = [fname_base]
        if platform._is_win and libtype in self.library_files:
            if fname_base.startswith('lib'):
                fname_try.append(fname_base[3:])
            else:
                fname_try.append('lib' + fname_base)
        return [(fname_base, fname_ext,
                 fname_base + '*' + fname_ext,
                 self._search_regex(fname_base, fname_ext))
                for fname_base in fname_try]

    def _search_linked(self, search_param=None, libtype=None, **kwargs):
        if libtype is None:
            libtype = self.get('libtype')
        if search_param is None:
            search_param = self._search_param(libtype=libtype)
        assert self.origin in ['standard', 'language']
        assert libtype in ['shared', 'windows_import']
        out = False
        if libtype == 'windows_import':
            dll = self.get('shared', False)
            if dll:
                out = self._search_brute(fname=dll, libtype=libtype,
                                         **kwargs)
            return out
        flags = self.get('dep_shared_flags', [])
        if not flags:
            if self.origin == 'standard':
                flags.append(f'-l{self.name}')
        try:
            for fname_base, fname_ext, fname, regex in search_param:
                if os.path.isfile(fname):
                    return fname
                for lib in self.basetool.find_component(
                        self.name, cfg=self.cfg, flags=flags,
                        component_types='shared_libraries',
                        regex=regex, **kwargs):
                    # TODO: temp
                    print(f"FIND_COMPONENT {self.name}: {lib}")
                    out = self._search_brute(fname=lib, libtype='shared',
                                             **kwargs)
                    if out:
                        break
                if out:
                    break
        except RuntimeError as e:
            logger.debug(f"Error in using diassembly to locate "
                         f"\'{self.name}\': {e}")
        return out

    def _search_brute(self, search_param=None, fname=None, libtype=None,
                      verbose=False, dont_check_windows_import=False,
                      **kwargs):
        r"""Locate a library file.

        Args:
            fname (str): Name of library.
            libtype (str, optional): Library type being searched for.
                Defaults to None.
            verbose (bool, optional): If True, display information about
                the success or failure of the search. Defaults to False.
            dont_check_windows_import (bool, optional): If True, a
                located windows import library will not be tested to
                check if the file is an import library or actually a
                static library.
            **kwargs: Additional keyword arguments are passed to
                get_search_path.

        Returns:
            str, bool: Full path to located library file or False if it
                cannot be located.

        """
        if libtype is None:
            libtype = self.get('libtype')
        if search_param is None:
            search_param = self._search_param(fname=fname,
                                              libtype=libtype)
        out = False
        search_list = self.tool(libtype).get_search_path(
            libtype=libtype, cfg=self.cfg, **kwargs)
        for fname_base, fname_ext, fname, use_regex in search_param:
            if os.path.isfile(fname):
                return fname
            out = tools.locate_file(fname, directory_list=search_list,
                                    environment_variable=None,
                                    use_regex=use_regex,
                                    select_return='shortest')
            if out:
                break
        if ((out and not dont_check_windows_import
             and libtype in ['static', 'windows_import']
             and platform._is_win)):  # pragma: windows
            is_wimp = is_windows_import(out)
            if is_wimp != (libtype == 'windows_import'):
                if verbose:
                    logger.info(f"Located {out} is not a "
                                f"{libtype} library")
                if libtype == 'windows_import':
                    alt_libtype = 'static'
                else:
                    alt_libtype = 'windows_import'
                self.files[self.key(alt_libtype)] = out
                out = False
        if out:
            assert os.path.isfile(out)
            out = os.path.abspath(out)
        if verbose:
            if out:
                logger.info(f'Located {fname}: {out}')
            else:
                logger.info(f"Could not locate {libtype} "
                            f"{fname} (search_list = "
                            f"\n\t" + '\n\t'.join(search_list) + ')')
        return out


# TODO: Cannot currently make compilation tools components because
# of circular imports
class CompilationToolMeta(type):
    r"""Meta class for registering compilers."""
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        global _tool_registry
        _tool_registry.register(cls)
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
        associated_tooltypes (list): Types of tools that are associated
            with this tool. [AUTOMATED]
        languages (list): Programming languages that this tool can be used on.
            [REQUIRED]
        platforms (list): Platforms that the tool is available on. Defaults to
            ['Windows', 'MacOS', 'Linux'].
        env (dict): Environment variables that should be updated when
            calling the tool.
        env_platform_specific (dict): Mapping of platform specific
            environment variables that should be updated when calling the
            tool.
        default_executable (str): The default tool executable command if
            different than the toolname.
        default_executable_env (str): Environment variable where the executable
            command might be stored.
        default_flags (list): Default flags that should be used when calling the
            tool (e.g. for verbose output or enhanced warnings).
        default_flags_env (str): Environment variable where default flags for
            the tools might be stored.
        default_libtype (str): Default file type that should result from
            a call to this tool.
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
        search_path_envvar (list): Environment variables containing a list of paths
            to search for library files. Either search_path_envvar or
            search_path_flags must be set. [REQUIRED]
        search_path_env (list): Paths relative to the env prefix that should
            be searched if the VIRTUAL_ENV or CONDA_PREFIX environment
            variable is set.
        search_path_flags (list): Flags that should be passed to the tool
            executable in order to locate the search path. Either search_path_envvar
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
        libtype_flags (dict): Mapping between output type and flags that
            should be used.
        libtype_prefix (dict): Mapping between output type and file
            prefix.
        libtype_suffix (dict): Mapping between output type and file
            suffix.
        libtype_ext (dict): Mapping between output type and file
            extension.
        libtype_next_stage (dict): Mapping between output type and the
            tool for the next stage in the build.
        standard_library (str): Standard library automatically included
            by the linker.
        standard_library_type (str): Type of standard_library.
        libraries (dict): Parameters for librarys associated with this
            tool
        builtin_next_stage (str): Tool type for the next stage that can
            be called as part of calls to this tool.
        combine_with_next_stage (str): Tool that this tool should be
            combined with on the command line where arguments for the
            next stage are passed to the this stage's executable to
            perform both operations in succession. If not set and
            builtin_next_stage is set, this will be set to this tool's
            name.
        no_additional_stages_flag (str): Flag to indicate that additional
            stages that can also be handled by this tool should not be
            completed (e.g. -c for GNU compiler).
        next_stage_switch (str): Flag to indicate beginning of flags that
            should be passed to the tool for the next stage. (e.g. /link
            for MSVC cl.exe).
        next_stage_flag_flag (str): Flag to indicate that the next flag
            should be passed to the next stage.
        create_next_stage_tool (dict): Parameters for a tool that should
            be created for the next stage based on this tool.
        local_kws (list): Keyword arguments that are unique to this tool.
        build_params (list): Additional dependency parameters that should
            be passed to this tool's get_flags or call methods.

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
    associated_tooltypes = []
    basetooltype = None
    basetool = None
    input_filetypes = []
    output_filetypes = []
    languages = []
    platforms = ['Windows', 'MacOS', 'Linux']  # all by default
    env = {}
    env_platform_specific = {
        'MacOS': {
            'CONDA_BUILD_SYSROOT': {
                'value': _osx_sysroot,
                'overwrite': True,
            },
            'SDKROOT': {
                'value': _osx_sysroot,
                'overwrite': True,
            },
            'MACOSX_DEPLOYMENT_TARGET': {
                'value': (
                    re.search(
                        r'MacOSX(?P<target>[0-9]+\.[0-9]+)?',
                        _osx_sysroot).groupdict()['target']
                    if _osx_sysroot else False),
                'overwrite': True,
            },
        }
    }
    default_executable = None
    default_executable_env = None
    default_flags = []
    default_flags_env = None
    default_libtype = None
    additional_flags_env = []
    output_key = '-o'
    output_first = False
    flag_options = OrderedDict()
    search_path_envvar = None
    search_path_env = None
    search_path_flags = None
    search_regex_begin = None
    search_regex_end = None
    search_regex = ['([^\n]+)']
    version_flags = ['--version']
    version_regex = None
    product_exts = []
    product_files = []
    remove_product_exts = []
    libtype_flags = {}
    libtype_prefix = {}
    libtype_suffix = {}
    libtype_ext = {}
    libtype_next_stage = {}
    standard_library = None
    standard_library_type = None
    libraries = {}
    builtin_next_stage = None
    combine_with_next_stage = None
    no_additional_stages_flag = None
    next_stage_switch = None
    next_stage_flag_flag = None
    create_next_stage_tool = None
    is_gnu = False
    toolset = None
    compatible_toolsets = []
    is_build_tool = False
    tool_suffix_format = '_%sx'
    no_output_file = False
    _language_ext = None  # only update once per class
    _language_cache = {}
    _is_mingw = None
    local_kws = []
    build_params = []
    
    def __init__(self, **kwargs):
        for k in ['executable', 'flags']:
            v = kwargs.pop(k, None)
            if v is not None:
                setattr(self, k, v)
        for k in self.associated_tooltypes:
            for kk in [k, f'{k}_flags']:
                v = kwargs.pop(kk, None)
                if v:
                    setattr(self, f'_{kk}', v)
        if len(kwargs) > 0:
            raise RuntimeError(f"Unused keyword arguments: {kwargs.keys()}")
        super(CompilationToolBase, self).__init__(**kwargs)

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for k in ['executable', 'flags']:
            if getattr(self, k, None) != getattr(other, k, None):
                return False
        for k in self.associated_tooltypes:
            for kk in [k, f'{k}_flags']:
                if ((getattr(self, f'_{kk}', None)
                     != getattr(other, f'_{kk}', None))):
                    return False
        return True

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        if cls.toolname is None:  # pragma: debug
            raise CompilationToolError("Registering unnamed compilation tool.")
        cls.is_gnu = (cls.toolset == 'gnu')
        if (cls.toolset is not None) and (cls.toolset not in cls.compatible_toolsets):
            cls.compatible_toolsets = [cls.toolset] + cls.compatible_toolsets
        cls._schema_type = cls.tooltype
        for k in ['default_executable', 'default_flags']:
            # Copy so that list modification is not propagated to subclasses
            setattr(cls, k, copy.deepcopy(getattr(cls, k, [])))
        # Set attributes based on environment variables or sysconfig
        if cls.default_executable is None:
            cls.default_executable = cls.env_matches_tool()
        if cls.default_executable is None:
            cls.default_executable = cls.env_matches_tool(
                use_sysconfig=True)
        # Set default_executable to name
        if cls.default_executable is None:
            cls.default_executable = cls.toolname
        # Add executable extension
        if platform._is_win:  # pragma: windows
            if not cls.default_executable.endswith('.exe'):
                cls.default_executable += '.exe'
        # Add defaults for associated tools
        for k in cls.associated_tooltypes:
            if not hasattr(cls, f'default_{k}'):
                setattr(cls, f'default_{k}', None)
            if not hasattr(cls, f'default_{k}_flags'):
                setattr(cls, f'default_{k}_flags', None)
            if not hasattr(cls, f'{k}_language'):
                setattr(cls, f'default_{k}_language', None)
        # Handle stages
        if cls.builtin_next_stage and not cls.combine_with_next_stage:
            cls.combine_with_next_stage = cls.toolname
        if cls.create_next_stage_tool:
            assert cls.combine_with_next_stage
            copy_attr = ['toolname', 'aliases', 'languages', 'platforms',
                         'default_executable', 'default_executable_env',
                         'toolset', 'version_flags', 'version_regex']
            if cls.create_next_stage_tool is True:
                cls.create_next_stage_tool = {}
            stage_attr = copy.deepcopy(
                cls.create_next_stage_tool.get('attributes', {}))
            stage_type = stage_attr.get(
                'tooltype', cls.builtin_next_stage)
            stage_base = cls.__name__.split(cls.tooltype.title())[0]
            stage_name = f"{stage_base}{stage_type.title()}"
            for k in copy_attr:
                stage_attr.setdefault(k, getattr(cls, k))
            global _tool_registry
            base_cls = cls.create_next_stage_tool.get(
                'base_classes', (_tool_registry._bases[stage_type], ))
            stage_cls = type(stage_name, base_cls, stage_attr)
            globals()[stage_cls.__name__] = stage_cls
            del stage_cls

    @classmethod
    def get_tool(cls, tooltype, allow_uninstalled=False,
                 force_simultaneous_next_stage=False, **kwargs):
        r"""Get the associate class for the required tool type.

        Args:
            tooltype (str): Type of tool to return.
            allow_uninstalled (bool, optional): If True, the returned
                tool may not be installed.
            force_simultaneous_next_stage (bool, optional): If True,
                the returned tool will allow simultaneous build.
            **kwargs: Additional keyword arguments are passed to
                CompilationToolRegistry.tool.

        Returns:
            CompilationToolBase: Tool class associated with this compiler.

        """
        global _tool_registry
        if ((tooltype == cls.tooltype
             and kwargs.get('language', None) in cls.languages
             and _tool_registry._matches(cls, **kwargs))):
            return cls
        if ((force_simultaneous_next_stage
             and tooltype == cls.builtin_next_stage
             and cls.combine_with_next_stage)):
            return _tool_registry.tool_instance(
                cls.builtin_next_stage, cls.combine_with_next_stage,
                only_installed=(not allow_uninstalled), **kwargs)
        if tooltype in cls.associated_tooltypes:
            kwargs.setdefault(
                'language',
                getattr(cls, f'default_{tooltype}_language', None))
            if not kwargs['language']:
                kwargs['language'] = cls.languages[0]
            if kwargs['language'] in cls.languages:
                kwargs.setdefault(
                    'toolname',
                    getattr(cls, f'_{tooltype}',
                            getattr(cls, f'default_{tooltype}')))
                kwargs.setdefault(
                    'flags',
                    getattr(cls, f'_{tooltype}_flags',
                            getattr(cls, f'default_{tooltype}_flags')))
        kwargs.setdefault('compatible_with', cls)
        kwargs['only_installed'] = (not allow_uninstalled)
        return _tool_registry.tool_instance(tooltype, **kwargs)

    @classmethod
    def compiler(cls, **kwargs):
        r"""Get the associated compiler class.

        Args:
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            CompilationToolBase: Compiler class associated with this compiler.

        """
        return cls.get_tool('compiler', **kwargs)

    @classmethod
    def linker(cls, **kwargs):
        r"""Get the associated linker class.

        Args:
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            CompilationToolBase: Linker class associated with this compiler.

        """
        return cls.get_tool('linker', **kwargs)

    @classmethod
    def archiver(cls, **kwargs):
        r"""Get the associated archiver class.

        Args:
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            ArchiverToolBase: Archiver class associated with this compiler.

        """
        return cls.get_tool('archiver', **kwargs)

    @classmethod
    def disassembler(cls, **kwargs):
        r"""Get the associated disassembler class.

        Args:
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            CompilationToolBase: Disassembler class associated with this
                compiler.

        """
        return cls.get_tool('disassembler', **kwargs)

    @classmethod
    def is_mingw(cls):
        r"""Check if the class provides access to a mingw/msys compiler"""
        if cls._is_mingw is None:
            ver = cls.tool_version()
            cls._is_mingw = ('mingw' in ver.lower()
                             or 'msys' in ver.lower())
            logger.info(f"Setting is_mingw to {cls._is_mingw}: "
                        f"ver = {ver}")
        return cls._is_mingw
    
    @classmethod
    def get_language_ext(cls, languages=None):
        r"""Get the extensions associated with the language that this tool can
        handle.

        Returns:
            list: Language file extensions.

        """
        if languages is None:
            languages = cls.languages
        if cls._language_ext is None:
            cls._language_ext = []
            for x in languages:
                new_ext = import_component('model', x).get_language_ext()
                if new_ext is not None:
                    cls._language_ext += new_ext
        return cls._language_ext

    @classmethod
    def get_alternate_class(cls, toolname=None, language=None):
        r"""Return an alternate class to use if the provided toolname
        dosn't match the current tool.

        Args:
            toolname (str, optional): Name of compilation tool that
                should be used. Defaults to None and the current
                toolname is assumed.
            language (str, optional): Language that alternate class
                should support. Defaults to None and the current
                language will be assumed.

        Returns:
            CompilationToolBase: The compilation tool that corresponds
                to the provided toolname.

        """
        global _tool_registry
        if (language is not None) and (language not in cls.languages):
            if toolname is None:
                toolname = cls.toolname
            lang_drv = import_component('model', language)
            cls = lang_drv.get_tool(cls.tooltype, toolname=toolname)
        elif ((toolname is not None) and (toolname != cls.toolname)
              and (toolname not in cls.aliases)):
            cls = _tool_registry.tool(cls.tooltype, toolname)
        return cls
            
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
        for k, v in dict(cls.env, **cls.env_platform_specific.get(
                platform._platform, {})).items():
            CompilationDependency._update_env_val(k, v, existing,
                                                  to_update=existing)
        if not cls.env_matches_tool():
            config_vars = {}
            cls.env_matches_tool(use_sysconfig=True, env=config_vars)
            env_vars = []
            env = getattr(cls, 'default_flags_env', None)
            if env is not None:
                if not isinstance(env, list):
                    env = [env]
                env_vars += env
            env_vars += cls.additional_flags_env
            for ienv in env_vars:
                existing.pop(ienv, [])
                if ienv in config_vars:
                    existing[ienv] = config_vars[ienv]
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
        return DependencyRegistry.splitext(os.path.basename(fname))[0]

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
            allow_duplicate_values (bool, optional): If True, the same
                key can be added with the same value more than once.
                Otherwise, only the first instance of the value is added.
                Defaults to False.

        Raises:
            ValueError: If there are unexpected keyword arguments.
            ValueError: If no_duplicates is True and the existing list of flags
                already contains a flag matching the provided flag key.

        """
        # Access class level flag option definitions
        if isinstance(key, str) and (key in cls.flag_options):
            key = cls.flag_options[key]
        if isinstance(key, dict):
            for k, v in key.items():
                if k != 'key':
                    kwargs.setdefault(k, v)
            key = key['key']
        # Loop over list
        if isinstance(value, list):
            if not kwargs.get('allow_duplicate_values', False):
                new_value = []
                for v in value:
                    if v not in new_value:
                        new_value.append(v)
                value = new_value
            for i, v in enumerate(value):
                cls.append_flags(out, key, v, **kwargs)
            return
        # Unpack keyword arguments
        prepend = kwargs.pop('prepend', False)
        position = kwargs.pop('position', None)
        no_duplicates = kwargs.pop('no_duplicates', None)
        allow_duplicate_values = kwargs.pop('allow_duplicate_values', None)
        if kwargs:  # pragma: debug
            raise ValueError(f"Unexpected keyword arguments: {kwargs}")
        # Create flags and check for duplicates
        new_flags = cls.create_flag(key, value)
        if no_duplicates:
            for o in out:
                if scanf.scanf(key, o):
                    raise ValueError(f"Flag for key {key} already "
                                     f"exists: '{o}'")
        # Check for exact matches
        if new_flags and (not allow_duplicate_values):
            idx = 0
            nnew = len(new_flags)
            nout = len(out)
            while idx < nout:
                if new_flags[0] not in out[idx:]:
                    break
                ibeg = idx + out[idx:].index(new_flags[0])
                iend = ibeg + nnew
                if (iend < nout) and (out[ibeg:iend] == new_flags):
                    return
                idx = iend
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
        if (not isinstance(key, (dict, list))) and (key in cls.flag_options):
            key = cls.flag_options[key]
        if isinstance(key, dict):
            key = key['key']
        if isinstance(value, list):
            out = []
            for v in value:
                out += cls.create_flag(key, v)
        elif isinstance(key, list):
            out = []
            for k in key:
                out += cls.create_flag(k, value)
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
        try:
            cls.get_executable()
            return True
        except InvalidCompilationTool:
            return False

    @classmethod
    def env_matches_tool(cls, use_sysconfig=False, env=None,
                         with_flags=False, verbose=False):
        r"""Determine if the executable pointed to by any environment
        variable matches this compilation tool.

        Args:
            use_sysconfig (bool, optional): If True, check the
                sysconfig variables, otherwise check os.environ.
                Defaults to False.
            env (dict, optional): Existing dictionary that should be
                updated with variables. Defaults to None and is ignored.
            with_flags (bool, optional): If True, preserve any flags
                included in the environment variable. Defaults to False.
            verbose (bool, optional): If True, print out information about
                the tools that were compared and the result.

        Returns:
            bool: True if the environment variable matches, False otherwise.

        """
        if env is None:
            env = {}
        if use_sysconfig:
            env.update(sysconfig.get_config_vars())
        else:
            env.update(os.environ)
        envi_full = ''
        if isinstance(cls.default_executable_env, str):
            envi_full = env.get(cls.default_executable_env, '').split(
                'ccache ')[-1]
        if envi_full:
            this_executable = (cls.default_executable
                               if cls.default_executable
                               else cls.toolname)
            envi_executable = envi_full.split(maxsplit=1)[0]
            out = envi_full if with_flags else envi_full.split(maxsplit=1)[0]
            this_version = CompilationToolBase.tool_version_static(
                cls, this_executable, require_match=True)
            envi_version = CompilationToolBase.tool_version_static(
                cls, envi_executable, require_match=True)
            if this_version and this_version and this_version == envi_version:
                if verbose:
                    logger.info(f"{cls.tooltype.title()} {cls.toolname} "
                                f"matches environment variable "
                                f"(use_sysconfig={use_sysconfig}) "
                                f"{cls.default_executable_env}:"
                                f"\n\t{envi_full}"
                                f"\n\ttool_exe = {this_executable}"
                                f"\n\tenvi_exe = {envi_executable}"
                                f"\n\ttool_ver = {this_version}"
                                f"\n\tenvi_ver = {envi_version}")
                return out
            if this_executable == cls.toolname and envi_version:
                if verbose:
                    logger.info(f"{cls.tooltype.title()} {cls.toolname} "
                                f"overriden from environment variable "
                                f"(use_sysconfig={use_sysconfig}) "
                                f"{cls.default_executable_env}:"
                                f"\n\t{envi_full}"
                                f"\n\ttool_exe = {this_executable}"
                                f"\n\tenvi_exe = {envi_executable}"
                                f"\n\ttool_ver = {this_version}"
                                f"\n\tenvi_ver = {envi_version}")
                return out
            if this_version and envi_version:
                if verbose:
                    logger.info(f"{cls.tooltype.title()} {cls.toolname} "
                                f"does not match environment variable "
                                f"(use_sysconfig={use_sysconfig}) "
                                f"{cls.default_executable_env}:"
                                f"\n\ttool_exe = {this_executable}"
                                f"\n\tenvi_exe = {envi_executable}"
                                f"\n\ttool_ver = {this_version}"
                                f"\n\tenvi_ver = {envi_version}")
        return None

    @classmethod
    def get_env_flags(cls):
        r"""Get a list of flags stored in the environment variables.

        Returns:
            list: Flags for the tool.

        """
        out = []
        env_dict = {}
        exe = cls.env_matches_tool(env=env_dict, with_flags=True)
        if not exe:
            exe = cls.env_matches_tool(env=env_dict, with_flags=True,
                                       use_sysconfig=True)
        if exe and env_dict:
            out += exe.split()[1:]
            env_vars = []
            env = getattr(cls, 'default_flags_env', None)
            if env is not None:
                if not isinstance(env, list):
                    env = [env]
                env_vars += env
            env_vars += cls.additional_flags_env
            for ienv in env_vars:
                new_val = env_dict.get(ienv, '').split()
                out += [v for v in new_val if v not in out]
        return out

    @classmethod
    def get_default_libtype(cls, no_additional_stages=False):
        r"""Get the default output type that this tool produces.

        Args:
            no_additional_stages (bool, optional): If True, the type is
                determined for this tool in isolation.

        Returns:
            str: Product file type.

        """
        global _tool_registry
        if no_additional_stages or not cls.builtin_next_stage:
            return cls.default_libtype
        return _tool_registry._bases[cls.builtin_next_stage].default_libtype

    @classmethod
    def get_flags(cls, flags=None, outfile=None, libtype=None,
                  output_first=None, unused_kwargs=None,
                  skip_defaults=False, dont_skip_env_defaults=False,
                  skip_no_additional_stages_flag=False,
                  additional_args=None, add_next_stage_switch=False,
                  force_simultaneous_next_stage=False, **kwargs):
        r"""Get a list of flags for the tool.

        Args:
            flags (list, optional): User defined flags that should be
                included. Defaults to empty list.
            outfile (str, optional): If provided, it is appended to the
                end of the flags following the cls.output_key flag to
                indicate that this is the name of the output file.
                Defaults to None and is ignored.
            libtype (str, optional): Type of file that flags should
                produce.
            output_first (bool, optional): If True, output flag(s) will
                be placed at the front of the returned flags. If False,
                they are placed at the end. Defaults to None and is set
                by cls.output_first.
            unused_kwargs (dict, optional): Existing dictionary that
                unused keyword arguments should be added to. Defaults to
                None and is ignored.
            skip_defaults (bool, optional): If True, the default flags
                will not be added. Defaults to False.
            dont_skip_env_defaults (bool, optional): If skip_defaults is
                True, and this keyword is True, the flags from the
                environment variable will be added. Defaults to False.
            skip_no_additional_stages_flag (bool, optional): If True,
                don't include the no_additional_stages_flag even if
                no_additional_stages is True.
            add_next_stage_switch (bool optional): If True, the switch
                that indicates that flags for the next stage are
                beginning will be added.
            force_simultaneous_next_stage (bool, optional): If True,
                force the next stage to be performed by the same command
                as this one.
            **kwargs: Additional keyword arguments are ignored and added
                to unused_kwargs if provided.

        Returns:
            list: Flags for the tool.

        """
        no_additional_stages = (not force_simultaneous_next_stage)
        if libtype is None:
            libtype = cls.get_default_libtype(
                no_additional_stages=no_additional_stages)
        if flags is None:
            flags = []
        flags = kwargs.pop(f'{cls.tooltype}_flags', flags)
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
            new_flags = cls.default_flags.copy()
            new_flags += [x for x in cls.get_env_flags()
                          if x not in new_flags]
            # It is on the user to make sure there are not conflicting
            # flags when an error is thrown
            out += new_flags + getattr(cls, 'flags', [])
        # Add class defined flags
        for k in cls.flag_options.keys():
            if k in kwargs:
                cls.append_flags(out, k, kwargs.pop(k))
        # Add output file
        if (outfile is not None) and (cls.output_key is not None):
            cls.append_flags(out, cls.output_key, outfile,
                             prepend=output_first, no_duplicates=True)
        # Add flags for this stage only
        if ((no_additional_stages and cls.no_additional_stages_flag
             and (not skip_no_additional_stages_flag)
             and cls.no_additional_stages_flag not in out)):
            out.insert(0, cls.no_additional_stages_flag)
        # Add switch for next stage
        if ((((not no_additional_stages) or add_next_stage_switch
              or force_simultaneous_next_stage)
             and cls.next_stage_switch
             and cls.next_stage_switch not in out)):
            out.append(cls.next_stage_switch)
        # Handle unused keyword argumetns
        if unused_kwargs is None:
            unused_kwargs = {}
        unused_kwargs.update(kwargs)
        # Add flags for next stage
        if force_simultaneous_next_stage:
            next_tooltype = cls.libtype_next_stage.get(libtype, None)
            if not next_tooltype:
                raise CompilationToolError(
                    f"force_simultaneous_next_stage set to True, "
                    f"but there is not an additional stage for "
                    f"'{libtype}' builds")
            if next_tooltype != cls.builtin_next_stage:
                raise CompilationToolError(
                    f"force_simultaneous_next_stage set to True, "
                    f"but the next tool required for '{libtype}' builds "
                    f"({next_tooltype}) cannot be performed with the "
                    f"{cls.toolname} {cls.tooltype}")
            next_outfile = None
            next_unused_kwargs = {}
            next_tool = unused_kwargs.pop(next_tooltype, None)
            if next_tool is None:
                next_tool = cls.get_tool(next_tooltype,
                                         force_simultaneous_next_stage=True)
            if next_tool.toolname != cls.combine_with_next_stage:
                raise CompilationToolError(
                    f"Cannot combine {next_tooltype} "
                    f"({next_tool.toolname}) and {cls.tooltype} "
                    f"({cls.toolname}) flags")
            logger.debug(f'The returned flags will contain '
                         f'{next_tooltype} flags that may need to '
                         f'follow the list of source files.')
            out += next_tool.get_flags(
                outfile=next_outfile, libtype=libtype,
                unused_kwargs=next_unused_kwargs, **unused_kwargs)
            for k in copy.deepcopy(list(unused_kwargs.keys())):
                if k not in next_unused_kwargs:
                    del unused_kwargs[k]
        if cls.libtype_flags.get(libtype, None):
            out.insert(0, cls.libtype_flags[libtype])
        if additional_args:
            out += additional_args
        return out

    @classmethod
    def get_executable(cls, full_path=False):
        r"""Determine the executable that should be used to call this tool.

        Args:
            full_path (bool, optional): If True the full path to the executable
                file will be returned. Defaults to False.

        Returns:
            str: Name of (or path to) the tool executable.

        """
        out = getattr(cls, 'executable', None)
        if out is None:
            from yggdrasil.config import ygg_cfg
            out = cls.default_executable
            if cls.languages:
                out = ygg_cfg.get(cls.languages[0],
                                  f'{cls.toolname}_executable',
                                  out)
        if out is None or not (os.path.isfile(out) or shutil.which(out)):
            raise InvalidCompilationTool(f"Executable invalid for "
                                         f"{cls.tooltype} "
                                         f"'{cls.toolname}': {out}.")
        if full_path:
            out = shutil.which(out)
        return out

    @classmethod
    def get_env_prefixes(cls):
        r"""Determine the virtualenv/conda path prefixes.

        Returns:
            list: Virtualenv/conda path prefixes. Empty list will be
                returned if virtualenv/conda are not active.

        """
        return tools.get_env_prefixes()
            
    @classmethod
    def get_search_path(cls, env_only=False, libtype=None, cfg=None,
                        **kwargs):
        r"""Determine the paths searched by the tool for external library files.

        Args:
            env_only (bool, optional): If True, only the search paths as
                indicated by a virtualenv/conda environment are returned.
                Defaults to False.
            libtype (str, optional): Library type being searched for.
                Defaults to None.
            cfg (YggConfigParser, optional): Configuration object currently
                being updated. Defaults to the global configuration.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: List of paths that the tools will search.

        """
        if cfg is None:
            from yggdrasil.config import ygg_cfg
            cfg = ygg_cfg
        if (cls.search_path_flags is None) and (cls.search_path_envvar is None):
            raise NotImplementedError("get_search_path method not implemented for "
                                      "%s tool '%s'" % (cls.tooltype, cls.toolname))
        if libtype == 'include':
            suffix = 'include'
        else:
            suffix = 'lib'
        paths = []
        # Add path based on executable
        exec_file = cls.get_executable(full_path=True)
        if exec_file is not None:
            prefix, exec_dir = os.path.split(os.path.dirname(exec_file))
            if exec_dir == 'bin':
                paths.append(os.path.join(prefix, suffix))
        # Get search paths from environment variable
        if (cls.search_path_envvar is not None) and (not env_only):
            assert isinstance(cls.search_path_envvar, list)
            for ienv in cls.search_path_envvar:
                if os.environ.get(ienv, ''):
                    paths += os.environ[ienv].split(os.pathsep)
        # Get flags based on path
        if (cls.search_path_flags is not None) and (not env_only):
            output = cls.call(cls.search_path_flags, for_version=True)[0]
            # Split on beginning & ending regexes if they exist
            if cls.search_regex_begin is not None:
                output = re.split(cls.search_regex_begin, output)[-1]
            if cls.search_regex_end is not None:
                output = re.split(cls.search_regex_end, output)[0]
            # Search for paths
            for r in cls.search_regex:
                paths += re.findall(r, output)
        # Get search paths from the virtualenv/conda environment
        if (cls.search_path_env is not None):
            for iprefix in cls.get_env_prefixes():
                assert isinstance(cls.search_path_env, list)
                for ienv in cls.search_path_env:
                    paths.append(os.path.join(iprefix, ienv))
        # Get libtype specific search paths
        if platform._is_win:  # pragma: windows
            base_paths = []
            vcpkg_suffix = 'bin' if libtype == 'shared' else suffix
            vcpkg_dir = cfg.get('c', 'vcpkg_dir', None)
            if vcpkg_dir is not None:
                if not os.path.isdir(vcpkg_dir):  # pragma: debug
                    raise RuntimeError(f"vcpkg_dir is not valid: '{vcpkg_dir}'")
                if platform._is_64bit:
                    arch = 'x64-windows'
                else:  # pragma: debug
                    arch = 'x86-windows'
                    raise NotImplementedError("Not yet tested on 32bit Python")
                if os.path.isdir(os.path.join(vcpkg_dir, 'installed')):
                    paths.append(os.path.join(vcpkg_dir, 'installed',
                                              arch, vcpkg_suffix))
                    if not os.path.isdir(paths[-1]):  # pragma: debug
                        partial = vcpkg_dir
                        for x in ['installed', arch, vcpkg_suffix]:
                            next_partial = os.path.join(partial, x)
                            if not os.path.isdir(next_partial):
                                files = glob.glob(os.path.join(partial, '*'))
                                logger.error(f'missing {next_partial}: '
                                             f'{files}')
                                break
                            partial = next_partial
                        raise RuntimeError(r"vcpkg subdirectory does not "
                                           r"exist: {paths[-1]}")
            if os.environ.get('ChocolateyInstall'.upper(), None):
                base_paths.append(os.environ['ChocolateyInstall'])
        else:
            base_paths = ['/usr', os.path.join('/usr', 'local')]
        brew_prefix = None
        if platform._is_mac:
            macos_sdkroot = cfg.get('c', 'macos_sdkroot', None)
            base_paths += [
                '/Library/Developer/CommandLineTools/usr',
                # XCode >= 12
                '/Applications/Xcode.app/Contents/Developer/'
                'Toolchains/XcodeDefault.xctoolchain/usr',
                '/usr/local/opt/llvm']
            if macos_sdkroot is not None:
                base_paths.append(os.path.join(macos_sdkroot, 'usr'))
                if 'Platforms' in macos_sdkroot:
                    base_paths.append(
                        os.path.join(
                            macos_sdkroot.split('/Platforms', 1)[0],
                            'Toolchains/XcodeDefault.xctoolchain/usr'))
            try:
                brew_prefix = subprocess.check_output(
                    ['brew', '--prefix']).decode('utf-8').strip()
                base_paths.append(brew_prefix)
            except (subprocess.CalledProcessError, OSError):
                pass
        for base in base_paths:
            paths.append(os.path.join(base, suffix))
        if platform._is_mac:
            # Check homebrew llvm
            # paths.append('/usr/local/Cellar/llvm/')
            for x in glob.glob(os.path.join(
                    macos_sdkroot.split('/Platforms', 1)[0], 'Platforms',
                    '*', '')):
                if ((('AppleTV' not in x) and ('iPhoneOS' not in x)
                     and ('WatchOS' not in x))):
                    paths.append(x)
            if brew_prefix:
                paths += [
                    os.path.join(brew_prefix, 'llvm'),
                    os.path.join(brew_prefix, suffix, 'llvm'),
                ]
            paths += [
                "/usr/local/Cellar/llvm/"]
        out = []
        for x in paths:
            if x and (x not in out) and os.path.isdir(x):
                out.append(x)
        return out

    @classmethod
    def cache_key(cls, fname, libtype, cache_toolname=False,
                  cache_key_base=None, **kwargs):
        r"""Get a key to use for a cached library path.

        Args:
            fname (str): Name of library.
            libtype (str): Library type being searched for.
            cache_toolname (bool, optional): If True, the toolname will
                be added to the cache entry.
            cache_key_base (str, optional): Alternate key to use for the
                key base. If not provided, one will be created from fname.
            **kwargs: Additional keyword arguments will be ignored.

        Returns:
            str: Cache key.
        
        """
        if cache_key_base is None:
            cache_key_base = os.path.basename(
                DependencyRegistry.splitext(fname)[0])
            if cache_key_base.startswith('lib'):
                cache_key_base = cache_key_base[3:]
            if '.' in cache_key_base:
                cache_key_base = cache_key_base.split('.')[0]
        cache_key = f"{cache_key_base}_{libtype}"
        if libtype == 'windows_import' or cache_toolname:
            cache_key += f"_{cls.toolname}"
        return cache_key

    @classmethod
    def get_executable_command(cls, args, skip_flags=False,
                               unused_kwargs=None, use_ccache=False,
                               executable=None, **kwargs):
        r"""Determine the command required to run the tool using the
        specified arguments and options.

        Args:
            args (list): The arguments that should be passed to the tool.
                If skip_flags is False, these are treated as input files
                that will be used by the tool.
            skip_flags (bool, optional): If True, args is assumed to
                include any necessary flags. If False, args are assumed
                to the files that the tool is called on and flags are
                determined from them. Defaults to False.
            unused_kwargs (dict, optional): Existing Python dictionary
                that unused keyword arguments will be added to. Defaults
                to None and is initialized to an empty dict.
            use_ccache (bool, optional): If True, ccache will be added to
                the compilation executable. Defaults to False.
            executable (str, optional): Executable that should be used.
                If not provided, the output of cls.get_executable(full_path=True)
                will be used.
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
        if executable is None:
            executable = cls.get_executable(full_path=True)
        cmd = flags + args + library_flags
        cmd = [executable] + cmd
        if use_ccache and shutil.which('ccache'):
            cmd = ['ccache'] + cmd
        # Pop library flags so it is not an unused_kwarg in cases of
        # non-linking compiler command
        for k in ['library_flags', 'skip_library_libs']:
            unused_kwargs.pop(k, [])
        cmd = [x for x in cmd if x]
        return cmd

    @classmethod
    def append_product(cls, products, new, sources=None,
                       exclude_sources=False, **kwargs):
        r"""Append a product to the specified list along with additional
        values indicated by cls.product_exts.

        Args:
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products produced by the compilation
                should be appended to.
            new (str): New product that should be appended to the list.
            sources (list, optional): Source files associated with the
                new product.
            exclude_sources (bool, optional): If True, the sources will
                be excluded from the removable files.
            **kwargs: Additional keyword arguments are passed to
                IntegrationPathSet.append_compilation_product

        Returns:
            CompilationProduct: Compilation product added to products for
                new.

        """
        assert isinstance(products, tools.IntegrationPathSet)
        kwargs.setdefault('extensions', [])
        kwargs.setdefault('files', [])
        kwargs.setdefault('removable_source_exts',
                          tuple(cls.remove_product_exts))
        kwargs['extensions'] += cls.product_exts
        if exclude_sources:
            kwargs['sources'] = sources
        kwargs['files'] += cls.product_files
        products.append_compilation_product(new, **kwargs)
        return products.last

    @staticmethod
    def extract_tool_version(cls, x, require_match=False):
        r"""Extract the tool's version from the provided string.

        Args:
            x (str): Raw version string.
            require_match (bool, optional): If True, a match to
                version_regex is required.

        Returns:
            str: Extracted version string.

        """
        if x and cls.version_regex:
            match = None
            regexes = (
                cls.version_regex
                if isinstance(cls.version_regex, list)
                else [cls.version_regex])
            for regex in regexes:
                match = re.search(regex, x)
                if match is not None:
                    return match.group('version')
            if require_match:
                return ''
            warnings.warn(
                f"Could not locate version in string: {x} with "
                f"regex {cls.version_regex}")
        if x and require_match:
            # raise Exception(f"{cls}: {cls.tooltype.title()} "
            #                 f"{cls.toolname} does not have a "
            #                 f"version regex")
            return ''
        return x

    @staticmethod
    def tool_version_static(cls, executable=None, skip_regex=False,
                            **kwargs):
        r"""Get the version of the compilation tool using only static
        class properties.

        Args:
            executable (str, optional): Executable that should be used
                with the version flags for this class. If not provided
                the default executable will be used if it is set and
                toolname will be used if it is not set.
            skip_regex (bool, optional): If True, don't call
                extract_tool_version and return the raw version result.
            **kwargs: Additional keyword arguments are pased to
                extract_tool_version.

        Returns:
            str: Version string associated with the provided executable.

        """
        if executable is None:
            executable = (
                cls.default_executable
                if cls.default_executable else cls.toolname)
        try:
            out = subprocess.check_output(
                [executable] + cls.version_flags,
                stderr=subprocess.STDOUT).decode('utf-8').strip()
        except (subprocess.CalledProcessError, OSError):
            out = ''
        if skip_regex:
            return out
        return CompilationToolBase.extract_tool_version(cls, out, **kwargs)

    @classmethod
    def tool_version(cls, skip_regex=False, **kwargs):
        r"""Get the version of the compilation tool.

        Args:
            skip_regex (bool, optional): If True, don't call
                extract_tool_version and return the raw version result.
            **kwargs: Additional keyword arguments are passed to call.

        Returns:
            str: Version.

        """
        kwargs.setdefault('cache_key', True)
        out = cls.call(cls.version_flags, for_version=True, **kwargs)[0]
        if skip_regex:
            return out
        return CompilationToolBase.extract_tool_version(cls, out)

    @classmethod
    def run_executable_command(cls, args, skip_flags=False,
                               dry_run=False, out=None, overwrite=False,
                               products=None, allow_error=False,
                               working_dir=None, cache_key=None,
                               for_version=False, verbose=None, **kwargs):
        r"""Run a command using this tool.

        Args:
            args (list): The arguments that should be passed to the tool.
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
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products produced by the compilation
                should be appended to. Defaults to None and is ignored.
            allow_error (bool, optional): If True and there is an error when
                call the executable, it will be ignored. If False, errors will
                result in an exception being raised. Defaults to False.
            working_dir (str, optional): Working directory where tool should be
                called from. This will also be used to construct the path for
                the output file. Defaults to None and is ignored.
            cache_key (str, optional): Key that should be used to
                cache results so that they may be used multiple
                times. Defaults to None and is ignored.
            for_version (bool, optional): If True, the call is used to
                determine the tool version and version info shouldn't
                be included in log messages.
            verbose (bool, optional): If True, the call command and
                and output will be logged as info.
            **kwargs: Additional keyword arguments are passed to
                cls.get_executable_command. and tools.popen_nobuffer.

        Returns:
            str: Output to stdout from the command execution if skip_flags is
                True, produced file otherwise.

        Raises:
            RuntimeError: If there is an error when running the command and
                allow_error is False.
        
        """
        out_product = None
        unused_kwargs = kwargs.pop('unused_kwargs', {})
        # Add product and check for file
        if not (skip_flags or cls.no_output_file):
            if products is None:
                products = tools.IntegrationPathSet(overwrite=overwrite)
            if out != 'clean':
                if working_dir is not None and not os.path.isabs(out):
                    out = os.path.join(working_dir, out)
                assert out not in args  # Don't remove source files
                out_product = cls.append_product(
                    products, out, sources=args, overwrite=overwrite,
                    dry_run=dry_run, **kwargs)
                if not dry_run:
                    out_product.setup()
                    if out_product.exists:
                        logger.debug(f"Output already exists: {out}")
                        return out
            kwargs['outfile'] = out
        cmd = cls.get_executable_command(args, skip_flags=skip_flags,
                                         unused_kwargs=unused_kwargs,
                                         cwd=working_dir, **kwargs)
        if cache_key is not None:
            if cache_key is True:
                cache_key = ' '.join(cmd)
            if cache_key in cls._language_cache:
                return cls._language_cache[cache_key]
        # Return if dry run
        if dry_run:
            if skip_flags:
                return ''
            else:
                return out
        # Run command
        
        def format_out(name, x, indent=2, wrap=100, tab='  ',
                       hanging_indent=False, dont_wrap=False):
            if not isinstance(x, str):
                x = pprint.pformat(x)
            lines = x.splitlines()
            if not dont_wrap:
                for i in range(len(lines) - 1, -1, -1):
                    j = i
                    while len(lines[j]) > wrap:
                        rem = lines[j][wrap:]
                        if hanging_indent:
                            rem = tab + rem
                        lines[j] = lines[j][:wrap]
                        j += 1
                        lines.insert(j, rem)
            if len(lines) == 1:
                x = lines[0]
            else:
                sep = '\n' + (indent * tab)
                x = sep + sep.join(lines)
            return f'\n  {name:<11}: {x}'
        
        output = ''
        try:
            if (not skip_flags) and ('env' not in unused_kwargs):
                unused_kwargs['env'] = cls.set_env()
            message_before = (
                format_out('Working Dir', working_dir)
                + format_out('Command', f"\"{' '.join(cmd)}\""))
            if not for_version:
                try:
                    message_before = (
                        format_out('Version', cls.tool_version())
                        + message_before)
                except BaseException:  # pragma: debug
                    pass
            if verbose:
                logger.info(message_before)
            else:
                logger.debug(message_before)
            proc = tools.popen_nobuffer(cmd, **unused_kwargs)
            output, err = proc.communicate()
            output = tools.safe_decode(output)
            err = tools.safe_decode(err)
            env_diff = tools.dict_diff(unused_kwargs.get('env', {}),
                                       os.environ)
            message = (message_before
                       + format_out('Return Code', proc.returncode)
                       + format_out('Env Changes', env_diff)
                       + format_out('Output', output))
            if err:
                message += format_out('Error', err)
            if (proc.returncode != 0) and (not allow_error):
                raise RuntimeError(message)
            if cls.no_output_file:
                out = output
            try:
                if verbose:
                    logger.info(message)
                else:
                    logger.debug(message)
            except UnicodeDecodeError:  # pragma: debug
                tools.print_encoded(message)
        except (subprocess.CalledProcessError, OSError) as e:
            if not allow_error:
                raise RuntimeError(f"Could not call command "
                                   f"'{' '.join(cmd)}': {e}")
        except BaseException as e:
            try:
                logger.error(f"Unexpected call error {type(e)}: {e}")
            except UnicodeDecodeError:  # pragma: debug
                tools.print_encoded(e)
            raise
        # Check for output
        if not (skip_flags or cls.no_output_file):
            if (out != 'clean'):
                if not out_product.exists:  # pragma: debug
                    logger.error(f"{' '.join(cmd)}\n{output}")
                    raise RuntimeError(
                        f"{cls.tooltype.title()} tool, {cls.toolname}"
                        f", failed to produce result \'{out}\'")
                logger.debug(
                    f"{cls.tooltype.title()} {cls.toolname} produced "
                    f"{out}")
            return out
        if cache_key:
            cls._language_cache[cache_key] = output
        return output

    @classmethod
    def call(cls, args, language=None, toolname=None, libtype=None,
             skip_flags=False, out=None, suffix='', cache_key=None,
             for_version=False, force_simultaneous_next_stage=False,
             **kwargs):
        r"""Call the tool with the provided arguments. If the first
        argument resembles the name of the tool executable, the
        executable will not be added.

        Args:
            args (list): The arguments that should be passed to the tool.
            language (str, optional): Language of tool that should be
                used. If different than the languages supported by the
                current tool, the correct tool is used instead. Defaults
                to None and is ignored.
            toolname (str, optional): Name of compilation tool that
                should be used. Defaults to None and the default tool
                for the language will be used.
            libtype (str, optional): Type of file that flags should
                produce.
            skip_flags (bool, optional): If True, args is assumed to
                include any necessary flags. If False, args are assumed
                to the files that the tool is called on and flags are
                determined from them. Defaults to False.
            out (str, optional): Full path to output file that should be
                created following this stage and any subsequent stages of
                the build. If None, the path will be determined from the
                path to the first argument provided. Defaults to None.
                This keyword argument will be ignored if skip_flags is
                True.
            suffix (str, optional): Suffix that should be added to the
                output file (before the extension). Defaults to "".
            cache_key (str, optional): Key that should be used to
                cache results so that they may be used multiple
                times. Defaults to None and is ignored.
            for_version (bool, optional): If True, the call is used to
                determine the tool version and version info shouldn't
                be included in log messages.
            force_simultaneous_next_stage (bool, optional): If True,
                force the next stage to be performed by the same command
                as this one.
            **kwargs: Additional keyword arguments are passed to
                cls.get_executable_command. and tools.popen_nobuffer.

        Returns:
            str: Output to stdout from the command execution if
                skip_flags is True, produced file otherwise.

        """
        # Call from another tool if the language dosn't match
        toolname = kwargs.pop(cls.tooltype, toolname)
        language = kwargs.pop(f'{cls.tooltype}_language', language)
        unused_kwargs = kwargs.pop('unused_kwargs', {})
        cls = cls.get_alternate_class(toolname=toolname,
                                      language=language)
        if libtype is None:
            libtype = cls.get_default_libtype(
                no_additional_stages=True)
        if isinstance(args, (str, bytes)):
            args = [args] if args else []
        assert isinstance(args, list)
        if for_version:
            skip_flags = True
            cache_key = True
            kwargs.update(allow_error=True)
        # Get output file
        origin = kwargs.pop('origin', 'user')
        if not (skip_flags or cls.no_output_file or out):
            kws = dict(kwargs)
            if suffix is not None:
                kws['suffix'] = suffix
            if 'working_dir' in kws:
                kws['directory'] = kws.pop('working_dir')
            dep = CompilationDependency.create_target(
                None, source=args, language=cls.languages[0],
                origin=origin, basetool=cls, libtype=libtype, **kws)
            out = dep['output']
        # Run command
        if not isinstance(out, list):
            out = [out]
        if len(out) == 1:
            args = [args]
        else:
            assert len(args) == len(out)
            args = [[x] for x in args]
        output = []
        if skip_flags:
            for k in cls.local_kws:
                kwargs.pop(k, None)
        else:
            kwargs.update(
                force_simultaneous_next_stage=force_simultaneous_next_stage,
                libtype=libtype)
        for isrc, iout in zip(args, out):
            output.append(cls.run_executable_command(
                isrc, out=iout, skip_flags=skip_flags,
                cache_key=cache_key, for_version=for_version,
                unused_kwargs=unused_kwargs, **kwargs))
        return output


class CompilerBase(CompilationToolBase):
    r"""Base class for compilers.

    Args:
        linker (str, optional): Name of the linker that should be used for
            linking compiled objects. Defaults to None if not provided and
            default_linker will be used.
        archiver (str, optional): Name of the archiver that should be used
            for combining compiled objects into a static library.
            Defaults to None if not provided and default_archiver will be
            used.
        linker_flags (list, optional): Flags that should be used when
            linking compiled objects. Defaults to default_linker_flags if
            not provided.
        archiver_flags (list, optional): Flags that should be used for
            combining compiled objects into a static library. Defaults to
            default_archiver_flags if not provided.

    Class Attributes:
        source_dummy (str): Code that should be used to generate a dummy
            shared library using this compiler that can be used to
            located linked shared/dynamic libraries.

    """
    tooltype = 'compiler'
    associated_tooltypes = ['linker', 'archiver']  # , 'disassembler']
    builtin_next_stage = 'linker'  # Most compiler's also link
    no_additional_stages_flag = '-c'
    input_filetypes = ['source']
    output_filetypes = [
        'object',
    ]
    source_exts = []
    include_exts = []
    flag_options = OrderedDict([('definitions', '-D%s'),
                                ('include_dirs', '-I%s')])
    search_path_env = ['include']
    source_dummy = ''
    standard_library_type = 'shared'
    default_libtype = 'object'
    libtype_ext = {'object': '.o'}
    libtype_next_stage = {'executable': 'linker',
                          'shared': 'linker',
                          'windows_import': 'linker',
                          'static': 'archiver'}

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilationToolBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            if not cls.is_gnu:
                cls.libtype_ext = dict(cls.libtype_ext, object='.obj')
            cls.search_path_env.append(os.path.join('library', 'include'))

    @classmethod
    def linker(cls, force_simultaneous_link=False, **kwargs):
        r"""Get the associated linker class.

        Args:
            force_simultaneous_link (bool, optional): If True, the
                returned linker will allow simultaneous linking.
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            CompilationToolBase: Linker class associated with this compiler.

        """
        kwargs.setdefault('force_simultaneous_next_stage',
                          force_simultaneous_link)
        assert (kwargs['force_simultaneous_next_stage']
                == force_simultaneous_link)
        return cls.get_tool('linker', **kwargs)

    @classmethod
    def archiver(cls, **kwargs):
        r"""Get the associated archiver class.

        Args:
            **kwargs: Additional keyword arguments are passed to
                get_tool.

        Returns:
            ArchiverToolBase: Archiver class associated with this compiler.

        """
        return cls.get_tool('archiver', **kwargs)

    @classmethod
    def find_component(cls, component, component_types=None,
                       flags=[], cfg=None, regex=None, **kwargs):
        r"""Locate components in a compiled test library that match.

        Args:
            component (str): Name of component to search for.
            component_types ((str, list, optional): Type of component(s)
                that should be searched for.
            flags (list, optional): Flags to add to the test compilation.
            regex (str, optional): Regular expression that should be used
                to locate the component in the output from the
                disassembler.
            **kwargs: Additional keyword arguments are passed to
                CompilationToolBase.call.

        Returns:
            list: Matching components.

        """
        products = tools.IntegrationPathSet(overwrite=True)
        ftest = os.path.join(
            os.getcwd(), f"a{cls.linker().libtype_ext['shared']}")
        ftest_src = os.path.join(
            os.getcwd(), f"a{cls.source_exts[0]}")
        assert not (os.path.isfile(ftest_src)
                    or os.path.isfile(ftest))
        products.append_generated(ftest_src, [cls.source_dummy])
        products.setup()
        try:
            cls.call([ftest_src], libtype='shared', out=ftest,
                     additional_args=flags, products=products,
                     include_dirs=cls.get_search_path(cfg=cfg),
                     force_simultaneous_next_stage=True, **kwargs)
            for lib in cls.disassembler().find_component(
                    ftest, component, component_types=component_types,
                    verbose=kwargs.get('verbose', False),
                    regex=regex):
                if ((not (os.path.isabs(lib)
                          and os.path.isfile(lib))
                     and cls.toolset in ['llvm', 'gnu'])):
                    lib = os.path.basename(lib)
                    lib_file = subprocess.check_output(
                        [cls.get_executable(),
                         f'-print-file-name={lib}']
                    ).decode('utf-8').strip()
                    if lib_file:
                        lib = lib_file
                if lib:
                    yield lib
        finally:
            products.teardown()

        
class LinkerBase(CompilationToolBase):
    r"""Base class for linkers.

    Attributes:
        library_name_key (str): Option key indicating the name of a library
            that should be linked against.
        library_directory_key (str): Option key indicating a directory that
            should be included in the linker search path for libraries.
        output_first_library (bool): If True, the output key (and its value) are
            put in front of the other flags when building a library. A value of
            None causes the output_first attribute to be used (unless explicitly
            set in the method call).

    """

    tooltype = 'linker'
    basetooltype = 'compiler'
    input_filetypes = ['object']
    output_filetypes = ['shared', 'windows_import', 'executable']
    flag_options = OrderedDict([
        ('library_libs', {
            'key': '-l%s',
            'allow_duplicate_values': True}),
        ('library_libs_nonstd', {
            'key': '-l:%s',
            'allow_duplicate_values': True}),
        ('library_dirs', '-L%s')])
    default_libtype = 'executable'
    library_libtype = 'shared'
    libtype_flags = {'shared': '-shared',
                     'windows_import': '-shared'}
    libtype_prefix = {'shared': '' if platform._is_win else 'lib',
                      'windows_import': ''}
    # TODO: keep .out extension for executables?
    libtype_ext = {'executable': '.exe' if platform._is_win else '',
                   'windows_import': '.lib'}  # depends on the OS
    output_first_library = None
    search_path_env = ['lib']
    all_library_ext = ['.so', '.a']
    preload_envvar = None
    local_kws = [
        'build_library', 'skip_library_libs', 'use_library_path',
        'libraries', 'library_dirs', 'library_libs',
        'library_libs_nonstd', 'library_flags',
        'additional_objs',
    ]

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilationToolBase.before_registration(cls)
        if platform._is_win:  # pragma: windows
            # TODO: Use 'cyg' prefix on cygwin?
            cls.libtype_ext['shared'] = '.dll'
            cls.search_path_env += [
                'DLLs', os.path.join('library', 'bin'), 'Library']
            cls.all_library_ext = ['.dll', '.lib', '.dll.a']
        elif platform._is_mac:
            cls.libtype_ext['shared'] = '.dylib'
        else:
            cls.libtype_ext['shared'] = '.so'
        if cls.is_gnu:
            cls.libtype_ext = dict(cls.libtype_ext,
                                   windows_import='.dll.a')
            # cls.libtype_prefix = dict(cls.libtype_prefix,
            #                           windows_import='lib')
            cls.libtype_ext['windows_import'] = '.dll.a'
        if cls.libtype_ext['shared'] not in cls.all_library_ext:
            cls.all_library_ext = (
                cls.all_library_ext + [cls.libtype_ext['shared']])

    @classmethod
    def is_standard_libname(cls, libname):
        r"""Determine if the provided file name conforms to the standards
        expected by this linker.

        Args:
            libname (str): Library file name to check.

        Returns:
            bool: True if the name conforms, False otherwise.

        """
        if cls.toolset == 'msvc':  # pragma: windows
            return False  # Pass all libraries w/ ext
        return (
            libname.startswith(cls.libtype_prefix[cls.library_libtype])
            and (libname.endswith(tuple(cls.all_library_ext))
                 or DependencyRegistry.splitext(libname)[-1].startswith(
                     tuple(cls.all_library_ext))))

    @classmethod
    def libpath2libname(cls, libpath):
        r"""Determine the library name from the library path.

        Args:
            libpath (str): Full or partial path to library.
        
        Returns:
            str: Library name.

        """
        out = cls.file2base(libpath)
        if cls.libtype_prefix[cls.library_libtype]:
            out = out.split(cls.libtype_prefix[cls.library_libtype], 1)[-1]
        return out

    @classmethod
    def get_flags(cls, libtype=None, skip_library_libs=False,
                  use_library_path=False, additional_objs=None, **kwargs):
        r"""Get a list of linker flags.

        Args:
            libtype (str, optional): Type of file that flags should
                produce.
            libraries (list, optional): Full paths to libraries that should be
                linked against. Defaults to an empty list.
            library_dirs (list, optional): Directories that should be searched
                for libraries. Defaults to an empty list.
            library_libs (list, optional): Names of libraries that should be
                linked against. Defaults to an empty list.
            library_libs_nonstd (list, optional): Names of libraries
                w/ non-standard naming conventions that should be linked
                against. Defaults to an empty list.
            library_flags (list, optional): Existing list that library flags
                should be appended to instead of the returned flags if
                skip_library_libs is True. Defaults to [].
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
            additional_objs (list, optional): Additional compiled object
                files that should be part of the resulting library.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            list: Linker flags.

        """
        build_library = (libtype in ['shared', 'windows_import'])
        # Add output_first keyword argument for libraries
        if build_library:
            kwargs.setdefault('output_first', cls.output_first_library)
        # Copy/Pop so that empty default dosn't get appended to and then
        # call the parent class's method
        libraries = kwargs.pop('libraries', [])
        library_dirs = kwargs.pop('library_dirs', [])
        library_libs = kwargs.pop('library_libs', [])
        library_libs_nonstd = kwargs.pop('library_libs_nonstd', [])
        library_rpath = kwargs.pop('library_rpath', [])
        library_flags = kwargs.pop('library_flags', [])
        flags = copy.deepcopy(kwargs.pop('flags', []))
        if kwargs.get('cwd', None):
            library_dirs = [
                x if os.path.isabs(x) else os.path.join(kwargs['cwd'], x)
                for x in library_dirs]
            libraries = [
                x if os.path.isabs(x) else os.path.join(kwargs['cwd'], x)
                for x in libraries]
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
                if x_d and (x_d not in library_dirs):
                    library_dirs.append(x_d)
                if cls.is_standard_libname(x_f):
                    library_libs.append(cls.libpath2libname(x_f))
                else:
                    library_libs_nonstd.append(x_f)
                if (((cls.tooltype == 'linker')
                     and x_f.endswith(cls.libtype_ext['shared'])
                     and ('library_rpath' in cls.flag_options))):
                    if x_d and x_d not in library_rpath:
                        library_rpath.append(x_d)
        # Add libraries to library_flags instead of flags so they can be
        # used elsewhere
        if skip_library_libs:
            if library_libs:
                cls.append_flags(library_flags,
                                 cls.flag_options['library_libs'],
                                 library_libs)
                library_libs = []
            if library_libs_nonstd:
                cls.append_flags(library_flags,
                                 cls.flag_options['library_libs_nonstd'],
                                 library_libs_nonstd)
                library_libs_nonstd = []
        # Call parent class
        kwargs['libtype'] = libtype
        if library_dirs:
            kwargs['library_dirs'] = library_dirs
        if library_libs:
            kwargs['library_libs'] = library_libs
        if library_libs_nonstd:
            kwargs['library_libs_nonstd'] = library_libs_nonstd
        if library_rpath:
            kwargs['library_rpath'] = library_rpath
        if additional_objs:
            kwargs.setdefault('additional_args', [])
            kwargs['additional_args'] = kwargs['additional_args'] + additional_objs
        return super(LinkerBase, cls).get_flags(flags=flags, **kwargs)

    @classmethod
    def preload_env(cls, libs, env):
        r"""Get environment variables necessary to preload libraries.

        Args:
            libs (list): One or more libaries to preload.
            env (dict): Dictionary to add environment variables to.

        Returns:
            dict: Environment variable options.

        """
        if isinstance(libs, str):
            libs = [libs]
        if cls.preload_envvar and libs:
            if cls.preload_envvar in env:  # pragma: no cover
                libs = [env[cls.preload_envvar]] + libs
            env[cls.preload_envvar] = ';'.join(libs)
            logger.debug(f"PRELOAD ENV ({cls.preload_envvar}): "
                         f"{env[cls.preload_envvar]}")
            # preload_file = '/etc/ld.so.preload'
            # if os.path.isfile(preload_file):
            #     contents = open(preload_file, 'r').read()
            #     logger.debug(f"PRELOAD FILE ({preload_file}):\n"
            #                  f"{contents}")
        return env


class ArchiverBase(CompilationToolBase):
    r"""Base class for archivers.

    Attributes:
        library_name_key (str): Option key indicating the name of a library
            that should be linked against.
        library_directory_key (str): Option key indicating a directory that
            should be included in the linker search path for libraries.

    """

    tooltype = 'archiver'
    basetooltype = 'compiler'
    input_filetypes = ['object']
    output_filetypes = ['static']
    flag_options = OrderedDict()
    default_libtype = 'static'
    library_libtype = 'static'
    libtype_flags = {'static': '-static'}
    libtype_prefix = {'static': '' if platform._is_win else 'lib'}
    libtype_ext = {'static': '.lib' if platform._is_win else '.a'}
    search_path_env = ([os.path.join('library', 'lib'), 'Library']
                       if platform._is_win else ['lib'])

    @classmethod
    def get_flags(cls, additional_objs=None, **kwargs):
        r"""Get a list of flags for this archiver tool.

        Args:
            additional_objs (list, optional): Additional compiled object
                files that should be part of the resulting library.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            list: Archiver flags.

        """
        if additional_objs:
            kwargs.setdefault('additional_args', [])
            kwargs['additional_args'] = (
                kwargs['additional_args'] + additional_objs)
        return super(ArchiverBase, cls).get_flags(**kwargs)


class DisassemblerBase(CompilationToolBase):
    r"""Base class for binary inspection tools."""
    tooltype = 'disassembler'
    languages = ['c', 'c++', 'fortran']
    component_options = {}
    no_output_file = True

    @classmethod
    def find_component(cls, fname, component, component_types=None,
                       regex=None, **kwargs):
        r"""Locate components in a binary file that match.

        Args:
            fname (str): Full path to the file containing the binary to
                search.
            component (str): Name of component to search for.
            component_types ((str, list, optional): Type of component(s)
                that should be searched for.
            regex (str, optional): Regular expression that should be used
                to locate the component in the output from the
                disassembler.
            **kwargs: Additional keyword arguments are passed to
                CompilationToolBase.call.

        Returns:
            list: Matching components.

        """
        if regex is None:
            regex = re.compile(
                CompilationDependency._search_regex(component, ''))
        elif isinstance(regex, str):
            regex = re.compile(regex)
        result = cls.call([fname], components=component_types, **kwargs)
        out = [x[0].strip() for x in regex.findall(result[0])]
        # TODO: temp
        print("FIND_COMPONENT", regex, out)
        return out

    @classmethod
    def call(cls, args, components=None, **kwargs):
        r"""Call the tool with the provided arguments.

        Args:
            args (list): The arguments that should be passed to the tool.
            components (str, list, optional): Type of component(s) that
                should be selected.
            **kwargs: Additional keyword arguments are passed to
                CompilationToolBase.call.
        
        """
        flags = []
        filters = []
        if isinstance(components, str):
            components = [components]
        if components is not None:
            for x in components:
                if cls.component_options[x]:
                    flags += cls.component_options[x].get('flags', [])
                    filters += cls.component_options[x].get('filters', [])
        out = super(DisassemblerBase, cls).call(flags + args, **kwargs)
        if filters:
            out = out[0]
            lines = out.splitlines()
            lines_filtered = []
            for x in lines:
                if any(xf in x for xf in filters):
                    lines_filtered.append(x)
            out = ['\n'.join(lines_filtered)]
        return out


# class LDDDisassembler(DisassemblerBase):
#     r"""Class for ldd inspection"""
#     toolname = 'ldd'
#     toolset = 'gnu'
#     component_options = {
#         'shared_libraries': {}
#     }


class OToolDisassembler(DisassemblerBase):
    r"""Class for otool inspection"""
    toolname = 'otool'
    toolset = 'llvm'
    component_options = {
        'shared_libraries': {
            'flags': ['-L']},
    }
    version_regex = r'disassmbler: (?P<version>.+? version \d+\.\d+\.\d+)'

    
class ObjDumpDisassembler(DisassemblerBase):
    r"""Class for objdump inspection"""
    toolname = 'objdump'
    toolset = 'gnu'
    compatible_toolsets = ['llvm', 'msvc']
    component_options = {
        'shared_libraries': {
            'flags': ['-p'],
            # 'filters': ['NEEDED'],
        },
    }


class DumpBinDisassembler(DisassemblerBase):
    r"""Class for dumpbin inspector"""
    toolname = 'dumpbin'
    toolset = 'msvc'
    component_options = {
        'shared_libraries': {
            'flags': ['/dependents']},
        'imported_libraries': {
            'flags': ['/all'],
            'filters': ['DLL name']},
    }
    version_regex = [
        r'Microsoft \(R\) COFF\/PE Dumper Version \d+\.\d+\.\d+\.\d+']


class BuilderBase(CompilationToolBase):
    r"""Base class for build tools.

    Args:
        buildfile (str, optional): File containing information about the build.
            Defaults to default_buildfile class attribute, if set.
        builddir (str, optional): Directory where build files should be placed.
            Defaults to directory where build is called.
        sourcedir (str, optional): Directory where source files are stored.
            Defaults to directory where build is called.
        target (str, optional): Build target. If not provided, build will be
            created without a target.

    """
    tooltype = 'builder'
    input_filetypes = ['target']
    output_filetypes = ['build']
    default_buildfile = None
    default_libtype = 'build'
    separate_configure = False
    is_build_tool = True
    build_language = None
    _schema_properties = {
        'buildfile': {'type': 'string'},
        'builddir': {'type': 'string'},
        'sourcedir': {'type': 'string'},
        'target': {'type': 'string'}}
    compatible_toolsets = _all_toolsets
    compatible_languages = ['c', 'c++', 'fortran']

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        CompilationToolBase.before_registration(cls)
        if cls.build_language is None:
            cls.build_language = cls.toolname

    @classmethod
    def get_language_ext(cls, languages=None):
        r"""Get the extensions associated with the language that this tool can
        handle.

        Returns:
            list: Language file extensions.

        """
        if languages is None:
            languages = cls.compatible_languages
        return super(BuilderBase, cls).get_language_ext(
            languages=languages)

    @classmethod
    def append_product(cls, products, new, sources=None,
                       exclude_sources=False, **kwargs):
        r"""Append a product to the specified list along with additional
        values indicated by cls.product_exts.

        Args:
            products (tools.IntegrationPathSet, optional): Existing set
                that additional products produced by the compilation
                should be appended to.
            new (str): New product that should be appended to the list.
            sources (list, optional): Source files associated with the
                new product.
            exclude_sources (bool, optional): If True, the sources will
                be excluded from the removable files.
            **kwargs: Additional keyword arguments are passed to
                IntegrationPathSet.append_compilation_product

        """
        out = super(BuilderBase, cls).append_product(
            products, new, **kwargs)
        builddir = kwargs.get('builddir', os.path.dirname(new))
        if not os.path.isfile(builddir):
            products.append(builddir, cls=tools.GeneratedDirectory,
                            move_existing=True)
        return out


class ConfigurerBase(BuilderBase):
    r"""Base class for configuration tools."""

    tooltype = 'configurer'
    default_libtype = 'builddir'
    input_filetypes = ['buildfile']
    output_filetypes = ['configfile']
    associated_tooltypes = ['builder']
    libtype_next_stage = {'build': 'builder'}
    default_configfile = None
    build_params = []


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
        args (str or list): The model executable and any arguments that
            should be passed to the model executable.
        source_files (list, optional): Source files that should be
            compiled into an executable. Defaults to an empty list and
            the driver will search for a source file based on the model
            executable (the first model argument).
        disable_python_c_api (bool, optional): If True, the Python C API
            will be disabled. Defaults to False.
        with_asan (bool, optional): If True, the model will be compiled
            and linked with the address sanitizer enabled (if there is
            one available for the selected compiler).
        with_omp (bool, optional): If True, the model will be compiled
            and linked with OpenMP if OpenMP is installed and can be
            located.
        compile_working_dir (str, optional): Directory where compilation
            should be invoked from if it is not the same as the provided
            working_dir.
        **kwargs: Additional keyword arguments are passed to parent class

    Class Attributes:
        allow_parallel_build (bool): If True, a file can be compiled by
            two processes simultaneously. If False, it cannot and an
            MPI barrier will be used to prevent simultaneous compilation.
            Defaults to False.

    Attributes:
        source_files (list): Source files.
        compiler (str): Name or path to the compiler that should be used.
        compiler_flags (list): Compiler flags.
        linker (str): Name or path to the linker that should be used.
        linker_flags (list): Linker flags.
        archiver (str): Name or path to the archiver that should be used.
        archiver_flags (list): Archiver flags.
        disassembler (str): Name or path to the disassembler that should
            be used.
        disassembler_flags (list): Disassembler flags.
        configurer (str): Name or path to the configurer that should be
            used.
        configurer_flags (list): Configurer flags.
        builder (str): Name or path to the builder that should be used.
        builder_flags (list): Builder flags.
        compiler_tool (CompilerBase): Compiler tool that will be used.
        linker_tool (LinkerBase): Linker tool that will be used.
        archiver_tool (ArchiverBase): Archiver tool that will be used.
        disassembler_tool (DisassemblerBase): Disassembler tool that will
            be used.
        configurer_tool (ConfigurerBase): Configurer tool that will be
            used.
        builder_tool (BuilderBase): Builder tool that will be used.

    """

    _schema_properties = {
        'compile_working_dir': {'type': 'string'},
        'source_files': {'type': 'array', 'items': {'type': 'string'},
                         'default': []},
        'disable_python_c_api': {'type': 'boolean', 'default': False},
        'with_asan': {'type': 'boolean', 'default': False},
        'with_omp': {'type': 'boolean', 'default': False}}
    executable_type = 'compiler'
    is_build_tool = False
    allow_parallel_build = False
    libraries = None
    standard_libraries = {}
    external_libraries = {}
    internal_libraries = {}
    basetool = 'compiler'
    default_model_libtype = 'executable'
    tooltypes = []
    optional_tooltypes = ['disassembler']

    def __init__(self, name, args, skip_compile=False, **kwargs):
        self.model_dep = None
        self.skip_compile = skip_compile
        super(CompiledModelDriver, self).__init__(name, args, **kwargs)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        global _tool_registry
        if not cls.tooltypes:
            cls.tooltypes = _tool_registry.tooltypes(cls.basetool)
            cls._config_keys = cls.tooltypes
            cls._config_attr_map = [{'attr': f'default_{k}', 'key': k}
                                    for k in cls.tooltypes]
            cls._config_attr_map += [{'attr': f'default_{k}_flags',
                                      'key': f'{k}_flags', 'type': list}
                                     for k in cls.tooltypes]
        cls._schema_properties = copy.deepcopy(cls._schema_properties)
        for k in cls.tooltypes:
            if not hasattr(cls, k):
                setattr(cls, f'default_{k}', None)
            if not hasattr(cls, f'default_{k}_flags'):
                setattr(cls, f'default_{k}_flags', None)
            cls._schema_properties[k] = {
                'type': 'string',
                'description': (f'Name of {k} that should be used to '
                                f'build the model')
            }
            cls._schema_properties[f'{k}_flags'] = {
                'type': 'array', 'items': {'type': 'string'},
                'default': [],
                'description': (f'Flags that should be passed to the {k}'
                                f'when building the model')
            }
        for k in _tool_registry.invalid_tooltypes(cls.basetool):
            for kk in [k, f'{k}_flags']:
                if kk in cls._schema_properties:
                    del cls._schema_properties[kk]
        ModelDriver.before_registration(cls)
        
    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        global _tool_registry
        ModelDriver.after_registration(cls, **kwargs)
        for k in cls.tooltypes:
            # Set default linker/archiver based on compiler
            default_tool_name = getattr(cls, f'default_{k}', None)
            if default_tool_name:
                default_tool = _tool_registry.tool(k, default_tool_name,
                                                   None)
                if (((default_tool is None)
                     or (not default_tool.is_installed()))):  # pragma: debug
                    if not tools.is_subprocess():
                        logger.debug(f'Default {k} for {cls.language} '
                                     f'({default_tool_name}) is not '
                                     f'installed. Attempting to locate '
                                     f'an alternative .')
                    setattr(cls, f'default_{k}', None)
        if not kwargs.get('second_pass', False):
            cls.libraries = DependencyRegistry(
                cls.language,
                internal=cls.internal_libraries,
                external=cls.external_libraries,
                standard=cls.standard_libraries,
                cfg=cls.cfg, driver=cls, in_driver_registration=True)

    def parse_arguments(self, args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        if self.compile_working_dir is None:
            self.compile_working_dir = self.working_dir
        elif not os.path.isabs(self.compile_working_dir):
            self.compile_working_dir = os.path.join(
                self.working_dir, self.compile_working_dir)
        # Set defaults from attributes
        for k0 in self.tooltypes:
            for k in [k0, f'{k0}_flags']:
                v = getattr(self, k, None)
                if v is None:
                    setattr(self, k, getattr(self, f'default_{k}'))
        # Set tools so that they are cached
        for k in self.tooltypes:
            setattr(self, f'{k}_tool', self.get_tool_instance(k))
        # Ensure source files are absolute paths
        source_files = []
        for src in self.source_files:
            if not os.path.isabs(src):
                src = os.path.normpath(os.path.join(self.working_dir, src))
            source_files.append(src)
        self.source_files = source_files
        super(CompiledModelDriver, self).parse_arguments(args, **kwargs)
        # Handle case where provided argument is source and not executable
        # and case where provided argument is executable, but source files are
        # not specified
        model_ext = os.path.splitext(self.model_file)[-1]
        model_is_source = self.is_source_file(self.model_file)
        if model_is_source:
            self.model_src = self.model_file
            self.model_file = None
            try:
                idx = self.source_files.index(self.model_function_file)
                self.source_files[idx] = self.model_src
            except ValueError:
                pass
            if not self.source_files:
                self.source_files.append(self.model_src)
        else:
            if len(model_ext) == 0:
                if not self.is_build_tool:
                    self.model_file += LinkerBase.libtype_ext['executable']
            else:
                # Assert that model file is not source code in any of the
                # registered languages
                if (((model_ext in constants.ALL_LANGUAGE_EXTS)
                     and (model_ext != '.exe'))):  # pragma: debug
                    from yggdrasil.components import import_component
                    from yggdrasil.schema import get_schema
                    s = get_schema()['model']
                    for v_name in s.classes:
                        v = import_component('model', v_name)
                        if (((v.language_ext is not None)
                             and (model_ext in v.language_ext))):
                            raise RuntimeError(
                                f"Extension '{model_ext}' indicates that "
                                f"the model language is '{v.language}', "
                                f"not '{self.language}' as specified.")
            if (len(self.source_files) == 0) and (self.language_ext is not None):
                # Add source file based on the model file
                # model_is_source = True
                self.model_src = (os.path.splitext(self.model_file)[0]
                                  + self.language_ext[0])
                self.source_files.append(self.model_src)
        # Add intermediate files and executable by doing a dry run
        self.init_model_dep()  # Required by make and cmake
        out = self.build_model(products=self.products, dry_run=True)
        if model_is_source:
            self.debug(f"Determined model file: {out[0]} "
                       f"({self.model_dep['libtype']})")
            self.model_file = out[0]
        self.debug(f"source_files: {self.source_files}")
        self.debug(f"model_file: {self.model_file}")

    def init_model(self):
        r"""Initialize the model executable."""
        super(CompiledModelDriver, self).init_model()
        # Compile
        if not self.skip_compile:
            self.build_model(products=self.products)
            self.debug(f"Built {self.model_file}")
        
    def init_model_dep(self, **kwargs):
        r"""Set the language of the target being compiled (usually the same
        as the language associated with this driver.

        Returns:
            str: Name of language.

        """
        if self.model_dep is None:
            self.model_dep = self.create_model_dep(**kwargs)
        return self.language

    @classmethod
    def identify_source_files(cls, args=None, working_dir=None,
                              source_files=None, **kwargs):
        r"""Determine the source file based on model arguments.

        Args:
            args (list, optional): Arguments provided.
            working_dir (str, optional): Working directory.
            source_files (list, optional): Source files in the model.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Source files.

        """
        out = []
        if isinstance(source_files, list):
            for src in source_files:
                if working_dir and (not os.path.isabs(src)):
                    src = os.path.normpath(os.path.join(working_dir, src))
                if os.path.isfile(src):
                    out.append(src)
        if not out:
            out = super(CompiledModelDriver, cls).identify_source_files(
                args=args, working_dir=working_dir,
                source_files=source_files, **kwargs)
        return out
        
    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            list: Full paths to any created wrappers.

        """
        out = super(CompiledModelDriver, self).write_wrappers(**kwargs)
        kwargs.setdefault('logging_level', self.numeric_logging_level)
        for k in self._schema_properties.keys():
            kwargs.setdefault(k, getattr(self, k, None))
        out += self.get_tool_instance('basetool').write_wrappers(**kwargs)
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
        global _tool_registry
        if tooltype == 'basetool':
            tooltype = cls.basetool
        reg = _tool_registry.language[tooltype].get(cls.language,
                                                    OrderedDict())
        return copy.deepcopy(reg)

    @staticmethod
    def get_tool_static(cls, tooltype, toolname=None, return_prop='tool',
                        default=tools.InvalidDefault(), language=None):
        r"""Get the class associated with the specified compilation tool
        for this language.

        Args:
            cls (class, instance): Compiled driver class or instance of
                compiled driver class to get tool for.
            tooltype (str): Type of compilation tool that should be
                returned.
            toolname (str, optional): Name of the tool that should be
                returned. Defaults to None and the tool name associated
                with the provided class/instance will be used.
            return_prop (str, optional): Value that should be returned.
                If 'tool', the tool is returned. If 'name', the tool
                name is returned. If 'flags', the tool flags are
                returned. Defaults to 'tool'.
            default (object, optiona): Tool that should be returned if
                one cannot be identified. If False, an error will be
                raised when a tool cannot be located.
            language (str, optional): Language of tools that should be
                returned. Defaults to None if not provided.

        Returns:
            CompilationToolBase: Class providing an interface to the
                specified compilation tool.

        Raises:
            NotImplementedError: If a tool is not specified.
            ValueError: If return_prop is not 'tool', 'name', or 'flags'.

        """
        global _tool_registry
        if return_prop == 'tool':
            return _tool_registry.tool_instance(
                tooltype, toolname=toolname, language=language,
                only_installed=True, driver=cls, default=default)
        elif return_prop == 'name':  # pragma: no cover
            return _tool_registry.tool_instance(
                tooltype, toolname=toolname, language=language,
                only_installed=True, driver=cls,
                default=default).toolname
        elif return_prop == 'flags':  # pragma: no cover
            return _tool_registry.tool_flags(
                tooltype, toolname=toolname, language=language,
                only_installed=True, driver=cls, default=default)
        else:
            raise ValueError(f"Invalid return_prop: '{return_prop}'")

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
    def create_dep(cls, driver=None, **kwargs):
        r"""Get a CompilationDependency instance associated with the
        driver.

        Args:
            driver (CompiledModelDriver, optional): Driver class that the
                created dependency will be associated with. If not
                provided, this class will be used.
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency.create_target

        Returns:
            CompilationDependency: New compilation target.

        """
        if driver is None:
            driver = cls
        kwargs.setdefault('commtype', tools.get_default_comm())
        return CompilationDependency.create_target(driver, **kwargs)

    def create_model_dep(self, attr_param=None, **kwargs):
        r"""Get a CompilationDependency instance associated with the
        model.

        Args:
            **kwargs: Additional keyword arguments are passed to
                CompilationDependency.create_target with defaults set
                based on the model's parameters.

        Returns:
            CompilationDependency: New compilation target for the model.

        """
        kwargs.setdefault('for_model', True)
        kwargs.setdefault('language', self.language)
        kwargs.setdefault('directory', self.working_dir)
        kwargs.setdefault('source', self.source_files)
        kwargs.setdefault('libtype', self.default_model_libtype)
        kwargs.setdefault('working_dir', self.compile_working_dir)
        if not os.path.isabs(kwargs['directory']):
            kwargs['directory'] = os.path.join(self.working_dir,
                                               kwargs['directory'])
        if kwargs.get('out', False):
            kwargs.setdefault('output', kwargs.pop('out'))
        elif self.model_file:
            kwargs.setdefault('output', self.model_file)
        if attr_param is None:
            attr_param = []
        for k in self.tooltypes:
            attr_param.append(f'{k}_flags')
            attr_param += CompilationDependency.tool_parameters_class(
                self.get_tool_instance(k))
        for k in attr_param:
            v = getattr(self, k, None)
            if v is not None:
                kwargs.setdefault(k, v)
        self.debug(f"Creating model dependency {pprint.pformat(kwargs)}")
        return self.create_dep(instance=self, **kwargs)
        
    @classmethod
    def language_executable(cls, toolname=None):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Args:
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        try:
            return cls.get_tool('basetool', toolname=toolname).get_executable()
        except InvalidCompilationTool as e:
            raise NotImplementedError(e)

    @classmethod
    def language_version(cls, toolname=None, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        basetool = cls.get_tool('basetool', toolname=toolname)
        return basetool.tool_version(**kwargs).splitlines()[0].strip()
        
    def run_model(self, **kwargs):
        r"""Run the model. Unless overridden, the model will be run using
        run_executable.

        Args:
            **kwargs: Keyword arguments are passed to run_executable.

        """
        kwargs.update(exec_type='direct')
        return super(CompiledModelDriver, self).run_model(**kwargs)
        
    @classmethod
    def executable_command(cls, args, exec_type='compiler', toolname=None,
                           **kwargs):
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
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.
            **kwargs: Additional keyword arguments are passed to either
                get_executable_command.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the compiler for this language.

        Raises:
            ValueError: If exec_type is not 'compiler', 'linker', or 'direct'.

        """
        try:
            if exec_type == 'direct':
                unused_kwargs = kwargs.pop('unused_kwargs', {})
                unused_kwargs.update(kwargs)
                return args
            elif exec_type == 'linker':
                exec_cls = cls.get_tool('linker', toolname=toolname)
            elif exec_type == 'compiler':
                exec_cls = cls.get_tool('compiler', toolname=toolname)
            else:
                raise ValueError("Invalid exec_type '%s'" % exec_type)
        except InvalidCompilationTool as e:
            raise NotImplementedError(e)
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
        dep = cls.libraries.get(lib, None)
        return dep and dep.is_installed
        
    @classmethod
    def configuration_steps(cls):
        r"""Get a list of configuration steps with tuples of flags and
        boolean values.

        Returns:
            OrderedDict: Pairs of descriptions and states for
                different steps in the configuration all steps must be
                True for the language to be configured.

        """
        out = super(CompiledModelDriver, cls).configuration_steps()
        if cls.interface_library:
            for k in cls.libraries[cls.interface_library].get(
                    'external_dependencies', []):
                out[str(k)] = cls.libraries[k].is_installed
        return out
        
    @classmethod
    def is_tool_installed(cls, tooltype):
        r"""Determine if a compilation tool of a certain is installed for
        this language.

        Args:
            tooltype (str): Type of tool to check for. Supported values include
                'compiler', 'linker', & 'archiver'.

        Returns:
            bool: True if a tool of the specified type is installed.

        """
        if cls.is_build_tool and (tooltype != 'compiler'):
            return True
        return (cls.get_tool(tooltype, default=None) is not None)
            
    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        out = super(CompiledModelDriver, cls).is_language_installed()
        for k in cls.tooltypes:
            if k in cls.optional_tooltypes:
                continue
            if not out:  # pragma: no cover
                break
            out = cls.is_tool_installed(k)
        return out

    @classmethod
    def configure(cls, cfg, **kwargs):
        r"""Add configuration options for this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
            **kwargs: Additional keyword arguments are used to set tool
                configuration options (e.g. 'compiler').
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        global _tool_registry
        if (cls.language is not None) and (not cfg.has_section(cls.language)):
            cfg.add_section(cls.language)
        for k, v in kwargs.items():
            if k not in _tool_registry._bases:  # pragma: debug
                raise ValueError(f"Unexpected configuration option: '{k}'")
            vtool = None
            try:
                vtool = _tool_registry.tool_instance(
                    k, v, dont_check_executable=True)
            except InvalidCompilationTool:  # pragma: debug
                reg = _tool_registry.tooltype[k]
                for kreg, vreg in reg.items():
                    if kreg in v:
                        vtool = vreg
                        break
            if not vtool:  # pragma: debug
                raise InvalidCompilationTool(
                    f"Could not locate a {k} tool '{v}'.")
            cfg.set(cls.language, k, vtool.toolname)
            if os.path.isfile(v):
                cfg.set(cls.language, f'{vtool.toolname}_executable', v)
        # Call __func__ to avoid direct invoking of class which dosn't
        # exist in after_registration where this is called
        return ModelDriver.configure.__func__(cls, cfg)
        
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
        global _tool_registry
        out = super(CompiledModelDriver, cls).configure_executable_type(cfg)
        for k in cls.tooltypes:
            default_tool_name = _tool_registry.toolname(
                k, language=cls.language, driver=cls, default=None)
            # Check default tool to make sure it is installed
            if default_tool_name:
                default_tool = _tool_registry.tool(k, default_tool_name)
                if not default_tool.is_installed():  # pragma: debug
                    logger.debug(f'Default {k} for {cls.language} '
                                 f'({default_tool_name}) not installed. '
                                 f'Attempting to locate an alternative.')
                    default_tool_name = None
            # Set default tool attribute & record compiler tool if set
            setattr(cls, f'default_{k}', default_tool_name)
            if default_tool_name:
                cfg.set(cls.language, k, default_tool_name)
        return out

    @classmethod
    def configure_library(cls, cfg, k, is_standard=None, **kwargs):
        r"""Add configuration options for an external library.

        Args:
            cfg (YggConfigParser): Config class that options should be set for.
            k (str): Name of the library to configure.
            is_standard (str, optional): If True, the library is treated
                as the language standard. Defaults to None and is determined
                based on the presence of k in cls.standard_libraries.
            **kwargs: Additional keyword arguments are passed to
                locate_file calls.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        v = cls.libraries[k]
        v.from_tool()
        return v.missing()

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
        kws = {'with_asan': True,  # To force location of ASAN lib
               'with_omp': True}
        for k in cls.tooltypes:
            try:
                kws[k] = cls.get_tool(k)
            except InvalidCompilationTool:
                pass
        libs = cls.libraries.specialized(**kws)
        for v in libs.libraries.values():
            v.from_cache(cfg)
            v.update_cache(cfg)
            if not v.is_rebuildable:
                out += v.missing
        return out

    def set_env(self, for_compile=False, compile_kwargs=None,
                toolname=None, **kwargs):
        r"""Get environment variables that should be set for the model
        process.

        Args:
            for_compile (bool, optional): If True, environment variables
                are set that are necessary for compiling. Defaults to
                False.
            compile_kwargs (dict, optional): Keyword arguments that should
                be passed to the compiler's set_env method. Defaults to
                empty dict.
            toolname (str, optional): Name of compiler tool that should be
                used. Defaults to None and the default compiler for the
                language will be used.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(CompiledModelDriver, self).set_env(**kwargs)
        out = self.model_dep.get('runtime_env', to_update=out)
        return out

    @classmethod
    def interface_library_spec(cls, **kwargs):
        r"""Speciailized version of the interface library dependency."""
        libs = cls.libraries_class(**kwargs)
        return libs[cls.interface_library]

    @classmethod
    def libraries_class(cls, instance=None, **kwargs):
        r"""Get the libraries specialized for a class."""
        spec = DependencySpecialization.select_attr(
            instance, no_tools=(not isinstance(instance, cls)))
        spec.update(DependencySpecialization.select(kwargs))
        return cls.libraries.specialized(**spec)

    def libraries_instance(self, **kwargs):
        r"""Get the libraries specialized for this instance."""
        return self.libraries_class(self, **kwargs)

    @classmethod
    def compile_dependencies(cls, dep=None, **kwargs):
        r"""Compile any required internal libraries, including the interface."""
        if dep is None:
            dep = cls.interface_library
        if dep is None or not cls.is_installed():
            return
        preserved_kwargs = {
            k: kwargs.pop(k) for k in
            ['dry_run', 'products', 'overwrite', 'verbose',
             'build_driver']
            if k in kwargs}
        kwargs = DependencySpecialization.select(kwargs, no_remainder=True)
        basetool = cls.get_tool(
            'basetool',
            toolname=kwargs.pop(
                'toolname', kwargs.get(
                    'basetool', kwargs.get(
                        cls.basetool, None))))
        kwargs[basetool.tooltype] = basetool
        dep = cls.libraries[dep].specialized(**kwargs)
        kwargs.update(preserved_kwargs)
        dep.build(**kwargs)
        dep.logInfo()

    @classmethod
    def cleanup_dependencies(cls, dep=None, products=None,
                             libtype=None, **kwargs):
        r"""Cleanup dependencies."""
        if products is None:
            suffix = str(uuid.uuid4())[:13]
            products = tools.IntegrationPathSet(
                generalized_suffix=suffix)
        assert products.generalized_suffix
        kwargs.update(
            generalized_suffix=products.generalized_suffix,
            products=products, dry_run=True)
        if isinstance(libtype, str):
            libtype = [libtype]
        elif libtype is None:
            libtype = ['shared', 'static']
        try:
            for libT in libtype:
                cls.compile_dependencies(dep, libtype=libT, **kwargs)
        except NotImplementedError:  # pragma: debug
            pass
        super(CompiledModelDriver, cls).cleanup_dependencies(
            products=products)

    def build_model(self, source_files=None, dep=None, **kwargs):
        r"""Compile model executable(s).

        Args:
            source_files (list, optional): Source files that will be
                compiled. Defaults to None and is set to the source_files
                attribute.
            dep (CompilationDependency, optional): Dependency that should
                be compiled. If not provided the model_dep will be used.
            **kwargs: Keyword arguments are passed on to dep's call
                method.

        Returns:
            str: Compiled model file path.

        """
        if source_files:
            kwargs['source'] = source_files
        if dep is None:
            if source_files and source_files != self.source_files:
                dep = self.create_model_dep(**kwargs)
            else:
                dep = self.model_dep
        dep = dep.specialized(**kwargs)
        kwargs = DependencySpecialization.remainder(
            kwargs, remove_parameters=dep.all_parameters())
        for k in ['overwrite', 'working_dir']:
            kwargs.setdefault(k, getattr(self, k))
        return dep.build(**kwargs)

    @classmethod
    def call_tool(cls, obj, tooltype='compiler', **kwargs):
        r"""Link several object files to create an executable or library (shared
        or static), checking for errors.

        Args:
            obj (list): Object files that should be linked.
            language (str, optional): Language that should be used to link
                the files. Defaults to None and the language of the current
                driver is used.
            toolname (str, optional): Name of compiler tool that should be used.
                Defaults to None and the default compiler for the language will
                be used.
            **kwargs: Additional keyword arguments are passed to run_executable.

        Returns:
            str: Full path to compiled source.

        """
        kwargs.setdefault(
            'basetool', kwargs.get(tooltype, cls.get_tool(tooltype)))
        dep = cls.create_dep(source=obj, **kwargs)
        return dep.libtool(**dep.unused_kwargs)

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(CompiledModelDriver, cls).get_testing_options(**kwargs)
        out.update(
            args=['1'],
        )
        if cls.is_installed() and (not getattr(cls, 'is_build_tool', False)):
            compiler = cls.get_tool('compiler')
            linker = cls.get_tool('linker')
            script_dir = os.path.join('tests', 'scripts')
            include_flag = compiler.create_flag('include_dirs', script_dir)
            library_flag = linker.create_flag('library_dirs', script_dir)
            out['kwargs'].update(compiler_flags=include_flag,
                                 linker_flags=library_flag)
        return out
