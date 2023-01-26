# https://www.python.org/dev/peps/pep-0508/
import os
import re
import pprint
import argparse
import shutil
import uuid
import json
import copy
from collections import UserList, UserDict, OrderedDict
from setup_test_env import (
    SetupParam, get_install_opts, _on_travis, call_script,
    get_summary_commands)
try:
    import yaml
except ImportError:
    yaml = None
_pip_os_map = {'osx': 'Darwin',
               'win': 'Windows',
               'linux': 'Linux'}
_rev_pip_os_map = {v.lower(): k for k, v in _pip_os_map.items()}
_req_dir = os.path.join(os.path.dirname(__file__), 'requirements')


class NoValidRequirementOptions(Exception):
    r"""Indicates that none of the requirement's options are valid."""
    pass


class DependencyNotFound(BaseException):
    r"""Exception raised when a dependency cannot be located."""
    pass


def isolate_package_name(entry):
    r"""Get the package name without any constraints or conditions.

    Args:
        entry (str): Requirements entry.

    Returns:
        str: Package name.

    """
    keys = ['<', '>', '=', ';', '#']
    out = entry
    for k in keys:
        out = out.split(k)[0].strip()
    return out.strip()


def get_pip_dependencies(pkg):
    r"""Get the dependencies required by a package via pip.

    Args:
        pkg (str): The name of a pip-installable package.

    Returns:
        list: The package's dependencies.

    """
    import requests
    url = 'https://pypi.org/pypi/{}/json'
    json = requests.get(url.format(pkg)).json()
    return json['info']['requires_dist']


def get_pip_dependency_version(pkg, dep):
    r"""Get the version of a dependency required by a pip-installable
    package.

    Args:
        pkg (str): The name of a pip-installable package.
        dep (str): The name of a dependency of pkg.

    Returns:
        str: The version of the dependency required by the package.

    """
    reqs = get_pip_dependencies(pkg)
    dep_regex = r'%s(?:\s*\((?P<ver>[^\)]+)\))?' % dep
    for x in reqs:
        m = re.fullmatch(dep_regex, x)
        if m:
            ver = ''
            if m.group('ver'):
                ver = m.group('ver').strip()
            return dep + ver
    raise DependencyNotFound(
        ("Could not locate the dependency '%s' "
         "in the list of requirements for package '%s': %s")
        % (dep, pkg, reqs))


