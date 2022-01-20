# https://www.python.org/dev/peps/pep-0508/
from pip._vendor.packaging.requirements import Requirement, InvalidRequirement
import os
import re
import copy
import uuid
import pprint
import argparse
from setup_test_env import (
    call_conda_command, locate_conda_exe, get_install_opts,
    PYTHON_CMD, CONDA_CMD, _is_win)


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


def prune(fname_in, fname_out=None, excl_method=None, incl_method=None,
          install_opts=None, additional_packages=[], skip_packages=[],
          verbose=False, return_list=False, dont_evaluate_markers=False,
          environment=None):
    r"""Prune a requirements.txt file to remove/select dependencies that are
    dependent on the current environment.

    Args:
        fname_in (str, list): Full path to one or more requirements files that
            should be read.
        fname_out (str, optional): Full path to requirements file that should be
            created. Defaults to None and is set to <fname_in[0]>_pruned.txt.
        excl_method (str, optional): Installation method (pip or conda) that
            should be ignored. Defaults to None and is ignored.
        incl_method (str, optional): Installation method (pip or conda) that
            should be installed (requirements with without an installation method
            or with a different method will be ignored). Defaults to None and is
            ignored.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        additional_packages (list, optional): Additional packages that should
            be installed. Defaults to empty list. Versions specified here take
            precedence over versions in the provided files.
        skip_packages (list, optional): A list of packages that should not
            be added to the pruned list. Defaults to an empty list.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        return_list (bool, optional): If True, return the list of requirements
            rather than writing it to a file. Defaults to False.
        dont_evaluate_markers (bool, optional): If True, don't check the pip-
            style markers when pruning (only those based on install_opts).
            Defaults to False.
        environment (dict, optional): Environment properties that should be
            used to evaluate pip-style markers. Defaults to None and the
            current environment will be used.

    Returns:
        str: Full path to created file.

    """
    regex_constrain = r'(?:(?:pip)|(?:conda)|(?:[a-zA-Z][a-zA-Z0-9]*))'
    regex_comment = r'\s*\[\s*(?P<vals>%s(?:\s*\,\s*%s)*)\s*\]\s*' % (
        regex_constrain, regex_constrain)
    # regex_elem = r'(?P<val>%s)\s*(?:(?:\,)|(?:\]))' % regex_constrain
    install_opts = get_install_opts(install_opts)
    if not isinstance(fname_in, (list, tuple)):
        fname_in = [fname_in]
    packages = []
    new_lines = []
    orig_lines = copy.copy(additional_packages)
    for line in additional_packages:
        pkg = isolate_package_name(line)
        if pkg in packages:
            continue
        if pkg in skip_packages:
            continue
        new_lines.append(line)
        packages.append(pkg)
    for ifname_in in fname_in:
        with open(ifname_in, 'r') as fd:
            old_lines = fd.readlines()
            orig_lines += old_lines
        for line in old_lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            pkg = isolate_package_name(line)
            if pkg in packages:
                continue
            if pkg in skip_packages:
                continue
            packages.append(pkg)
            skip_line = False
            req_name = line
            if '#' in line:
                req_name, comment = line.split('#')
                m = re.fullmatch(regex_comment, comment)
                if m:
                    values = [x.strip() for x in m.group('vals').split(',')]
                    if verbose:
                        print('line: %s, values = %s, excl = %s, incl = %s'
                              % (line, values, excl_method, incl_method))
                    if excl_method and (excl_method in values):
                        continue
                    if incl_method and (incl_method not in values):
                        continue
                    for v in values:
                        if v not in ['pip', 'conda']:
                            if v not in install_opts:
                                raise RuntimeError("Unsupported install opt: '%s'" % v)
                            if not install_opts[v]:
                                skip_line = True
                                break
                elif incl_method:
                    skip_line = True
            elif incl_method:
                skip_line = True
            if skip_line:
                continue
            if dont_evaluate_markers:
                new_lines.append(req_name.strip())
                continue
            try:
                req = Requirement(req_name.strip())
                if ((req.marker
                     and (not req.marker.evaluate(environment=environment)))):
                    continue
                new_lines.append(req.name + str(req.specifier))
            except InvalidRequirement as e:
                print(e)
                continue
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
        print('INSTALL OPTS:\n%s' % pprint.pformat(install_opts))
        print('ORIGINAL DEP LIST:\n\t%s\nPRUNED DEP LIST:\n\t%s'
              % ('\n\t'.join([x.strip() for x in orig_lines]),
                 '\n\t'.join(new_lines)))
    return fname_out


