import os
import sys
import argparse
import uuid
import pprint
import shutil
import subprocess
PYVER = ('%s.%s' % sys.version_info[:2])
PY2 = (sys.version_info[0] == 2)
_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])
INSTALLLPY = (os.environ.get('INSTALLLPY', '0') == '1')
if _is_win:
    INSTALLC = (os.environ.get('INSTALLC', '0') == '1')
else:
    INSTALLC = True  # c compiler usually installed by default
INSTALLR = (os.environ.get('INSTALLR', '0') == '1')
INSTALLFORTRAN = (os.environ.get('INSTALLFORTRAN', '0') == '1')
if not INSTALLC:
    INSTALLFORTRAN = False
INSTALLSBML = (os.environ.get('INSTALLSBML', '0') == '1')
INSTALLAPY = (os.environ.get('INSTALLAPY', '0') == '1')
INSTALLZMQ = (os.environ.get('INSTALLZMQ', '0') == '1')
INSTALLRMQ = (os.environ.get('INSTALLRMQ', '0') == '1')
INSTALLTRIMESH = (os.environ.get('INSTALLTRIMESH', '0') == '1')
INSTALLPYGMENTS = (os.environ.get('INSTALLPYGMENTS', '0') == '1')
BUILDDOCS = (os.environ.get('BUILDDOCS', '0') == '1')


def call_conda_command(args, **kwargs):
    r"""Function for calling conda commands as the conda script is not
    available on subprocesses for windows unless invoked via the shell.

    Args:
        args (list): Command arguments.
        **kwargs: Additional keyword arguments are passed to subprocess.check_output.

    Returns:
        str: The output from the command.

    """
    if _is_win:
        args = ' '.join(args)
        kwargs['shell'] = True
    return subprocess.check_output(args, **kwargs).decode("utf-8")


def call_script(lines):
    r"""Write lines to a script and call it.

    Args:
        lines (list): Lines that should be written to the script.

    """
    if not lines:
        return
    if _is_win:  # pragma: windows
        script_ext = '.bat'
        error_check = 'if %errorlevel% neq 0 exit /b %errorlevel%'
        for i in range(len(lines), 0, -1):
            lines.insert(i, error_check)
    else:
        script_ext = '.sh'
        if lines[0] != '#!/bin/bash':
            lines.insert(0, '#!/bin/bash')
        error_check = 'set -e'
        if error_check not in lines:
            lines.insert(1, error_check)
    fname = 'ci_script_%s%s' % (str(uuid.uuid4()), script_ext)
    try:
        pprint.pprint(lines)
        with open(fname, 'w') as fd:
            fd.write('\n'.join(lines))
            
        call_kws = {}
        if _is_win:  # pragma: windows
            call_cmd = [fname]
        else:
            call_cmd = ['./%s' % fname]
            os.chmod(fname, 0o755)
        subprocess.check_call(call_cmd, **call_kws)
    finally:
        if os.path.isfile(fname):
            os.remove(fname)


def setup_package_on_ci(method, python):
    r"""Setup a test environment on a CI resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        python (str): Version of Python that should be tested.

    Raises:
        ValueError: If method is not 'conda' or 'pip'.

    """
    cmds = []
    major, minor = [int(x) for x in python.split('.')]
    if os.environ.get('GITHUB_ACTIONS', False):
        conda_cmd = '$CONDA/bin/conda'
    elif _is_win:
        conda_cmd = 'call conda'
    else:
        conda_cmd = 'conda'
    if method == 'conda':
        cmds += [
            "echo Installing Python using conda...",
            # Configure conda
            "%s config --set always_yes yes --set changeps1 no" % conda_cmd,
            # "%s config --set channel_priority strict" % conda_cmd,
            "%s config --add channels conda-forge" % conda_cmd,
            "%s update -q conda" % conda_cmd,
            # "%s config --set allow_conda_downgrades true" % conda_cmd,
            # "%s install -n root conda=4.9" % conda_cmd,
            "%s create -q -n test-environment python=%s" % (conda_cmd, python)
        ]
    elif method == 'pip':
        if INSTALLLPY or _is_win:
            setup_package_on_ci('conda', python)
        elif _is_osx:
            cmds.append("echo Installing Python using virtualenv...")
            pip_cmd = 'pip'
            if sys.version_info[0] != major:
                pip_cmd = 'pip%d' % major
                try:
                    call_script(['python%d --version' % major])
                except BaseException:
                    cmds.append('brew install python%d' % major)
            cmds += [
                "%s install --upgrade pip virtualenv" % pip_cmd,
                "virtualenv -p python%d venv" % major
            ]
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
    call_script(cmds)
    