class YggRequirements(UserDict):
    r"""Structure outlining requirements for yggdrasil under different
    circumstances."""

    def __init__(self, *args, **kwargs):
        add = kwargs.pop('add', None)
        raw_data = copy.deepcopy(dict(*args, **kwargs))
        super(YggRequirements, self).__init__(*args, **kwargs)
        self.raw_data = raw_data
        if add:
            self.data['general'] += add
        self.data['general'] = YggRequirementsList(
            self.data['general'])
        for k in self.data['extras'].keys():
            self.data['extras'][k] = YggRequirementsList(
                self.data['extras'][k], extras=[k])
        for k in self.data.pop('bespoke_extras', []):
            self.data['extras'][k] = YggRequirementsList(
                [k], extras=[k])
    
    @classmethod
    def from_file(cls, fname=None, force_yaml=False, add=None):
        r"""Load requirements from a file.

        Args:
            fname (str, optional): Path to YAML/JSON file containing
                requirements. Defaults to 'yggdrasil/requirements.yaml'
                unless pyyaml is not installed and then json will be
                used (unless force_yaml is True).
            force_yaml (bool, optional): If True and fname is None,
                the YAML file will be used even if pyyaml is not
                installed (causing an ImportError). Defaults to False.
            add (list, optional): Additional packages that should be
                added to the general list. Defaults to None and is
                ignored.

        Returns:
            YggRequirements: Requirements instance.

        """
        if fname is None:
            ext = 'yaml'
            if yaml is None and not force_yaml:
                ext = 'json'
            fname = os.path.join(_req_dir, f'requirements.{ext}')
        if fname.endswith(('.yml', '.yaml')):
            out = yaml.load(open(fname, 'r').read(), yaml.SafeLoader)
        else:
            out = json.load(open(fname, 'r'))
        return cls(out, add=add)

    def extras(self, methods=None):
        r"""Get the list of extras.

        Args:
            method (list, optional): List of methods that should
               be present in an extra's requirements for it to be
               returned. Defaults to None and is ignored.

        Returns:
            str: Yggdrasil build varients.

        """
        out = list(self.data['extras'].keys())
        if methods:
            for k, v in self.data['extras'].items():
                if not v.has_method(methods):
                    out.remove(k)
        return out

    def select_extra(self, extra):
        r"""Select the requirements for an extra.

        Args:
            extra (str): Extra to select.

        Returns:
            YggRequirementsList: Extra requirements.

        """
        if extra is None or extra == 'general':
            return self.data['general']
        return self.data['extras'][extra]

    def select(self, param, **kwargs):
        r"""Select requirements that are valid for the provided
        installation options.

        Args:
            param (SetupParam): Setup parameters instance.
            **kwargs: Additional keyword arguments are passed to
                select methods for YggRequirementList members.

        """
        out = YggRequirementsList()
        if param.for_development:
            out += self.data['general'].select(param, **kwargs)
        for extra in self.data['extras']:
            if not param.install_opts[extra]:
                continue
            out += self.data['extras'][extra].select(param, **kwargs)
        return out

    def create_requirements_file_varient(self, varient=None,
                                         save=False, fname=None,
                                         param=None, format_kws=None):
        r"""Create a requirements file for a varient.

        Args:
            varient (str, optional): Build varient that requirements
                should be taken from. Defaults to None and the general
                requirements will be used.
            save (bool, optional): If True and fname is not provided,
                the requirements will be saved to a file with a name
                based on the varient. Defaults to False.
            fname (str, optional): File where requirements should be
                saved. Defaults to None and is ignored.
            param (SetupParam, optional): Parameters that should be
                used to select requirements. Defaults to all Python
                requirements by default.
            format_kws (dict, optional): Keyword arguments to pass to
                the format operation for each requirement.

        """
        if format_kws is None:
            format_kws = {}
        if param is None:
            install_opts = get_install_opts(empty=True)
            kwargs = {}
            if varient is not None:
                for x in self.data['extras'][varient].extras:
                    install_opts[x] = True
            elif 'conda' not in format_kws.get('included_methods', []):
                kwargs['fallback_to_conda'] = False
            param = SetupParam(install_opts=install_opts, **kwargs)
        if save and fname is None:
            if varient is None:
                fname = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'requirements.txt')
            else:
                fname = os.path.join(
                    _req_dir, f'requirements_{varient}.txt')
        reqs = self.select_extra(varient).select(
            param, allow_multiple=True, allow_missing=True,
            ignore_existing=True,
            deselect_flags={'not_in_txt': True})
        lines = reqs.format(standard='pip', fname=fname, **format_kws)
        if fname is not None:
            lines_str = '\n\t'.join(lines)
            print(f"Created '{fname}':\n\t{lines_str}")
        return lines

    def create_requirements_files(self):
        r"""Create requirements files for all available varients."""
        self.create_requirements_file_varient(save=True,
                                              format_kws={'excluded_methods': ['conda']})
        extras_sep = ['dev', 'testing', 'docs']
        format_kws = {'included_methods': ['conda']}
        for k in extras_sep:
            self.create_requirements_file_varient(
                k, save=True, format_kws=format_kws)
        # Optional requirements
        format_kws = {'include_extra': True,
                      'excluded_methods': ['conda', 'pip']}
        lines = []
        for k in self.extras():
            if k in extras_sep:
                continue
            lines += self.create_requirements_file_varient(
                k, format_kws=format_kws)
        lines = sorted(lines)
        fname_opt = os.path.join(
            _req_dir, 'requirements_optional.txt')
        with open(fname_opt, 'w') as fd:
            fd.write('\n'.join(lines) + '\n')
        lines_str = '\n\t'.join(lines)
        print(f"Created '{fname_opt}':\n\t{lines_str}")
        # Piponly/condaonly
        for method in ['pip', 'conda']:
            if method == 'pip':
                excluded = 'conda'
            else:
                excluded = 'pip'
            format_kws = {'include_extra': True,
                          'included_methods': [method],
                          'excluded_methods': [excluded, 'python']}
            fname = os.path.join(
                _req_dir,
                f'requirements_{method}only.txt')
            lines = []
            if method == 'conda':
                lines += self.create_requirements_file_varient(
                    format_kws=format_kws)
            for k in self.extras():
                if k in extras_sep:
                    continue
                lines += self.create_requirements_file_varient(
                    k, format_kws=format_kws)
            lines = sorted(lines)
            with open(fname, 'w') as fd:
                fd.write('\n'.join(lines) + '\n')
            lines_str = '\n\t'.join(lines)
            print(f"Created '{fname}':\n\t{lines_str}")

    def create_conda_recipe_varient(self, varient=None,
                                    param=None, format_kws=None):
        r"""Create a conda entry for a varient.

        Args:
            varient (str, optional): Build varient that requirements
                should be taken from. Defaults to None and the general
                requirements will be used.
            param (SetupParam, optional): Parameters that should be
                used to select requirements. Defaults to all Python
                requirements by default.
            format_kws (dict, optional): Keyword arguments to pass to
                the format operation for each requirement.

        Returns:
            dict: Entry for the varient.

        """
        if param is None:
            install_opts = get_install_opts(empty=True)
            if varient is not None:
                for x in self.data['extras'][varient].extras:
                    install_opts[x] = True
            param = SetupParam('conda', install_opts=install_opts,
                               deps_method='conda_recipe')
        if format_kws is None:
            format_kws = {}
        format_kws.setdefault('included_methods', ['conda_recipe'])
        reqs = self.select_extra(varient).select(
            param, ignore_existing=True, allow_multiple=True,
            deselect_flags={'not_in_recipe': True})
        if not reqs:
            return {}
        deps = reqs.format(standard='conda', **format_kws)
        return deps

    def create_conda_recipe(self):
        r"""Create a conda recipe file."""
        fname = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'recipe', 'meta.yaml')
        lines = open(fname, 'r').read()
        bound_defs = {
            'version': ('{% set version = "', '"'),
            'entry_points': ('\n  entry_points:', '\nrequirements:'),
            'requirements': ('\nrequirements:', '\ntest:'),
            'extras': ('\noutputs:', '\nabout:')}
        bounds = {}
        for k, v in bound_defs.items():
            idx_beg = lines.find(v[0])
            if k in ['version', 'entry_points']:
                idx_beg += len(v[0])
            idx_end = lines.find(v[1], idx_beg)
            bounds[k] = (idx_beg, idx_end)
        if any(x[0] == -1 or x[1] == -1 for x in bounds.values()):
            raise ValueError(f"Could not find indices to replace: "
                             f"{bounds}")
        
        class OrderedDumper(yaml.SafeDumper):

            def increase_indent(self, flow=False, indentless=False):
                return super(OrderedDumper, self).increase_indent(
                    flow, False)

            def choose_scalar_style(self, *args, **kwargs):
                out = super(OrderedDumper, self).choose_scalar_style(
                    *args, **kwargs)
                if out in ["\"", "\'"]:
                    return None
                return out

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items())

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        yaml_kws = {"Dumper": OrderedDumper,
                    'default_flow_style': False,
                    'width': 1000}
        # Base package
        fname_entry_points = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'console_scripts.txt')
        entry_points = open(fname_entry_points, 'r').read()
        entry_points = entry_points.replace('=', ' = ').splitlines()
        deps = self.create_conda_recipe_varient()
        new_lines = lines[:bounds['entry_points'][0]]
        new_lines += '\n    - ' + '\n    - '.join(entry_points) + '\n'
        new_lines += lines[bounds['entry_points'][1]:bounds['requirements'][0]]
        new_lines += '\n' + yaml.dump(deps, **yaml_kws)
        new_lines += lines[bounds['requirements'][1]:
                           bounds['extras'][0]]
        # Varients
        extra_deps = {'outputs': [{'name': 'yggdrasil'}]}
        for k in self.extras():
            k_out = self.create_conda_recipe_varient(k)
            if k_out:
                extra_deps['outputs'].append(k_out)
        new_lines += '\n' + yaml.dump(extra_deps, **yaml_kws)
        new_lines += '\n' + lines[bounds['extras'][1]:]
        with open(fname, 'w') as fd:
            fd.write(new_lines)
        print(f"Created '{fname}':\n{new_lines}")

    def create_extras_require(self):
        r"""Create a config file containing extras_require."""
        import configparser
        fname = os.path.join(_req_dir, 'requirements_extras.ini')
        extras = {}
        format_kws = {'include_method': False, 'include_extra': False}
        for k in self.extras():
            extras[k] = self.create_requirements_file_varient(
                k, format_kws=format_kws)
        config = configparser.ConfigParser(allow_no_value=True)
        for k, v in extras.items():
            if not v:
                continue
            config.add_section(k)
            for x in v:
                config.set(k, x, None)
        with open(fname, 'w') as fd:
            config.write(fd)
        print(f"Created '{fname}':\n{open(fname, 'r').read()}")


