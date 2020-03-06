import os
import sys
import argparse
import uuid
import pprint
import subprocess
PYVER = ('%s.%s' % sys.version_info[:2])
PY2 = (sys.version_info[0] == 2)
_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])
INSTALLLPY = (os.environ.get('INSTALLLPY', '0') == '1')
INSTALLR = (os.environ.get('INSTALLR', '0') == '1')
INSTALLAPY = (os.environ.get('INSTALLAPY', '0') == '1')
INSTALLZMQ = (os.environ.get('INSTALLZMQ', '0') == '1')
INSTALLRMQ = (os.environ.get('INSTALLRMQ', '0') == '1')
BUILDDOCS = (os.environ.get('BUILDDOCS', '0') == '1')


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
    if _is_win:
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
    

def deploy_package_on_ci(method):
    r"""Build and install the package and its dependencies on a CI
    resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.

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
        # Upgrade pip and setuptools and wheel to get clean install
        "pip install --upgrade wheel"
    ]
    if not _is_win:
        cmds += ["pip install --upgrade pip"]
    cmds += ["pip install --upgrade wheel"]
    if PY2:  # Python 2
        cmds.append("pip install setuptools==43.0.0")
    else:
        cmds.append("pip install --upgrade setuptools")
    cmds += [
        # Uninstall default numpy and matplotlib to allow installation
        # of specific versions
        "pip uninstall -y numpy",
        "pip uninstall -y matplotlib"
    ]
    install_req = os.path.join("utils", "install_from_requirements.py")
    if method == 'conda':
        cmds += [
            "%s install -q conda-build conda-verify %s %s %s" % (
                conda_cmd,
                os.environ.get('NUMPY', 'numpy'),
                os.environ.get('MATPLOTLIB', 'matplotlib'),
                os.environ.get('JSONSCHEMA', 'jsonschema')),
            "%s info -a" % conda_cmd,
            "python %s conda requirements_testing.txt" % install_req
        ]
        if BUILDDOCS:
            cmds.append(
                "python %s conda requirements_documentation.txt" % (
                    install_req))
        if INSTALLAPY:
            cmds += [
                "echo Installing AstroPy...",
                "%s install astropy" % conda_cmd
            ]
        if INSTALLLPY:
            cmds += [
                "echo Installing LPy...",
                "%s install openalea.lpy boost=1.66.0 -c openalea" % conda_cmd
            ]
        if INSTALLRMQ:
            cmds += [
                "echo Installing Pika...",
                "%s install \"pika<1.0.0b1\"" % conda_cmd
            ]
        # Temp fix to install missing dependencies from jsonschema
        if PY2:
            cmds.append(("%s install contextlib2 pathlib2 "
                         "\"configparser >=3.5\"") % conda_cmd)
        index_dir = os.path.join("${CONDA_PREFIX}", "conda-bld")
        cmds += [
            # Install from conda build
            "%s build %s --python %s" % (
                conda_cmd, os.path.join('recipe', 'meta.yaml'), PYVER),
            "%s index %s" % (conda_cmd, index_dir),
            "%s install -c file:/${CONDA_PREFIX}/conda-bld yggdrasil" % conda_cmd,
            "%s list" % conda_cmd
        ]
    elif method == 'pip':
        _in_conda = (_is_win or INSTALLLPY)
        # May need to uninstall conda version of numpy and matplotlib
        # on LPy test
        if _in_conda:
            # Installing via pip causes import error on Windows and
            # a conflict when installing LPy
            cmds += [
                "%s install %s scipy" % (
                    conda_cmd,
                    os.environ.get('NUMPY', 'numpy')),
                "pip install %s %s" % (
                    os.environ.get('MATPLOTLIB', 'matplotlib'),
                    os.environ.get('JSONSCHEMA', 'jsonschema'))
            ]
        else:
            cmds += [
                "pip install %s %s %s" % (
                    os.environ.get('NUMPY', 'numpy'),
                    os.environ.get('MATPLOTLIB', 'matplotlib'),
                    os.environ.get('JSONSCHEMA', 'jsonschema'))]
        cmds.append(
            "python %s pip requirements_testing.txt" % install_req)
        if BUILDDOCS:
            cmds.append(
                "python %s pip requirements_documentation.txt" % (
                    install_req))
        if INSTALLR:
            cmds.append("echo Installing R...")
            if _in_conda:
                cmds.append("%s install r-base" % conda_cmd)
            elif _is_linux:
                cmds += ["sudo apt-get install r-base",
                         "sudo apt-get install libudunits2-dev"]
            elif _is_osx:
                cmds += ["brew install r",
                         "brew install udunits"]
            else:
                raise NotImplementedError("Could not determine "
                                          "R installation method.")
            
        if INSTALLAPY:
            cmds += [
                "echo Installing AstroPy...",
                "pip install astropy"
            ]
        if INSTALLLPY:
            if not _in_conda:  # pragma: debug
                raise RuntimeError("Could not detect conda environment. "
                                   "Cannot proceed with a conda deployment "
                                   "(required for LPy).")
            cmds += [
                "echo Installing LPy...",
                "%s install openalea.lpy boost=1.66.0 -c openalea" % conda_cmd
            ]
        if INSTALLZMQ:
            cmds.append("echo Installing ZeroMQ...")
            if INSTALLLPY:
                cmds.append("%s install czmq zeromq" % conda_cmd)
            elif _is_linux:
                cmds.append("./ci/install-czmq-linux.sh")
            elif _is_osx:
                cmds.append("bash ci/install-czmq-osx.sh")
            elif _is_win:
                cmds += ["call ci\\install-czmq-windows.bat",
                         "echo \"%PATH%\""]
            else:
                raise NotImplementedError("Could not determine "
                                          "ZeroMQ installation method.")
        if INSTALLRMQ:
            cmds += [
                "echo Installing Pika...",
                "pip install \"pika<1.0.0b1\""
            ]
        cmds += [
            # Install from source dist
            "python setup.py sdist"
        ]
        if _is_win:  # pragma: windows
            cmds += [
                "for %%a in (\"dist\\*.tar.gz\") do set YGGSDIST=%%a",
                "echo %YGGSDIST%"
            ]
            sdist = "%YGGSDIST%"
        else:
            sdist = "dist/*.tar.gz"
        cmds += [
            "pip install --verbose %s" % sdist,
            "pip list",
            "python create_coveragerc.py"
        ]
        if _in_conda:
            cmds.append("%s list" % conda_cmd)
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
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
    args = parser.parse_args()
    if args.operation in ['env', 'setup']:
        setup_package_on_ci(args.method, args.python)
    elif args.operation == 'deploy':
        deploy_package_on_ci(args.method)