def deploy_package_on_ci(method, verbose=False):
    r"""Build and install the package and its dependencies on a CI
    resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.

    Raises:
        ValueError: If method is not 'conda' or 'pip'.

    """
    if _is_win:
        conda_cmd = 'call conda'
    else:
        conda_cmd = 'conda'
    cmds = [
        # Check that we have the expected version of Python
        "python --version",
    ]
    # Upgrade pip and setuptools and wheel to get clean install
    upgrade_pkgs = ['wheel', 'setuptools']
    if not _is_win:
        upgrade_pkgs.insert(0, 'pip')
    cmds += ["pip install --upgrade %s" % ' '.join(upgrade_pkgs)]
    # Uninstall default numpy and matplotlib to allow installation
    # of specific versions
    cmds += ["pip uninstall -y numpy matplotlib"]
    # Get dependencies
    install_req = os.path.join("utils", "install_from_requirements.py")
    conda_pkgs = []
    pip_pkgs = []
    requirements_files = ['requirements_testing.txt']
    _in_conda = False
    if method == 'conda':
        _in_conda = True
        default_pkgs = conda_pkgs
    elif method == 'pip':
        _in_conda = (_is_win or INSTALLLPY)
        default_pkgs = pip_pkgs
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
    # Installing via pip causes import error on Windows and
    # a conflict when installing LPy
    conda_pkgs += ['scipy', os.environ.get('NUMPY', 'numpy')]
    default_pkgs += [os.environ.get('MATPLOTLIB', 'matplotlib'),
                     os.environ.get('JSONSCHEMA', 'jsonschema')]
    if INSTALLSBML:
        pip_pkgs.append('libroadrunner')
    if INSTALLAPY:
        default_pkgs.append('astropy')
    if INSTALLRMQ:
        default_pkgs.append("\"pika<1.0.0b1\"")
    if INSTALLTRIMESH:
        default_pkgs.append('trimesh')
    if INSTALLPYGMENTS:
        default_pkgs.append('pygments')
    if (method == 'pip') and _in_conda:
        if INSTALLR:
            conda_pkgs.append('r-base')
        if INSTALLFORTRAN:
            if _is_win:
                conda_pkgs += ['m2w64-gcc-fortran', 'make',
                               'm2w64-toolchain_win-64']
            else:
                conda_pkgs += ['fortran-compiler']
        if INSTALLZMQ:
            conda_pkgs += ['czmq', 'zeromq']
    if BUILDDOCS:
        requirements_files.append('requirements_documentation.txt')
    # Install dependencies
    if method == 'conda':
        cmds += [
            "%s install -q -n base conda-build conda-verify" % conda_cmd,
        ]
    elif method == 'pip':
        if INSTALLR and (not _in_conda):
            cmds.append("echo Installing R...")
            if _is_linux:
                cmds += [("sudo add-apt-repository 'deb https://cloud"
                          ".r-project.org/bin/linux/ubuntu xenial-cran35/'"),
                         ("sudo apt-key adv --keyserver keyserver.ubuntu.com "
                          "--recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9"),
                         "sudo apt update",
                         "sudo apt-get install r-base r-base-dev",
                         "sudo apt-get install libudunits2-dev"]
            elif _is_osx:
                cmds += ["brew install r",
                         "brew install udunits"]
            else:
                raise NotImplementedError("Could not determine "
                                          "R installation method.")
        if INSTALLFORTRAN and (not _in_conda):
            cmds.append("echo Installing Fortran...")
            if _is_linux:
                cmds += ["sudo apt-get install gfortran"]
            elif _is_osx:
                cmds += ["brew install gfortran"]
            else:
                raise NotImplementedError("Could not determine "
                                          "Fortran installation method.")
        if INSTALLZMQ and (not _in_conda):
            cmds.append("echo Installing ZeroMQ...")
            if _is_linux:
                cmds.append("./ci/install-czmq-linux.sh")
            elif _is_osx:
                cmds.append("bash ci/install-czmq-osx.sh")
            # elif _is_win:
            #     cmds += ["call ci\\install-czmq-windows.bat",
            #              "echo \"%PATH%\""]
            else:
                raise NotImplementedError("Could not determine "
                                          "ZeroMQ installation method.")
    if _in_conda:
        if conda_pkgs:
            cmds += ["%s install %s" % (conda_cmd, ' '.join(conda_pkgs))]
    else:
        pip_pkgs += conda_pkgs
    if pip_pkgs:
        cmds += ["pip install %s" % ' '.join(pip_pkgs)]
    for x in requirements_files:
        cmds += ["python %s %s %s" % (install_req, method, x)]
    if INSTALLLPY:
        if _in_conda:
            cmds += ["%s install openalea.lpy boost=1.66.0 -c openalea"
                     % conda_cmd]
        else:  # pragma: debug
            raise RuntimeError("Could not detect conda environment. "
                               "Cannot proceed with a conda deployment "
                               "(required for LPy).")
    # Install yggdrasil
    if method == 'conda':
        # Install from conda build
        # Assumes that an environment is active
        conda_prefix = os.environ.get('CONDA_PREFIX', None)
        if not conda_prefix:
            if os.environ.get('GITHUB_ACTIONS', False):
                conda_prefix = os.environ['CONDA']
            else:
                conda_prefix = shutil.which('conda')
        prefix_dir = os.path.dirname(os.path.dirname(conda_prefix))
        index_dir = os.path.join(prefix_dir, "conda-bld")
        if verbose:
            build_flags = ''
            install_flags = '-vvv'
        else:
            build_flags = '-q'
            install_flags = '-q'
        cmds += [
            "%s build %s --python %s %s" % (
                conda_cmd, 'recipe', PYVER, build_flags),
            "%s index %s" % (conda_cmd, index_dir),
            "%s install %s --use-local --update-deps yggdrasil" % (
                conda_cmd, install_flags),
            # "%s install %s --update-deps -c file:/%s/conda-bld yggdrasil" % (
            #     conda_cmd, install_flags, prefix_dir),
        ]
    elif method == 'pip':
        if verbose:
            build_flags = ''
            install_flags = '--verbose'
        else:
            build_flags = '--quiet'
            install_flags = ''
        # Install from source dist
        cmds += ["python setup.py %s sdist" % build_flags]
        if _is_win:  # pragma: windows
            cmds += [
                "for %%a in (\"dist\\*.tar.gz\") do set YGGSDIST=%%a",
                "echo %YGGSDIST%"
            ]
            sdist = "%YGGSDIST%"
        else:
            sdist = "dist/*.tar.gz"
        cmds += [
            "pip install %s %s" % (install_flags, sdist),
            "python create_coveragerc.py"
        ]
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
    # Print summary of what was installed
    cmds.append('pip list')
    if _in_conda:
        cmds.append("%s list" % conda_cmd)
    call_script(cmds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Perform setup operations to test package build and "
        "installation on continuous integration services.")
    parser.add_argument(
        'method', choices=['conda', 'pip'],
        help=("Method that should be used to build "
              "and install the packages and its "
              "dependencies."))
    subparsers = parser.add_subparsers(
        dest='operation',
        help="CI setup operation that should be performed.")
    parser_env = subparsers.add_parser(
        'env', help="Setup an environment for testing.")
    parser_env.add_argument(
        'python',
        help="Version of python that should be tested.")
    parser_dep = subparsers.add_parser(
        'deploy', help="Build and install package.")
    parser_dep.add_argument(
        '--verbose', action='store_true',
        help="Turn up verbosity of output from setup step.")
    args = parser.parse_args()
    if args.operation in ['env', 'setup']:
        setup_package_on_ci(args.method, args.python)
    elif args.operation == 'deploy':
        deploy_package_on_ci(args.method, verbose=args.verbose)