class YggRequirementsList(UserList):
    r"""Set of requirements."""

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict):
            kwargs.update(args[0])
            args = (kwargs.pop('requirements'), )
        requires_extras = kwargs.pop('requires_extras', None)
        extras = kwargs.pop('extras', None)
        if requires_extras:
            if extras is None:
                extras = []
            for k in requires_extras:
                if k not in extras:
                    extras.append(k)
        super(YggRequirementsList, self).__init__(*args, **kwargs)
        self.extras = extras
        self.data = [YggRequirement.from_file(x, extras=extras)
                     for x in self.data]

    @classmethod
    def from_files(cls, fname, skip=None, add=None):
        r"""Read a list of requirements from one or more pip-style
        files.

        Args:
            fname (str, list): One or more file names.
            skip (list, optional): Names of packages to skip. Defaults
                to None and is ignored.
            add (list, optional): Additional packages that should be
                added to the list. Defaults to None and is ignored.

        Returns:
            YggRequirementsList: Requirements list.

        """
        if not isinstance(fname, list):
            fname = [fname]
        out = YggRequirementsList()
        lines = []
        packages = []
        for ifname in fname:
            with open(ifname, 'r') as fd:
                lines += fd.readlines()
        if add:
            lines += add
        for x in lines:
            x = x.strip()
            if x.startswith('#'):
                continue
            pkg = YggRequirement.from_pip_requirement(x)
            pkg_name = pkg.base_name
            if (skip and pkg_name in skip) or pkg_name in packages:
                continue
            out.append(pkg)
            packages.append(pkg_name)
        return out

    def flatten(self):
        r"""Return a list of requirements that is flattened so that
        members do not have any 'add' members.

        Returns:
            list: Complete list of requirements covered by this set.

        """
        if not any(x.add for x in self.data):
            return self
        out = YggRequirementsList(extras=self.extras)
        for x in self.data:
            out += x.flatten()
        return out

    def has_method(self, methods):
        r"""Determine if one or more methods is present in any of the
        member requirements.

        Args:
            methods (list): Methods to check for.

        Returns:
            bool: True if any of the specified methods are present,
                False otherwise.

        """
        for x in self.data:
            if x.has_method(methods):
                return True
        return False

    def select_method(self, included_methods=None,
                      excluded_methods=None):
        r"""Select requirements based on methods constraints.

        Args:
            included_methods (list, optional): Installation methods
                that should be included. By default, python and the
                format standard will be added to this list. If a
                requirement has a method that is not in this list, it
                will be skipped.
            excluded_methods (list, optional): Installation methods
                that should be excluded. Defaults to empty list.

        Returns:
            YggRequirementsList: List of selected requirements.

        """
        if included_methods is None:
            included_methods = []
        if excluded_methods is None:
            excluded_methods = []
        out = YggRequirementsList(extras=self.extras)
        for x in self.data:
            if ((x.method in included_methods
                 and x.method not in excluded_methods)):
                out.append(x)
        return out

    def select(self, param, **kwargs):
        r"""Select requirements that are valid for the provided
        installation options.

        Args:
            param (SetupParam): Setup parameters instance.
            **kwargs: Additional keyword arguments are passed to
                the add_option method of member YggRequirement
                instances.

        Returns:
            YggRequirementsList: List of selected requirements.

        """
        out = YggRequirementsList(extras=self.extras)
        for x in self.data:
            x.add_option(out, param, **kwargs)
        return out

    def sorted_by_method(self, format_names=False):
        r"""

        Args:
            format_names (bool, optional): If True, the returned
                dictionary will be a formatted list of requirements.
                Defaults to False.

        Returns:
            dict: Requirements sorted by method.

        """
        out = {}
        for x in self.data:
            if x.method not in out:
                out[x.method] = YggRequirementsList()
            out[x.method].append(x)
        if format_names:
            for k, v in out.items():
                out[k] = v.format(included_methods=[k], name_only=True)
        else:
            for k, v in out.items():
                out[k] = out[k].flatten()
        return out

    def format(self, fname=None, included_methods=None,
               excluded_methods=None, standard='pip', **kwargs):
        r"""Format this set of requirements according to a certain
        standard.

        Args:
            fname (str, optional): File where lines should be written.
            standard (str, optional): Standard that should be used.
            included_methods (list, optional): Installation methods
                that should be included. By default, python and the
                format standard will be added to this list. If a
                requirement has a method that is not in this list, it
                will be skipped.
            excluded_methods (list, optional): Installation methods
                that should be excluded. Defaults to empty list.
            **kwargs: Additional keyword arguments are passed to the
                format method for each requirement.

        Returns:
            list: Formated requirement lines.

        """
        if included_methods is None:
            included_methods = []
        included_methods += ['python', standard]
        selected = self.select_method(
            included_methods=included_methods,
            excluded_methods=excluded_methods).flatten()
        kwargs['standard'] = standard
        out = [
            x.format(**kwargs) for x in selected if not x.host_only]
        out = sorted(list(set(out)))
        if standard == 'conda':
            req = out
            out = OrderedDict()
            host_req = [
                x.format(**kwargs) for x in selected if x.host]
            if self.extras:
                host_req.append('python')
                name = self.extras[0]
                out['name'] = f"yggdrasil.{name}"
                out['build'] = OrderedDict([
                    ('string', (
                        "py{{ PY_VER_MAJOR }}{{ PY_VER_MINOR }}h"
                        "{{ PKG_HASH }}_{{ PKG_BUILDNUM }}")),
                    ('run_exports', [
                        f"{{{{ pin_subpackage('yggdrasil.{name}') }}}}"
                    ])
                ])
                if len(self.extras) > 1:
                    req = [
                        f"{{{{ pin_subpackage('yggdrasil.{x}', exact=True) }}}}"
                        for x in self.extras[1:]] + req
                else:
                    req.insert(
                        0, "{{ pin_subpackage('yggdrasil', exact=True) }}")
            out['requirements'] = OrderedDict()
            if host_req:
                out['requirements']['host'] = sorted(host_req)
            out['requirements']['run'] = req
            if fname is not None:
                with open(fname, 'w') as fd:
                    yaml.write(fd, out)
        else:
            if fname is not None:
                with open(fname, 'w') as fd:
                    fd.write('\n'.join(out) + '\n')
        return out

    def install(self, param, return_commands=False, **kwargs):
        r"""Install requirements in this list.

        Args:
            param (SetupParam) Parameters defining the setup.
            return_commands (bool, optional): If True, the script
                is assembled (including any temporary files containing
                requirements), but not executed. Defaults to False.
            **kwargs: Additional keyword arguments are passed to
                the install_command_prefix method for each member
                requirement.

        Returns:
            list: Comands resulting in installation.

        """
        cmds = []
        reqs = self.sorted_by_method()
        if 'python' in reqs:
            if param.method_base == 'pip':
                reqs['pip'] += reqs.pop('python')
            else:
                reqs['conda'] += reqs.pop('python')
        # Do non-python first
        order = [k for k in reqs.keys() if k not in
                 ['python', 'pip', 'conda']]
        order += [k for k in reqs.keys() if k in
                  ['python', 'pip', 'conda']]
        temp_files = []
        for k in order:
            v = reqs[k]
            mapping = {}
            for x in v:
                kargs, kparam = x.install_command_prefix(
                    param, **kwargs)
                if not kargs:
                    continue
                if kargs not in mapping:
                    mapping[kargs] = kparam
                else:
                    mapping[kargs]['requirements'] += kparam['requirements']
            for k, v in mapping.items():
                cmds += YggRequirement.format_install_commands(
                    k, v, param, temp_files=temp_files)
        if temp_files:
            if param.install_opts['os'] == 'win':
                cmds += [
                    f"{param.python_cmd} -c \'exec(\"import os;"
                    f"if os.path.isfile(\\\"{x}\\\"): "
                    f"os.remove(\\\"{x}\\\")\")\'"
                    for x in temp_files]
            else:
                cmds += [
                    f"{param.python_cmd} -c \'import os\n"
                    f"if os.path.isfile(\"{x}\"): "
                    f"os.remove(\"{x}\")\'"
                    for x in temp_files]
        if not return_commands:
            summary_cmds = get_summary_commands(param=param)
            cmds = summary_cmds + cmds + summary_cmds
        if not (param.dry_run or return_commands):
            try:
                call_script(cmds, verbose=param.verbose)
            finally:
                for x in temp_files:
                    if os.path.isfile(x):
                        os.remove(x)
        return cmds


