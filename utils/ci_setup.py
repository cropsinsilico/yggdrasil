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
    if method == 'conda':
        cmds += [
            "echo Installing Python using conda...",
            # Configure conda
            "conda config --set always_yes yes --set changeps1 no",
            "conda config --set channel_priority strict",
            "conda config --add channels conda-forge",
            "conda update -q conda",
            "conda create -q -n test-environment python=%s" % python
        ]
    elif method == 'pip':
        if INSTALLLPY:
            setup_package_on_ci('conda', python)
        elif _is_osx:
            cmds.append("echo Installing Python using virtualenv...")
            if sys.version_info[0] != major:
                cmds.append('brew install python%d' % major)
            cmds += [
                "pip install --upgrade pip virtualenv",
                "virtualenv -p python%s venv" % python
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
    cmds = [
        # Check that we have the expected version of Python
        "python --version",
        # Upgrade pip and setuptools and wheel to get clean install
        "pip install --upgrade pip",
        "pip install --upgrade wheel",
        "pip install --upgrade setuptools",
        # Uninstall default numpy and matplotlib to allow installation
        # of specific versions
        "pip uninstall -y numpy",
        "pip uninstall -y matplotlib"
    ]
    install_req = os.path.join("utils", "install_from_requirements.py")
    if method == 'conda':
        cmds += [
            "conda install -q conda-build conda-verify",
            "conda info -a",
            "conda install %s %s %s" % (
                os.environ.get('NUMPY', 'numpy'),
                os.environ.get('MATPLOTLIB', 'matplotlib'),
                os.environ.get('JSONSCHEMA', 'jsonschema')),
            "python %s conda requirements_testing.txt" % install_req
        ]
        if BUILDDOCS:
            cmds.append(
                "python %s conda requirements_documentation.txt" % (
                    install_req))
        if INSTALLAPY:
            cmds += [
                "echo Installing AstroPy...",
                "conda install astropy"
            ]
        if INSTALLLPY:
            cmds += [
                "echo Installing LPy...",
                "conda install openalea.lpy boost=1.66.0 -c openalea"
            ]
        if INSTALLRMQ:
            cmds += [
                "echo Installing Pika...",
                "conda install \"pika<1.0.0b1\""
            ]
        # Temp fix to install missing dependencies from jsonschema
        if PY2:
            cmds.append("conda install contextlib2 pathlib2 "
                        "\"configparser >=3.5\"")
        index_dir = os.path.join("${CONDA_PREFIX}", "conda-bld")
        cmds += [
            # Install from conda build
            "conda build %s --python %s" % (
                os.path.join('recipe', 'meta.yaml'), PYVER),
            "conda index %s" % index_dir,
            "conda install -c file:/${CONDA_PREFIX}/conda-bld yggdrasil",
            "conda list"
        ]
    elif method == 'pip':
        # May need to uninstall conda version of numpy and matplotlib
        # on LPy test
        if _is_win:  # pragma: windows
            # Installing via pip causes import error
            cmds += [
                "conda install %NUMPY% scipy",
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
            "pip install -r requirements_testing.txt")
        if BUILDDOCS:
            cmds.append(
                "pip install -r requirements_documentation.txt")
        if INSTALLR:
            cmds.append("echo Installing R...")
            if INSTALLLPY or _is_win:
                cmds.append("conda install r-base")
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
            cmds += [
                "echo Installing LPy...",
                "conda install openalea.lpy boost=1.66.0 -c openalea"
            ]
        if INSTALLZMQ:
            cmds.append("echo Installing ZeroMQ...")
            if INSTALLLPY:
                cmds.append("conda install czmq zeromq")
            elif _is_linux:
                cmds.append("./ci/install-czmq-linux.sh")
            elif _is_osx:
                cmds.append("bash ci/install-czmq-osx.sh")
            elif _is_win:
                cmds.append("call ci\\install-czmq-windows.bat")
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
