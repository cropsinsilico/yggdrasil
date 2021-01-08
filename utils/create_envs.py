import os
import argparse
from setup_test_env import create_env, install_pkg
_utils_dir = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.dirname(_utils_dir)


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
    create_env('conda', python=python, name=name, **kwargs)
    install_pkg('%s-dev' % env_type, python=python,
                conda_env=name, always_yes=True, only_python=True,
                fallback_to_conda=True)
    # python_cmd = locate_conda_exe(name, 'python')
    # req_suffixes = ['', '_testing', '_development']
    # if env_type == 'conda':
    #     req_suffixes.append('_condaonly')
    #     # TODO: Find a way to install pip-only packages into conda
    #     # environment
    # elif env_type == 'pip':
    #     req_suffixes.append('_piponly')
    #     print(call_conda_command(['conda', 'install', '-y', '--name', name,
    #                               'czmq', 'zeromq']))
    # req = [os.path.join(_pkg_dir, 'requirements%s.txt' % x)
    #        for x in req_suffixes]
    # args = ([python_cmd, os.path.join(_utils_dir,
    #                                   'install_from_requirements.py'),
    #          '--conda-env', name, env_type] + req)
    # print(call_conda_command(args))
    # # This is not called directly because it needs to be invoked with the
    # # version of Python installed in the target environment
    # # install_from_requirements(env_type, req, conda_env=name)
    # print(call_conda_command([python_cmd, 'setup.py', 'develop'],
    #                          cwd=_pkg_dir))
    # print("Created environment %s" % name)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Create dev environments for matrix of installation methods "
        "and Python versions.")
    parser.add_argument('--method', '--methods',
                        nargs='+', default=['conda', 'pip'],
                        choices=['conda', 'pip'],
                        help=("Method(s) that should be used to install the "
                              "dependencies."))
    parser.add_argument('--version', '--versions', '--python', '--pythons',
                        nargs='+', default=['3.6'],
                        choices=['3.6', '3.7', '3.8', '3.9'],
                        help=("Python version(s) to create environments for."))
    parser.add_argument('--name', default=None,
                        help=("Name of the conda env that should be created or "
                              "updated. If provided, 'method' will default to "
                              "'conda' and 'version' will default to '3.6'."))
    args = parser.parse_args()
    if args.name:
        args.method = ['conda']
        args.version = ['3.6']
    for env_type in args.method:
        for python in args.version:
            create_devenv(env_type, python=python, name=args.name)