class YggRequirement(object):
    r"""Yggdrasil requirement.

    Args:
        name (str): Name of the requirement.
        os (str, optional): Required operating system.
        method (str, optional): Required installation method.
        add (list, optional): Additional packages that should be
            installed with the requirement.
        executable (str, optional): Executable that should be checked
            for before installing the requirement.
        extras (list, optional): yggdrasil build varient/extra(s) that
            the requirement belongs to.
        options (list, optional): Different installation options for
            the requirement under different conditions.
        host (bool, optional): If True, the requirement must be
            included in the host section in a conda recipe. Defaults
            to False.
        host_only (bool, optional): If True, the requirment should
            only be included in the host section of a conda recipe.
            Defaults to False.
        flags (dict, optional): Additional flags that can be used
            during installation. Defaults to empty dict.

    """

    def __init__(self, name, os=None, method='python', add=None,
                 executable=None, extras=None, options=None,
                 host=False, host_only=False, flags=None):
        self.name = name
        self.os = os
        self.method = method
        if add is not None:
            if not isinstance(add, list):
                add = [add]
            new_add = []
            for x in add:
                x_dict = {'os': os,
                          'method': method,
                          'extras': extras,
                          'host': host,
                          'host_only': host_only,
                          'flags': flags}
                if isinstance(x, str):
                    x_dict['name'] = x
                else:
                    x_dict.update(x)
                new_add.append(
                    YggRequirement(x_dict.pop('name'), **x_dict))
            add = new_add
        self.add = add
        self.executable = executable
        self.extras = extras
        self.options = options
        self.host = host
        self.host_only = host_only
        if flags is None:
            flags = {}
        self.flags = flags

    @property
    def kwargs(self):
        r"""dict: Keyword arguments used to create this requirement."""
        out = {}
        for k in ["name", "os", "method", "add", "executable",
                  "extras", "options", "host", "host_only", "flags"]:
            out[k] = getattr(self, k)
        return out

    def install(self, param, return_commands=False, **kwargs):
        r"""Install this requirement.

        Args:
            param (SetupParam) Parameters defining the setup.
            return_commands (bool, optional): If True, the script
                is assembled (including any temporary files containing
                requirements), but not executed. Defaults to False.
            **kwargs: Additional keyword arguments are passed to
                the install_command_prefix method.

        Returns:
            list: Comands resulting in installation.

        """
        cmds = []
        k, v = self.install_command_prefix(param, **kwargs)
        if not k:
            return cmds
        cmds += YggRequirement.format_install_commands(k, v, param)
        if not return_commands:
            summary_cmds = get_summary_commands(param=param)
            cmds = summary_cmds + cmds + summary_cmds
        if not (param.dry_run or return_commands):
            call_script(cmds, verbose=param.verbose)
        return cmds

    @staticmethod
    def format_install_commands(args, kwargs, param, temp_files=None):
        r"""Format installation commands.

        Args:
            args (str): Installation arguments.
            kwargs (dict): Additional parameters controlling
                the installation.
            param (SetupParam) Parameters defining the setup.
            temp_files (list, optional): Existing list that generated
                files should be added to so that they can be removed
                after installation is complete.

        Returns:
            list: Commands resulting in installation.

        """
        cmds = []
        req = sorted(list(set(kwargs['requirements'])))
        if len(req) == 0:
            return cmds
        elif len(req) == 1:
            if kwargs.get('quote_constraints', False):
                quoted_req = []
                for x in req:
                    if any(y in x for y in '!=<>'):
                        quoted_req.append(f'"{x}"')
                    else:
                        quoted_req.append(x)
                req = quoted_req
        else:
            if kwargs.get('individually', False):
                for x in req:
                    ikwargs = dict(kwargs, requirements=[x])
                    cmds += YggRequirement.format_install_commands(
                        args, ikwargs, param, temp_files=temp_files)
                return cmds
            if kwargs.get('file_flag', False):
                ifile = f"requirements_{uuid.uuid4()}.txt"
                if param.dry_run:
                    req_str = '\n\t'.join(req)
                    print(f"Temporary file: {ifile}\n\t{req_str}")
                else:
                    with open(ifile, 'w') as fd:
                        fd.write('\n'.join(req))
                temp_files.append(ifile)
                args += f" {kwargs['file_flag']} "
                req = [ifile]
        cmds.append(f"{args} {' '.join(req)} "
                    f"{' '.join(kwargs.get('suffix', ''))}")
        return cmds

    def install_command_prefix(self, param):
        r"""Get the arguments in the installation command for a given
        method.

        Args:
            param (SetupParam) Parameters defining the setup.

        Returns:
            list, dict: Installation commands and some parameters for
                the installation command.

        """
        method = self.method
        if method == 'python':
            method = param.method_base
        args = []
        install_param = {}
        if method == 'pip':
            install_param['file_flag'] = '-r'
            install_param['quote_constraints'] = True
            args += [param.python_cmd, '-m', 'pip', 'install']
            if param.verbose:
                args.append('--verbose')
            if param.user:
                args.append('--user')
        elif method == 'conda':
            install_param['file_flag'] = '--file'
            args = [param.conda_exe, 'install']
            if param.always_yes:
                args.append('-y')
            if param.verbose:
                args.append('-vvv')
            else:
                args.append('-v')
                # args.append('-q')
            if param.conda_env:
                args += ['--name', param.conda_env]
            if param.user:
                args.append('--user')
        elif param.only_python or method.endswith('skip'):
            pass
        elif method == 'cran':
            pass  # TODO?
        elif method == 'brew':
            args = ['brew']
            if self.flags.get('reinstall', False):
                args.append('reinstall')
            else:
                args.append('install')
            if _on_travis and self.flags.get('from_src_on_travis', False):
                args.append('--build-from-source')
        elif method == 'apt':
            if not param.install_opts['no_sudo']:
                args += ['sudo']
            args += ['apt']
            if param.always_yes and not param.install_opts['no_sudo']:
                args += ['-y']
            args += ['update;']
            if not param.install_opts['no_sudo']:
                args += ['sudo']
            args += ['apt-get']
            if param.always_yes and not param.install_opts['no_sudo']:
                args += ['-y']
            args += ['install']
            install_param['requires_shell'] = True
        elif method == 'choco':
            args += ['choco', 'install']
            install_param.update(
                individually=True,
                suffix=['--force'])
        elif method == 'vcpkg':
            args += ['vcpkg.exe', 'install']
            install_param['suffix'] = ['--triplet', 'x64-windows']
        else:
            raise NotImplementedError(method)
        if 'install_flags' in self.flags:
            args += self.flags['install_flags']
        if args:
            install_param['requirements'] = [
                self.format(name_only=True)]
        return ' '.join(args), install_param

    @property
    def base_name(self):
        r"""str: Base name of the package."""
        return isolate_package_name(self.full_name)

    @property
    def full_name(self):
        r"""str: Full name of the package."""
        if self.flags and self.flags.get('from_env', False):
            env = self.name.upper()
            if isinstance(self.flags['from_env'], str):
                env = self.flags['from_env']
            if env in os.environ and os.environ[env] != self.name:
                return os.environ[env]
        return self.name

    def pip_requirement(self, include_os=True, include_extra=False,
                        include_method=True, padding=17,
                        name_only=False):
        r"""Get the formatted pip requirement string.

        Args:
            include_os (bool, optional): If True, include any OS
               constraints in the requirement using pip's format.
               Defaults to True.
            include_extra (bool, optional): If True, include the
               build extra associated with the requirement (if one
               exists) in the varients tag next to the requirement.
               Defaults to False.
            include_method (bool, optional): If True, include the
               method associated with the requirement (if one exists)
               in the varients tag next to the requirement. Defaults
               to True.
            padding (int, optional): Number of spaces to pad with
               before varients.
            name_only (bool, optional): If True, no additional
               information will be added to the requirement. Implies
               include_os==True, include_extra==True, and
               include_method==True. Defaults to False.

        Returns:
            str: Pip requirement.

        """
        out = self.full_name
        if name_only:
            include_os = False
            include_extra = False
            include_method = False
        if include_os and self.os is not None:
            out += "; platform_system"
            if self.os == 'unix':
                out += " != 'Windows'"
            else:
                assert self.os in _pip_os_map
                out += f" == '{_pip_os_map[self.os]}'"
            if 'pip_markers' in self.flags:
                out += ' ' + '; '.join(self.flags['pip_markers'])
        varients = []
        if include_method and self.method != 'python':
            varients.append(self.method)
        if include_extra and self.extras is not None:
            varients += self.extras
        if varients:
            suffix = self.format_varients(varients)
            out = self.add_padded_suffix(out, suffix, padding=padding)
        if self.add:
            out = [out]
            for x in self.add:
                out.append(
                    x.pip_requirement(include_os=include_os,
                                      include_extra=include_extra,
                                      include_method=include_method,
                                      padding=padding,
                                      name_only=name_only))
            out = '\n'.join(out)
        return out

    def conda_requirement(self):
        r"""Get the formatted conda requirement string.

        Returns:
            str: Conda requirement.

        """
        suffix = ''
        varients = []
        if self.os is not None:
            if self.os == 'unix':
                varients.append('not win')
            else:
                varients.append(self.os)
        if varients:
            suffix += '  ' + self.format_varients(varients)
        out = self.full_name + suffix
        if self.add:
            out = [out]
            for x in self.add:
                out.append(x.conda_requirement())
            out = '\n'.join(out)
        return out

    def format_varients(self, varients):
        r"""Format varients into the comment form that should be used
        at the end of a requirement line.

        Args:
            varients (list): Varient tags indicating under what
                conditions a requirement should be used.

        Returns:
            str: Formatted varients string for end of requirement.

        """
        return f"# [{','.join(varients)}]"

    def has_method(self, methods):
        r"""Determine if one or more methods is present in any of the
        requirement's options.

        Args:
            methods (list): Methods to check for.

        Returns:
            bool: True if any of the specified methods are present,
                False otherwise.

        """
        if self.options:
            for x in self.options:
                if x.has_method(methods):
                    return True
            return False
        if not isinstance(methods, (list, tuple)):
            methods = [methods]
        return self.method in methods
        
    def add_padded_suffix(self, name, suffix, padding=0):
        r"""Add a suffix with padding so that first character of
        suffix lands at padding or greater.

        Args:
            name (str): Name that proceeds suffix.
            suffix (str): Suffix to add after padding.
            padding (int, optional): Minimum column that suffix should
                be padded to. Defaults to 0. A mininum of 2 spaces
                will be added between name and suffix.

        Returns:
            str: Formatted name with suffix.

        """
        if not suffix:
            return name
        spaces = padding - len(name)
        if spaces < 2:
            spaces = 2
        return f"{name}{' ' * spaces}{suffix}"

    def format(self, standard='pip', **kwargs):
        r"""Format this requirement according to a certain standard.

        Args:
            standard (str, optional): Standard that should be used.
            **kwargs: Additional keyword arguments are passed to
                either pip_requirement or conda_requirement as
                dictanted by the provided standard.

        Returns:
            str: Formated requirement line.

        """
        if standard == 'pip':
            return self.pip_requirement(**kwargs)
        elif standard == 'conda':
            return self.conda_requirement(**kwargs)
        else:  # pragma: debug
            raise ValueError(
                f"Standard must be one of ['pip', 'conda'], not"
                f" {standard}.")

    def executable_exists(self):
        r"""Returns true if the executable associated with this
        requirement already exists."""
        if self.executable is None:
            return False
        return shutil.which(self.executable)

    def os_matches(self, param):
        r"""Returns true if the OS requirement is met.

        Args:
            param (SetupParam) Parameters defining the setup.

        Returns:
            bool: True if the OS requirement is met.

        """
        return ((self.os is None
                 or self.os == param.install_opts['os']
                 or param.install_opts['os'] == 'any'
                 or (self.os == 'unix' and (param.install_opts['os']
                                            in ['osx', 'linux']))))

    def method_selected(self, param):
        r"""Returns True if the method requirement is met.

        Args:
            param (SetupParam) Parameters defining the setup.

        Returns:
            bool: True if the method requirement is met.

        """
        if ((param.only_python
             and self.method not in ['python', 'pip', 'conda'])):
            return False
        methods = [self.method]
        if 'method_validate' in self.flags:
            methods.append(self.flags['method_validate'])
        return any(x in param.valid_methods for x in methods)

    def flags_selected(self, select_flags=None, deselect_flags=None,
                       required_flags=None):
        r"""Determine if requirement flags are selected/deselected.

        Args:
            select_flags (dict, optional): Dictionary of flags for
                which the requirement will be selected if it has
                matching flags. The requirement will also match if a
                flag is missing. Defaults to None and is ignored.
            deselect_flags (dict, optional): Dictionary of flags for
                which the requirement will NOT be selected if it has
                matching flags. Defaults to None and is ignored.
            required_flags (list, optional): Flags that are required.
                Defaults to None and is ignored.

        Returns:
            bool: True if the requirement is selected, False otherwise

        """
        if select_flags:
            if not self.flags:
                return False
            for k, v in select_flags.items():
                if k not in self.flags:
                    continue
                if self.flags[k] != v:
                    return False
        if deselect_flags and self.flags:
            for k, v in deselect_flags.items():
                if k not in self.flags:
                    continue
                if self.flags[k] == v:
                    return False
        if required_flags:
            if not self.flags:
                return False
            for k in required_flags:
                if k not in self.flags:
                    return False
        return True

    def is_selected(self, param, allow_multiple=False,
                    ignore_existing=False, os_covered=None,
                    select_flags=None, deselect_flags=None,
                    required_flags=None):
        r"""Determine if the provided parameters select this
        requirement.

        Args:
            param (SetupParam) Parameters defining the setup.
            allow_multiple (bool, optional): If True, multiple options
                may be selected for the same requirement. Defaults to
                False.
            ignore_existing (bool, optional): If True, any executable
                associated with the requirement will not be checked.
                Defaults to False.
            os_covered (dict, optional): Mapping of os to booleans to
                indicate which OSes have a valid requirement option.
            select_flags (dict, optional): Dictionary of flags for
                which the requirement will be selected if it has
                matching flags. Defaults to None and is ignored.
            deselect_flags (dict, optional): Dictionary of flags for
                which the requirement will NOT be selected if it has
                matching flags. Defaults to None and is ignored.
            required_flags (list, optional): Flags that are required.
                Defaults to None and is ignored.

        Returns:
            bool: True if the requirement is selected, False otherwise

        """
        # print(self.name, not self.os_matches(param),
        #       not self.method_selected(param)
        #       not self.flags_selected(select_flags=select_flags,
        #                               deselect_flags=deselect_flags,
        #                               required_flags=required_flags),
        #       ((not ignore_existing) and self.executable_exists()))
        if not self.os_matches(param):
            return False
        if not self.method_selected(param):
            return False
        if not self.flags_selected(select_flags=select_flags,
                                   deselect_flags=deselect_flags,
                                   required_flags=required_flags):
            return False
        if os_covered is not None:
            os_mark = []
            if self.os is None:
                os_mark = list(os_covered.keys())
            elif self.os == 'unix':
                os_mark = ['osx', 'linux']
            else:
                os_mark = [self.os]
            
            # if (not allow_multiple) and
            if all(os_covered[k] for k in os_mark):
                return False
            for k in os_mark:
                os_covered[k] = True
        if (not ignore_existing) and self.executable_exists():
            return False
        return True

    def add_option(self, out, param, allow_missing=False,
                   allow_multiple=False, os_covered=None,
                   for_setup=False, **kwargs):
        r"""Add the first valid option for this requirement.

        Args:
            out (list): List that requirement option should be added to.
            param (SetupParam) Parameters defining the setup.
            allow_missing (bool, optional): If True, requirements
                without valid options will be ignored. Defaults to
                False.
            allow_multiple (bool, optional): If True, multiple options
                may be selected for the same requirement. Defaults to
                False.
            os_covered (dict, optional): Mapping of os to booleans to
                indicate which OSes have a valid requirement option.
            **kwargs: Additional keyword arguments are passed to
                is_selected and add_option calls for child options.

        """
        if param.deps_method == 'supplemental':
            allow_missing = True
        kwargs.update(os_covered=os_covered,
                      allow_multiple=allow_multiple)
        if self.extras and not all([param.install_opts[x]
                                    for x in self.extras]):
            return False
        if self.options is None:
            solf = self
            if for_setup and 'method_in_setup' in self.flags:
                solf_kws = self.kwargs
                solf_kws['method'] = self.flags['method_in_setup']
                solf = YggRequirement(**solf_kws)
            if not solf.is_selected(param, **kwargs):
                return False
            if not solf.method.endswith('skip'):
                out.append(solf)
            return True
        else:
            os_covered = {'win': False, 'linux': False, 'osx': False}
            kwargs.update(os_covered=os_covered,
                          allow_missing=allow_missing)
            kwargs['os_covered'] = os_covered
            added = []
            match = False
            for x in self.options:
                if x.add_option(out, param, **kwargs):
                    added.append(x.name)
                    if all(os_covered.values()) or (not allow_multiple):
                        match = True
                        break
            if all(os_covered.values()):
                match = True
            if not (match or allow_missing):
                raise NoValidRequirementOptions(
                    f"Failed to find valid option for: {self}"
                    f" (os_covered = {os_covered})")
        return False

    def __str__(self):
        if self.options is None:
            out = f'Requirement({self.name}'
            if self.os is not None:
                out += f', os={self.os}'
            if self.method is not None:
                out += f', method={self.method}'
            if self.flags:
                out += f', flags={self.flags}'
            out += ')'
            return out
        return str({self.name: self.options})
    
    def __repr__(self):
        return self.__str__()

    def flatten(self):
        r"""Return a list of requirements covered by this one
        including any specified by the 'add' keyword.

        Returns:
            list: Requirements covered by this one.

        """
        assert not self.options
        out = YggRequirementsList()
        if not self.add:
            out.append(self)
            return out
        cpy_kws = self.kwargs
        cpy_kws.pop('add')
        out.append(YggRequirement(cpy_kws.pop('name'), **cpy_kws))
        for x in self.add:
            out += x.flatten()
        return out

    @classmethod
    def from_pip_requirement(cls, src, verbose=False):
        r"""Create a requirement from a pip-style string.

        Args:
            src (str): Pip-style requirement string.
            verbose (bool, optional): If True, setup steps are run
                with verbosity turned up. Defaults to False.

        Returns:
            YggRequirement: Pip requirement.

        """
        regex_constrain = r'(?:(?:pip)|(?:conda)|(?:[a-zA-Z][a-zA-Z0-9]*))'
        regex_comment = r'\s*\[\s*(?P<vals>%s(?:\s*\,\s*%s)*)\s*\]\s*' % (
            regex_constrain, regex_constrain)
        regex_marker = (r'(?P<name>[a-zA-Z][a-zA-Z0-9_]*)\s*'
                        r'(?P<op>[=!<>]+)\s*'
                        r'(?:\'|\")(?P<val>[a-zA-Z0-9_.]+)(?:\'|\")')
        name = src
        kwargs = {}
        if '#' in name:
            name, comment = name.split('#')
            m = re.fullmatch(regex_comment, comment)
            if m:
                values = []
                for x in m.group('vals').split(','):
                    v = x.strip()
                    values.append(v)
                    if v in ['pip', 'conda']:
                        assert 'method' not in kwargs
                        kwargs['method'] = v
                    elif v in ['win', 'osx', 'linux', 'unix']:
                        assert 'os' not in kwargs
                        kwargs['os'] = v
                    else:
                        kwargs.setdefault('extras', [])
                        kwargs['extras'].append(v)
                if verbose:
                    print(f'src = {src}, values = {values}')
        if ';' in name:
            markers = [x.strip() for x in name.split(';')]
            name = markers[0]
            del markers[0]
            for x in markers:
                m = re.fullmatch(regex_marker, x)
                assert m
                if m.group('name') == 'sys_platform':
                    assert 'os' not in kwargs
                    kwargs['os'] = _rev_pip_os_map[m.group('val')]
                    if m.group('op') == '==':
                        pass
                    elif m.group('op') == '!=':
                        assert kwargs['os'] == 'win'
                        kwargs['os'] = 'unix'
                    else:
                        raise NotImplementedError(m.group('op'))
                else:
                    kwargs.setdefault('flags', {})
                    kwargs['flags'].setdefault('pip_markers', [])
                    kwargs['flags']['pip_markers'].append(x)
        return cls(name.strip(), **kwargs)

    @classmethod
    def from_file(cls, src, parent=None, extras=None):
        r"""Create a requirement from information loaded from the
        requirements.yaml or requirements.json file.

        Args:
            src (str, dict): Requirement information.
            parent (str, optional): Name of parent requirement if this
                is a requirement option. Defaults to None and is
                ignored.
            extras (list, optional): Build varients that are required
                for this requirement to be installed. Defaults to None
                and is ignored.

        Returns:
            YggRequirement: New requirement instance.

        """
        name = None
        kwargs = {}
        if isinstance(src, str):
            name = src
        elif isinstance(src, dict):
            if 'name' in src:
                name = src.pop('name')
                kwargs.update(src)
            else:
                assert len(src) == 1
                for k, v in src.items():
                    name = k
                    if isinstance(v, list):
                        kwargs['options'] = v
                    elif isinstance(v, dict):
                        kwargs.update(v)
                    else:
                        raise RuntimeError(
                            f"Unexpected requirement structure: {src}")
        else:
            raise RuntimeError(
                f"Unexpected requirement of type '{type(src)}': {src}")
        if name is None:
            if parent is None:
                raise RuntimeError(f"Could not determine name: {src}")
            name = parent
        if 'requires_extras' in kwargs:
            if extras is None:
                extras = []
            else:
                extras = list(extras)
            for k in kwargs.pop('requires_extras'):
                if k not in extras:
                    extras.append(k)
        if extras is not None:
            kwargs['extras'] = extras
        if 'options' in kwargs:
            opts = []
            inherit_kwargs = {'name': name}
            for k, v in kwargs.items():
                if k not in ['options', 'requires_extras']:
                    inherit_kwargs[k] = v
            for x in kwargs['options']:
                for k, v in inherit_kwargs.items():
                    x.setdefault(k, v)
                opts.append(YggRequirement.from_file(x, parent=name,
                                                     extras=extras))
            kwargs['options'] = opts
        return cls(name, **kwargs)


