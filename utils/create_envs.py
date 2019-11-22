import os
import argparse
import subprocess
from install_from_requirements import locate_conda_exe
_utils_dir = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.dirname(_utils_dir)


def conda_env_exists(name):
    r"""Determine if a conda environment already exists.

    Args:
        name (str): Name of the environment to check.

    Returns:
        bool: True the the environment exits, False otherwise.

    """
    args = ['conda', 'info', '--envs']
    out = subprocess.check_output(args).decode("utf-8")
    envs = []
    for x in out.splitlines():
        if x.startswith('#') or (not x):
            continue
        envs.append(x.split()[0])
    return (name in envs)


def create_env(name, python='3.6', packages=None):
    r"""Create a new conda environment with the specified parameters.

    Args:
        name (str): Name of the environment being created.
        python (str, optional): Version of python that should be used. Defaults
            to '3.6'.
        packages (list, optional): Packages that should be installed in the new
            environment. Defaults to None and is ignored.

    """
    if conda_env_exists(name):
        print("Conda env with name '%s' already exists." % name)
        return
    if packages is None:
        packages = []
    if 'ipython' not in packages:
        packages.append('ipython')
    args = ['conda', 'create', '-y', '-n', name, 'python=%s' % python] + packages
    print('running', args)
    print(subprocess.check_output(args).decode("utf-8"))
    assert(conda_env_exists(name))


def create_devenv(env_type, python='3.6', name=None, **kwargs):
    r"""Create a new conda environment with the specified parameters with
    yggdrasil installed in development mode.

    Args:
        env_type (str): Type of environment that should be created, either
            'pip' or 'conda'.
        python (str, optional): Version of python that should be used. Defaults
            to '3.6'.
        name (str, optional): Name that should be given to the environment.
            Defaults to None and a name will be created from the provided
            values for env_type and python.
        **kwargs: Additional keyword arguments are passed to create_env.

    """
    assert(env_type in ['pip', 'conda'])
    if name is None:
        name = '%s%s' % (env_type, python.replace('.', ''))
    create_env(name, python=python, **kwargs)
    python_cmd = locate_conda_exe(name, 'python')
    req_suffixes = ['', '_testing', '_development']
    if env_type == 'conda':
        req_suffixes.append('_condaonly')
    elif env_type == 'pip':
        print(subprocess.check_output(['conda', 'install', '-y', '--name', name,
                                       'czmq', 'zeromq']).decode("utf-8"))
    req = [os.path.join(_pkg_dir, 'requirements%s.txt' % x)
           for x in req_suffixes]
    args = ([python_cmd, os.path.join(_utils_dir,
                                      'install_from_requirements.py'),
             '--conda-env', name, env_type] + req)
    print(subprocess.check_output(args).decode("utf-8"))
    # This is not called directly because it needs to be invoked with the
    # version of Python installed in the target environment
    # install_from_requirements(env_type, req, conda_env=name)
    print(subprocess.check_output([python_cmd, 'setup.py', 'develop'],
                                  cwd=_pkg_dir).decode("utf-8"))
    print("Created environment %s" % name)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Create dev environments for matrix of installation methods "
        "and Python versions.")
    parser.add_argument('--method', choices=['conda', 'pip', 'both'], default='both',
                        help=("Method(s) that should be used to install the "
                              "dependencies."))
    parser.add_argument('--version', '--python', default='2&3',
                        choices=['2.7', '3.6', '3.7', '3.8', '2&3'],
                        help=("Python version(s) to create environments for."))
    parser.add_argument('--name', default=None,
                        help=("Name of the conda env that should be created or "
                              "updated. If provided, 'method' will default to "
                              "'conda' and 'version' will default to '3.6'."))
    args = parser.parse_args()
    if args.method == 'both':
        if args.name:
            args.method = ['conda']
        else:
            args.method = ['pip', 'conda']
    else:
        args.method = [args.method]
    if args.version == '2&3':
        if args.name:
            args.version = ['3.6']
        else:
            args.version = ['2.7', '3.6']
    else:
        args.version = [args.version]
    for env_type in args.method:
        for python in args.version:
            create_devenv(env_type, python=python, name=args.name)