def install_from_requirements(method, fname_in, conda_env=None,
                              user=False, unique_to_method=False,
                              python_cmd=None, install_opts=None,
                              verbose=False, verbose_prune=False,
                              additional_packages=[], skip_packages=[],
                              return_cmds=False, append_cmds=None,
                              temp_file=None):
    r"""Install packages via pip or conda from one or more pip-style
    requirements file(s).

    Args:
        method (str): Installation method; either 'pip' or 'conda'.
        fname_in (str, list): Full path to one or more requirements files that
            should be read.
        conda_env (str, optional): Name of conda environment that requirements
            should be installed into. Defaults to None and is ignored.
        user (bool, optional): If True, install in user mode. Defaults to
            False.
        unique_to_method (bool, optional): If True, only those packages that
            can only be installed via the specified method will be installed.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        python_cmd (str, optional): Python executable that should be used to
            call pip. Defaults to None and will be determined from conda_env if
            provided. Otherwise the current executable will be used.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        verbose_prune (bool, optional): If True, additional information will
            be printed when determine the list of requirements that should be
            installed. Defaults to False. If verbose is True, verbose_prune
            will be set to True as well.
        additional_packages (list, optional): Additional packages that should
            be installed. Defaults to empty list.
        skip_packages (list, optional): A list of packages that should not
            be added to the pruned list. Defaults to an empty list.
        return_cmds (bool, optional): If True, the necessary commands will be
            returned. Defaults to False.
        append_cmds (list, optional): List that commands should be appended to.
            Defaults to None and is ignored. If provided, the temporary file
            is returned. This keyword will be ignored if return_cmds is True.
        temp_file (str, optional): File where pruned requirements list should
            be stored. Defaults to None and one will be created.

    """
    if verbose:
        verbose_prune = True
    return_temp = (return_cmds or isinstance(append_cmds, list))
    install_opts = get_install_opts(install_opts)
    if python_cmd is None:
        python_cmd = PYTHON_CMD
    if conda_env:
        python_cmd = locate_conda_exe(conda_env, 'python')
    if method == 'pip':
        excl_method = 'conda'
    elif method == 'conda':
        excl_method = 'pip'
    else:
        raise ValueError("Invalid method: '%s'" % method)
    if unique_to_method:
        incl_method = method
    else:
        incl_method = None
    temp_file = prune(fname_in, fname_out=temp_file,
                      excl_method=excl_method, incl_method=incl_method,
                      install_opts=install_opts, verbose=verbose_prune,
                      additional_packages=additional_packages,
                      skip_packages=skip_packages)
    try:
        if method == 'conda':
            assert(CONDA_CMD)
            args = [CONDA_CMD, 'install', '-y']
            if verbose:
                args.append('-vvv')
            else:
                args.append('-q')
            if conda_env:
                args += ['--name', conda_env]
            args += ['--file', temp_file]
            if user:
                args.append('--user')
            args.append('--update-all')
        elif method == 'pip':
            assert(python_cmd)
            args = [python_cmd, '-m', 'pip', 'install']
            if verbose:
                args.append('--verbose')
            args += ['-r', temp_file]
            if user:
                args.append('--user')
        if return_temp:
            if return_cmds:
                cmd_list = []
            else:
                cmd_list = append_cmds
            if os.path.isfile(temp_file):
                cmd_list += [' '.join(args)]
                if _is_win:
                    cmd_list.append(
                        ('%s -c \'exec(\"import os;if os.path.isfile'
                         '(\\"%s\\"): os.remove(\\"%s\\")\")\'')
                        % (python_cmd, temp_file, temp_file))
                else:
                    cmd_list.append(
                        ('%s -c \'import os\nif os.path.isfile'
                         '(\"%s\"): os.remove(\"%s\")\'')
                        % (python_cmd, temp_file, temp_file))
        if return_cmds:
            return cmd_list
        if isinstance(append_cmds, list):
            return temp_file
        if os.path.isfile(temp_file):
            print(call_conda_command(args))
    except BaseException:
        if os.path.isfile(temp_file):
            with open(temp_file, 'r') as fd:
                print(fd.read())
        raise
    finally:
        if os.path.isfile(temp_file) and (not return_temp):
            os.remove(temp_file)


if __name__ == "__main__":
    install_opts = get_install_opts()
    parser = argparse.ArgumentParser(
        "Install dependencies via pip or conda from one or more "
        "pip-style requirements files.")
    parser.add_argument('method', choices=['conda', 'pip'],
                        help=("Method that should be used to install the "
                              "dependencies."))
    parser.add_argument('files', nargs='+',
                        help='One or more pip-style requirements files.')
    parser.add_argument('--conda-env', default=None,
                        help=('Conda environment that requirements should be '
                              'installed into.'))
    parser.add_argument('--user', action='store_true',
                        help=('Install in user mode.'))
    parser.add_argument('--unique-to-method', action='store_true',
                        help=('Only install packages that are unique to the specified '
                              'installation method.'))
    parser.add_argument('--verbose', action='store_true',
                        help="Turn up verbosity of output.")
    parser.add_argument('--additional-packages', nargs='+',
                        help="Additional packages that should be installed.")
    for k, v in install_opts.items():
        if v:
            parser.add_argument(
                '--dont-install-%s' % k, action='store_true',
                help=("Don't install %s" % k))
        else:
            parser.add_argument(
                '--install-%s' % k, action='store_true',
                help=("Install %s" % k))
    args = parser.parse_args()
    new_opts = {}
    for k, v in install_opts.items():
        if v and getattr(args, 'dont_install_%s' % k, False):
            new_opts[k] = False
        elif (not v) and getattr(args, 'install_%s' % k, False):
            new_opts[k] = True
    install_opts.update(new_opts)
    install_from_requirements(args.method, args.files, conda_env=args.conda_env,
                              user=args.user, unique_to_method=args.unique_to_method,
                              install_opts=install_opts, verbose=args.verbose,
                              additional_packages=args.additional_packages)