def select_requirements(param, fname=None, req=None, **kwargs):
    r"""Select requirements that are valid for the provided
    installation options.

    Args:
        param (SetupParam): Setup parameters instance.
        fname (str, optional): Path to YAML/JSON file containing
            requirements. Defaults to 'yggdrasil/requirements.yaml'
            unless pyyaml is not installed and then json will be used.
        req (list, optional): Pre-loaded list of requirements. If not
            provided, requirements will be loaded from fname.
        **kwargs: Additional keyword arguments are passed to
            YggRequirements.select.

    Returns:
        dict: Requirements sorted by method.

    """
    if req is None:
        req = YggRequirements.from_file(fname)
    return req.select(param, **kwargs).sorted_by_method(
        format_names=True)


def create_requirements(standard, fname=None, req=None):
    r"""Create requirements files for all available varients.

    Args:
        standard (str): Standard that should be used to format lines
            in the file.
        fname (str, optional): Path to YAML/JSON file containing
            requirements. Defaults to 'yggdrasil/requirements.yaml'
            unless pyyaml is not installed and then json will be used.
        req (YggRequirements, optional): Existing set of requirements
            to use. If not provided, one will be created from fname.

    """
    if req is None:
        req = YggRequirements.from_file(fname, force_yaml=True)
    if standard == 'all':
        for k in ['pip', 'conda', 'extras_require', 'json']:
            create_requirements(k, req=req)
    elif standard == 'pip':
        req.create_requirements_files()
    elif standard == 'conda':
        req.create_conda_recipe()
    elif standard == 'extras_require':
        req.create_extras_require()
    elif standard == 'json':
        fname = os.path.join(_req_dir, 'requirements.json')
        with open(fname, 'w') as fd:
            json.dump(req.raw_data, fd, indent=2)
    else:
        raise NotImplementedError(standard)


