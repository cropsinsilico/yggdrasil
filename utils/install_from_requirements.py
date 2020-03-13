# https://www.python.org/dev/peps/pep-0508/
from pip._vendor.packaging.requirements import Requirement, InvalidRequirement
import os
import sys
import argparse
import subprocess


def prune(fname_in, fname_out=None, excl_suffix=None):
    r"""Prune a requirements.txt file to remove/select dependencies that are
    dependent on the current environment.

    Args:
        fname_in (str, list): Full path to one or more requirements files that
            should be read.
        fname_out (str, optional): Full path to requirements file that should be
            created. Defaults to None and is set to <fname_in[0]>_pruned.txt.
        excl_suffix (str, optional): Lines ending in this string will be
            excluded. Defaults to None and is ignored.

    Returns:
        str: Full path to created file.

    """
    if not isinstance(fname_in, (list, tuple)):
        fname_in = [fname_in]
    new_lines = []
    for ifname_in in fname_in:
        with open(ifname_in, 'r') as fd:
            old_lines = fd.readlines()
        for line in old_lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            if excl_suffix and line.endswith(excl_suffix):
                continue
            try:
                req = Requirement(line.split('#')[0].strip())
                if req.marker and (not req.marker.evaluate()):
                    continue
                new_lines.append(req.name + str(req.specifier))
            except InvalidRequirement as e:
                print(e)
                continue
    # Write file
    if fname_out is None:
        fname_out = '_pruned'.join(os.path.splitext(fname_in[0]))
    with open(fname_out, 'w') as fd:
        fd.write('\n'.join(new_lines))
    return fname_out


def locate_conda_exe(conda_env, name):
    r"""Determine the full path to an executable in a specific conda environment.

    Args:
        conda_env (str): Name of conda environment that executable should be
            returned for.
        name (str): Name of the executable to locate.

    Returns:
        str: Full path to the executable.

    """
    conda_prefix = os.environ.get('CONDA_PREFIX', None)
    assert(conda_prefix)
    if os.path.dirname(conda_prefix).endswith('envs'):
        conda_prefix = os.path.dirname(conda_prefix)
    else:
        conda_prefix = os.path.join(conda_prefix, 'envs')
    if (sys.platform in ['win32', 'cygwin']):
        if not name.endswith('.exe'):
            name += '.exe'
        if name.startswith('python'):
            out = os.path.join(conda_prefix, conda_env, name)
        else:
            out = os.path.join(conda_prefix, conda_env,
                               'Scripts', name)
    else:
        out = os.path.join(conda_prefix, conda_env, 'bin', name)
    try:
        assert(os.path.isfile(out))
    except AssertionError:
        out = os.path.expanduser(os.path.join('~', '.conda', 'envs', name))
        if not os.path.isfile(out):
            raise
    return out


def install_from_requirements(method, fname_in, conda_env=None,
                              user=False):
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

    """
    if method not in ['pip', 'conda']:
        raise ValueError("Invalid method: '%s'" % method)
    elif method == 'pip':
        excl_suffix = '# conda'
    elif method == 'conda':
        excl_suffix = '# pip'
    temp_file = prune(fname_in, excl_suffix=excl_suffix)
    try:
        if method == 'conda':
            args = ['conda', 'install', '-y']
            if conda_env:
                args += ['--name', conda_env]
            args += ['--file', temp_file]
            if user:
                args.append('--user')
        elif method == 'pip':
            if conda_env:
                pip_cmd = locate_conda_exe(conda_env, 'pip')
            else:
                pip_cmd = 'pip'
            args = [pip_cmd, 'install', '-r', temp_file]
            if user:
                args.append('--user')
        print(subprocess.check_output(args).decode("utf-8"))
    finally:
        if os.path.isfile(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
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
    args = parser.parse_args()
    install_from_requirements(args.method, args.files, conda_env=args.conda_env,
                              user=args.user)