def create_environment_file(param, fname=None, req=None, add=None,
                            channels=None,
                            fname_out='environment.yml', **kwargs):
    r"""Create an yaml file describing a conda environment.

    Args:
        param (SetupParam): Setup parameters instance.
        fname (str, optional): Path to YAML/JSON file containing
            requirements. Defaults to 'yggdrasil/requirements.yaml'
            unless pyyaml is not installed and then json will be used.
        req (YggRequirements, optional): Existing set of requirements
            to use. If not provided, one will be created from fname
            and add.
        add (list, optional): Additional packages that should be
            installed. Defaults to None and is ignored.
        channels (list, optional): Conda channels that should be used
            in the environment file. Defaults to []. 'conda-forge'
            will be added if it is not already present.
        fname_out (str, optional): Path where the generate file should
            be saved. Defaults to 'environment.yml'.
        **kwargs: Additional keyword arguments are passed to
            YggRequirements.select.

    """
    if req is None:
        file_kwargs = {'add': add}
        if ((isinstance(fname, list)
             or (isinstance(fname, str) and fname.endswith('.txt')))):
            req = YggRequirements.from_files(fname, **file_kwargs)
        else:
            req = YggRequirements.from_file(fname, **file_kwargs)
    kwargs.setdefault('for_setup', True)
    deps = req.select(param, **kwargs).format(name_only=True)
    if channels is None:
        channels = []
    if 'conda-forge' not in channels:
        channels.append('conda-forge')
    out = {'name': param.conda_env,
           'channels': channels,
           'dependencies': deps}
    with open(fname_out, 'w') as fd:
        yaml.dump(out, fd, Dumper=yaml.SafeDumper)
    return out


def install_requirements(param, fname=None, req=None, add=None,
                         return_commands=False, **kwargs):
    r"""Install selected requirements on the current machine.

    Args:
        param (SetupParam): Setup parameters instance.
        fname (str, optional): Path to YAML/JSON file containing
            requirements. Defaults to 'yggdrasil/requirements.yaml'
            unless pyyaml is not installed and then json will be used.
        req (YggRequirements, optional): Existing set of requirements
            to use. If not provided, one will be created from fname
            and add.
        add (list, optional): Additional packages that should be
            installed. Defaults to None and is ignored.
        return_commands (bool, optional): If True, the commands
            necessary to install the dependencies are returned instead
            of running them. Defaults to False.
        **kwargs: Additional keyword arguments are passed to
            YggRequirements.select.

    Returns:
        list: Command resulting installation.

    """
    if req is None:
        file_kwargs = {'add': add}
        if ((isinstance(fname, list)
             or (isinstance(fname, str) and fname.endswith('.txt')))):
            req = YggRequirements.from_files(fname, **file_kwargs)
        else:
            req = YggRequirements.from_file(fname, **file_kwargs)
    kwargs.setdefault('for_setup', True)
    return req.select(param, **kwargs).install(
        param, return_commands=return_commands)


def prune(fname_in, fname_out=None, excl_method=None, incl_method=None,
          install_opts=None, additional_packages=[], skip_packages=[],
          verbose=False, return_list=False, dont_evaluate_markers=False,
          environment=None, skipped_mpi=None, param=None, **kwargs):
    r"""Prune a requirements.txt file to remove/select dependencies
    that are dependent on the current environment.

    Args:
        fname_in (str, list): Full path to one or more requirements
            files that should be read.
        fname_out (str, optional): Full path to requirements file that
            should be created. Defaults to None and is set to
            <fname_in[0]>_pruned.txt.
        excl_method (str, list, optional): Installation method(s) (pip
            or conda) that should be ignored. Defaults to None and is
            ignored.
        incl_method (str, list, optional): Installation method(s) (pip
            or conda) that should be installed (requirements without
            an installation method or with a different method will be
            ignored). Defaults to None and is ignored.
        additional_packages (list, optional): Additional packages that
            should be installed. Defaults to empty list. Versions
            specified here take precedence over versions in the
            provided files.
        skip_packages (list, optional): A list of packages that should
            not be added to the pruned list. Defaults to an empty
            list.
        verbose (bool, optional): If True, setup steps are run with
            verbosity turned up. Defaults to False.
        return_list (bool, optional): If True, return the list of
            requirements rather than writing it to a file. Defaults to
            False.
        dont_evaluate_markers (bool, optional): If True, don't check
            the pip-style markers when pruning (only those based on
            install_opts). Defaults to False.
        environment (dict, optional): Environment properties that
            should be used to evaluate pip-style markers. Defaults to
            None and the current environment will be used.
        skipped_mpi (list, optional): Existing list that skipped mpi
            packages should be added to. Defaults to False and is
            ignored.
        **kwargs: Additional keyword arguments are passed to
            SetupParam if param not provided.

    Returns:
        str: Full path to created file.

    """
    if param is None:
        if incl_method:
            kwargs.setdefault('method', incl_method)
        param = SetupParam(**kwargs)
    if not isinstance(fname_in, (list, tuple)):
        fname_in = [fname_in]
    skip_mpi = ('mpi4py' in skip_packages)
    mpi_pkgs = ['mpi4py', 'openmpi', 'mpich', 'msmpi', 'pytest-mpi']
    if isinstance(excl_method, str):
        excl_method = [excl_method]
    if skip_mpi:
        if not isinstance(skipped_mpi, list):
            skipped_mpi = []
        for x in mpi_pkgs:
            if x in skip_packages:
                skip_packages.remove(x)
    reqs = YggRequirementsList.from_files(
        fname_in, skip=skip_packages, add=additional_packages).select(
            param)
    if excl_method and not isinstance(excl_method, list, tuple):
        excl_method = [excl_method]
    if incl_method:
        if not isinstance(incl_method, (list, tuple)):
            incl_method = [incl_method]
        if not any(x == 'python' for x in incl_method):
            if not excl_method:
                excl_method = []
            excl_method.append('python')
    format_kws = dict(included_methods=incl_method,
                      excluded_methods=excl_method,
                      include_os=True, include_extra=True,
                      include_method=True)
    if skip_mpi:
        cpy = YggRequirementsList()
        mpi = YggRequirementsList()
        for x in reqs:
            if x.base_name in mpi_pkgs:
                mpi.append(x)
            else:
                cpy.append(x)
        skipped_mpi += mpi.format(**format_kws)
        reqs = cpy
    new_lines = reqs.format(**format_kws)
    if return_list:
        return new_lines
    # Write file
    if fname_out is None:
        if fname_in:
            fname_out = ('_pruned%s' % str(uuid.uuid4())).join(
                os.path.splitext(fname_in[0]))
        else:
            fname_out = ('pruned%s.txt' % str(uuid.uuid4()))
    if new_lines:
        with open(fname_out, 'w') as fd:
            fd.write('\n'.join(new_lines))
    if verbose:
        orig_lines = copy.copy(additional_packages)
        for x in fname_in:
            orig_lines += open(x, 'r').readlines()
        print(f'INSTALL OPTS:\n{pprint.pformat(install_opts)}')
        print('ORIGINAL DEP LIST:\n\t%s\nPRUNED DEP LIST:\n\t%s'
              % ('\n\t'.join([x.strip() for x in orig_lines]),
                 '\n\t'.join(new_lines)))
    return fname_out


if __name__ == "__main__":
    install_opts = get_install_opts(empty=True)
    parser = argparse.ArgumentParser(
        "Perform actions to manage yggdrasil's requirements.")
    subparsers = parser.add_subparsers(
        dest='operation',
        help="Requirements management operation to performed.")
    # List requirements
    parser_req = subparsers.add_parser(
        'select', help="Determine what dependencies are required.")
    SetupParam.add_parser_args(
        parser_req, install_opts=install_opts,
        skip=['conda-env', 'python'],
        skip_types=['install'],
        method_choices=['conda', 'pip', 'mamba',
                        'conda-dev', 'pip-dev', 'mamba-dev'],
        target_os_choices=['any', 'win', 'osx', 'linux'],
        target_os_default='any',
        additional_args=[
            (('--allow-missing', ),
             {'action': 'store_true',
              'help': "Ignore requirements with no valid options"}),
        ])
    # Create requirements
    parser_cre = subparsers.add_parser(
        'create', help="Create requirements files.")
    parser_cre.add_argument(
        'standard',
        choices=['conda', 'pip', 'extras_require', 'json',
                 'env', 'all'],
        help="Type of requirements file to create.")
    # Create a conda environment file
    parser_env = subparsers.add_parser(
        'env', help="Create a conda environment file.")
    SetupParam.add_parser_args(
        parser_env, install_opts=install_opts,
        env_name_default='env',
        skip_types=['run'],
        skip=['method', 'windows_package_manager', 'only_python',
              'use_mamba', 'fallback_to_conda', 'deps_method'],
        additional_args=[
            (('--filename', ),
             {'default': "environment.yml",
              'help': ("File where the environment yaml should be "
                       "saved.")}),
            (('--channels', '--channel', '-c'),
             {'nargs': '*',
              'help': "Name of conda channels that should be used."}),
            (('--additional-packages', ),
             {'nargs': '+',
              'help': "Additional packages that should be installed."}),
        ])
    # Install requirements
    parser_ins = subparsers.add_parser(
        'install', help="Install required dependencies.")
    SetupParam.add_parser_args(
        parser_ins, install_opts=install_opts,
        method_choices=['conda', 'pip', 'mamba',
                        'conda-dev', 'pip-dev', 'mamba-dev'],
        deps_method_default="supplemental",
        additional_args=[
            (('--files', ),
             {'nargs': '+',
              'help': 'One or more pip-style requirements files'}),
            (('--additional-packages', ),
             {'nargs': '+',
              'help': "Additional packages that should be installed."}),
            (('--allow-missing', ),
             {'action': 'store_true',
              'help': "Ignore requirements with no valid options"}),
        ])
    # Call methods
    args = parser.parse_args()
    if args.operation == 'select':
        param = SetupParam.from_args(args, install_opts)
        x = select_requirements(param,
                                allow_missing=args.allow_missing)
        pprint.pprint(x)
    elif args.operation == 'create':
        create_requirements(args.standard)
    elif args.operation == 'env':
        args.method = 'conda'
        args.deps_method = 'env'
        param = SetupParam.from_args(args, install_opts,
                                     env_created=True)
        create_environment_file(param, add=args.additional_packages,
                                channels=args.channels,
                                fname_out=args.filename)
    elif args.operation == 'install':
        # Use the version that takes the environment into account
        install_opts = get_install_opts()
        param = SetupParam.from_args(args, install_opts)
        x = install_requirements(
            param, fname=args.files, add=args.additional_packages,
            allow_missing=args.allow_missing)
        pprint.pprint(x)
    else:
        raise NotImplementedError(args.operation)
