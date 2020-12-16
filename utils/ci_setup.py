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
INSTALLZMQ = (os.environ.get('INSTALLZMQ', '0') == '1')
if not INSTALLC:
    INSTALLFORTRAN = False
    INSTALLZMQ = False
INSTALLSBML = (os.environ.get('INSTALLSBML', '0') == '1')
INSTALLAPY = (os.environ.get('INSTALLAPY', '0') == '1')
INSTALLRMQ = (os.environ.get('INSTALLRMQ', '0') == '1')
INSTALLTRIMESH = (os.environ.get('INSTALLTRIMESH', '0') == '1')
INSTALLPYGMENTS = (os.environ.get('INSTALLPYGMENTS', '0') == '1')
BUILDDOCS = (os.environ.get('BUILDDOCS', '0') == '1')
GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS', False)
CONDA_ENV = os.environ.get('CONDA_DEFAULT_ENV', None)
CONDA_PREFIX = os.environ.get('CONDA_PREFIX', None)
CONDA_INDEX = None
try:
    CONDA_CMD_WHICH = shutil.which('conda')
except AttributeError:
    if _is_win:
        CONDA_CMD_WHICH = None
    else:
        try:
            CONDA_CMD_WHICH = subprocess.check_output(
                ['which', 'conda']).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            CONDA_CMD_WHICH = None
if (not CONDA_PREFIX):
    if CONDA_CMD_WHICH:
        CONDA_PREFIX = os.path.dirname(os.path.dirname(CONDA_CMD_WHICH))
    elif GITHUB_ACTIONS and os.environ.get('CONDA', None):
        CONDA_PREFIX = os.environ['CONDA']
    if CONDA_PREFIX and (not CONDA_ENV):
        CONDA_ENV = 'base'
if ((isinstance(CONDA_PREFIX, str)
     and os.path.dirname(CONDA_PREFIX).endswith('envs'))):
    CONDA_PREFIX = os.path.dirname(os.path.dirname(CONDA_PREFIX))
if CONDA_PREFIX:
    CONDA_INDEX = os.path.join(CONDA_PREFIX, "conda-bld")
    if not os.path.isdir(CONDA_INDEX):
        if GITHUB_ACTIONS and _is_win and CONDA_PREFIX.endswith('Library'):
            CONDA_INDEX = os.path.join(os.path.dirname(CONDA_PREFIX),
                                       "conda-bld")
if CONDA_CMD_WHICH:
    if _is_win:
        CONDA_CMD = 'call conda'
    else:
        CONDA_CMD = 'conda'
elif os.environ.get('CONDA', None):
    if _is_win:
        CONDA_CMD = 'call %s' % os.path.join(os.environ['CONDA'],
                                             'condabin', 'conda.bat')
    else:
        CONDA_CMD = os.path.join(os.environ['CONDA'], 'bin', 'conda')
else:
    CONDA_CMD = None
SUMMARY_CMDS = ["python --version",
                "pip list"]
if CONDA_ENV:
    SUMMARY_CMDS += ["echo 'CONDA_PREFIX=%s'" % CONDA_PREFIX,
                     "%s info" % CONDA_CMD,
                     "%s list" % CONDA_CMD]


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
    if method == 'conda':
        cmds += [
            "echo Installing Python using conda...",
            # Configure conda
            "%s config --set always_yes yes --set changeps1 no" % CONDA_CMD,
            # "%s config --set channel_priority strict" % CONDA_CMD,
            "%s config --add channels conda-forge" % CONDA_CMD,
            "%s update -q conda" % CONDA_CMD,
            # "%s config --set allow_conda_downgrades true" % CONDA_CMD,
            # "%s install -n root conda=4.9" % CONDA_CMD,
            "%s create -q -n test-environment python=%s" % (CONDA_CMD, python)
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


def build_package_on_ci(method, python=None, return_commands=False,
                        verbose=False):
    r"""Build the package on a CI resource.

    Args:
        method (str): Method that should be used to build the package.
            Valid values include 'conda' and 'pip'.
        python (str, optional): Version of Python that package should be
            built for. Defaults to None if not provided and the current
            version of Python will be used.
        return_commands (bool, optional): If True, the commands necessary to
            build the package are returned instead of running them. Defaults
            to False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.

    """
    if python is None:
        python = PYVER
    cmds = SUMMARY_CMDS.copy()
    # Upgrade pip and setuptools and wheel to get clean install
    upgrade_pkgs = ['wheel', 'setuptools']
    if not _is_win:
        upgrade_pkgs.insert(0, 'pip')
    cmds += ["pip install --upgrade %s" % ' '.join(upgrade_pkgs)]
    if method == 'conda':
        assert(CONDA_INDEX and os.path.isdir(CONDA_INDEX))
        if verbose:
            build_flags = ''
        else:
            build_flags = '-q'
        # Must always build in base to avoid errors (and don't change the
        # version of Python used in the environment)
        # https://github.com/conda/conda/issues/9124
        # https://github.com/conda/conda/issues/7758#issuecomment-660328841
        assert(CONDA_ENV == 'base')
        if GITHUB_ACTIONS:
            cmds += [
                "%s config --add channels conda-forge" % CONDA_CMD,
                "%s update -q conda" % CONDA_CMD,
            ]
        if _is_win:
            cmds.append("%s clean --all" % CONDA_CMD)  # Might invalidate cache
            if GITHUB_ACTIONS:
                build_flags = ''
                build_flags += ' --no-test'
        cmds += [
            # "%s clean --all" % CONDA_CMD,  # Might invalidate cache
            # "%s deactivate" % CONDA_CMD,
            "%s install -q -n base conda-build conda-verify" % CONDA_CMD,
            "%s build %s --python %s %s" % (
                CONDA_CMD, 'recipe', python, build_flags),
            "%s index %s" % (CONDA_CMD, CONDA_INDEX),
            # "%s activate %s" % (CONDA_CMD, CONDA_ENV),
        ]
    elif method == 'pip':
        if verbose:
            build_flags = ''
        else:
            build_flags = '--quiet'
        # Install from source dist
        cmds += ["python setup.py %s sdist" % build_flags]
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
    # Print summary of what was installed
    cmds += SUMMARY_CMDS
    if return_commands:
        return cmds
    call_script(cmds)


def deploy_package_on_ci(method, python=None, without_build=False,
                         verbose=False, windows_package_manager='vcpkg'):
    r"""Build and install the package and its dependencies on a CI
    resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        python (str, optional): Version of Python that package should be
            built for. Defaults to None if not provided and the current
            version of Python will be used. This will be ignored if
            without_build is True.
        without_build (bool, optional): If True, the package will not be
            built prior to install. Defaults to False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        windows_package_manager (str, optional): Name of the package
            manager that should be used on windows. Defaults to 'vcpkg'.

    Raises:
        ValueError: If method is not 'conda' or 'pip'.

    """
    if without_build:
        cmds = SUMMARY_CMDS.copy()
    else:
        cmds = build_package_on_ci(method, python=python,
                                   return_commands=True, verbose=verbose)
    # Uninstall default numpy and matplotlib to allow installation
    # of specific versions
    cmds += ["pip uninstall -y numpy matplotlib"]
    # Get dependencies
    install_req = os.path.join("utils", "install_from_requirements.py")
    conda_pkgs = []
    pip_pkgs = []
    os_pkgs = []
    choco_pkgs = []
    vcpkg_pkgs = []
    requirements_files = ['requirements_testing.txt']
    _in_conda = False
    if method == 'conda':
        _in_conda = True
        default_pkgs = conda_pkgs
    elif method == 'pip':
        _in_conda = ((_is_win or INSTALLLPY) and (not GITHUB_ACTIONS))
        default_pkgs = pip_pkgs
    else:  # pragma: debug
        raise ValueError("Method must be 'conda' or 'pip', not '%s'"
                         % method)
    # Refresh channel
    # https://github.com/conda/conda/issues/8051
    if _in_conda and GITHUB_ACTIONS:
        cmds += [
            "%s config --set channel_priority strict" % CONDA_CMD,
            # "%s install -n root conda=4.9" % CONDA_CMD,
            # "%s config --set allow_conda_downgrades true" % CONDA_CMD,
            "%s config --remove channels conda-forge" % CONDA_CMD,
            "%s config --add channels conda-forge" % CONDA_CMD,
        ]
    # Installing via pip causes import error on Windows and
    # a conflict when installing LPy
    conda_pkgs += ['scipy', os.environ.get('NUMPY', 'numpy')]
    default_pkgs += [os.environ.get('MATPLOTLIB', 'matplotlib'),
                     os.environ.get('JSONSCHEMA', 'jsonschema')]
    if _is_linux:
        os_pkgs += ["strace", "valgrind"]
    # Valgrind failure:
    # "valgrind: This formula either does not compile or function as expected
    # on macOS versions newer than High Sierra due to an upstream
    # incompatibility."
    # elif _is_osx:
    #     os_pkgs += ["valgrind"]
    if INSTALLSBML:
        pip_pkgs.append('libroadrunner')
    if INSTALLAPY:
        default_pkgs.append('astropy')
    if INSTALLRMQ:
        default_pkgs.append("\"pika<1.0.0b1\"")
        # if _is_linux:
        #     os_pkgs.append("rabbitmq-server")
        # elif _is_osx:
        #     os_pkgs.append("rabbitmq")
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
        if not _in_conda:
            os_pkgs.append("doxygen")
    if GITHUB_ACTIONS and _is_linux and _in_conda:
        # Do both to ensure that the path is set for the installation
        # and in following steps
        cmds += [
            "export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH",
            "echo -n \"LD_LIBRARY_PATH=\" >> $GITHUB_ENV",
            "echo $CONDA_PREFIX/lib:$LD_LIBRARY_PATH >> $GITHUB_ENV"
        ]
    # Install dependencies
    if method == 'pip':
        if INSTALLR and (not _in_conda):
            if _is_linux:
                cmds += [("sudo add-apt-repository 'deb https://cloud"
                          ".r-project.org/bin/linux/ubuntu xenial-cran35/'"),
                         ("sudo apt-key adv --keyserver keyserver.ubuntu.com "
                          "--recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9")]
                os_pkgs += ["r-base", "r-base-dev", "libudunits2-dev"]
                os.environ['YGG_USE_SUDO_FOR_R'] = '1'
            elif _is_osx:
                os_pkgs += ["r", "udunits"]
            elif _is_win:
                choco_pkgs += ["r.project"]
            else:
                raise NotImplementedError("Could not determine "
                                          "R installation method.")
        if INSTALLFORTRAN and (not _in_conda):  # and (not _is_win):
            if _is_osx:
                os_pkgs.append("gcc")
            else:
                os_pkgs.append("gfortran")
        if INSTALLZMQ and (not _in_conda):
            cmds.append("echo Installing ZeroMQ...")
            if _is_linux:
                os_pkgs += ["libczmq-dev", "libzmq3-dev"]
            elif _is_osx:
                os_pkgs += ["czmq", "zmq"]
            elif _is_win:
                vcpkg_pkgs += ["czmq", "zeromq"]
            else:
                raise NotImplementedError("Could not determine "
                                          "ZeroMQ installation method.")
            # if _is_linux:
            #     cmds.append("./ci/install-czmq-linux.sh")
            # elif _is_osx:
            #     cmds.append("bash ci/install-czmq-osx.sh")
            # # elif _is_win:
            # #     cmds += ["call ci\\install-czmq-windows.bat",
            # #              "echo \"%PATH%\""]
            # else:
            #     raise NotImplementedError("Could not determine "
            #                               "ZeroMQ installation method.")
    if os_pkgs or (_is_win and (choco_pkgs or vcpkg_pkgs)):
        if _is_linux:
            cmds += ["sudo apt update"]
            cmds += ["sudo apt-get install %s" % ' '.join(os_pkgs)]
        elif _is_osx:
            if not _in_conda:
                cmds += ["brew uninstall --ignore-dependencies pkg-config"]
            cmds += ["brew install %s" % ' '.join(os_pkgs)]
        elif _is_win:
            if windows_package_manager == 'choco':
                choco_pkgs += os_pkgs
            elif windows_package_manager == 'vcpkg':
                vcpkg_pkgs += os_pkgs
            else:
                raise NotImplementedError("Invalid package manager: '%s'"
                                          % windows_package_manager)
            if choco_pkgs:
                cmds += ["choco install %s" % ' '.join(os_pkgs)]
            if vcpkg_pkgs:
                cmds += ["vcpkg.exe install %s" % ' '.join(os_pkgs)]
        else:
            raise NotImplementedError("No native package manager supported "
                                      "on Windows.")
    if _in_conda:
        if conda_pkgs:
            cmds += ["%s install %s" % (CONDA_CMD, ' '.join(conda_pkgs))]
    else:
        pip_pkgs += conda_pkgs
    if pip_pkgs:
        cmds += ["pip install %s" % ' '.join(pip_pkgs)]
    for x in requirements_files:
        cmds += ["python %s %s %s" % (install_req, method, x)]
    if INSTALLLPY:
        if _in_conda:
            cmds += ["%s install openalea.lpy boost=1.66.0 -c openalea"
                     % CONDA_CMD]
        else:  # pragma: debug
            raise RuntimeError("Could not detect conda environment. "
                               "Cannot proceed with a conda deployment "
                               "(required for LPy).")
    # Install yggdrasil
    if method == 'conda':
        assert(CONDA_INDEX and os.path.isdir(CONDA_INDEX))
        # Install from conda build
        # Assumes that the target environment is active
        if verbose:
            install_flags = '-vvv'
        else:
            install_flags = '-q'
        cmds += [
            "%s install %s --update-deps -c file:/%s yggdrasil" % (
                CONDA_CMD, install_flags, CONDA_INDEX),
            # Related issues if this stops working again
            # https://github.com/conda/conda/issues/466#issuecomment-378050252
        ]
    elif method == 'pip':
        if verbose:
            install_flags = '--verbose'
        else:
            install_flags = ''
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
    cmds += SUMMARY_CMDS
    call_script(cmds)


def verify_package_on_ci(method):
    r"""Verify that the package was installed correctly.

    Args:
        method (str): Method that was used to build and install
            the package. Valid values include 'conda' and 'pip'.

    """
    global INSTALLC, INSTALLFORTRAN
    if _is_win and (not INSTALLZMQ):
        INSTALLC = False
        INSTALLFORTRAN = False
    elif (not INSTALLFORTRAN) and shutil.which('gfortran'):
        INSTALLFORTRAN = True
    src_dir = os.path.join(os.getcwd(),
                           os.path.dirname(os.path.dirname(__file__)))
    src_version = subprocess.check_output(
        ["python", "-c",
         "'import versioneer; print(versioneer.get_version())'"],
        cwd=src_dir)
    bld_version = subprocess.check_output(
        ["python", "-c",
         "'import yggdrasil; print(yggdrasil.__version__)'"],
        cwd=os.path.dirname(src_dir))
    if src_version != bld_version:
        raise RuntimeError("Installed version does not match the version of "
                           "this source code.\n"
                           "\tSource version: %s\n\tBuild  version: %s"
                           % (src_version, bld_version))
    if INSTALLR:
        assert(shutil.which("R"))
        assert(shutil.which("Rscript"))
    subprocess.check_call(["flake8", "yggdrasil"], cwd=src_dir)
    if method == 'conda':
        subprocess.check_call(["python", "create_coveragerc.py"], cwd=src_dir)
    if not os.path.isfile(".coveragerc"):
        raise RuntimeError(".coveragerc file dosn't exist.")
    with open(".coveragerc", "r") as fd:
        print(fd.read())
    subprocess.check_call(["ygginfo", "--verbose"], cwd=src_dir)
    # Verify that languages are installed
    sys.stdout.flush()
    from yggdrasil.tools import is_lang_installed, is_comm_installed
    installed_lang = [(INSTALLC, 'c'),
                      (INSTALLR, 'R'),
                      (INSTALLFORTRAN, 'fortran'),
                      (INSTALLSBML, 'sbml'),
                      (INSTALLLPY, 'lpy')]
    installed_comm = [(INSTALLZMQ, 'zmq'),
                      (INSTALLRMQ, 'rmq')]
    errors = []
    for flag, name in installed_lang:
        if flag and (not is_lang_installed(name)):
            errors.append("Language '%s' should be installed, but is not."
                          % name)
        elif (not flag) and is_lang_installed(name):
            errors.append("Language '%s' should NOT be installed, but is."
                          % name)
    for flag, name in installed_comm:
        if name == 'rmq':
            language = 'python'  # rmq dosn't work for C
        else:
            language = None
        if flag and (not is_comm_installed(name, language=language)):
            errors.append("Comm '%s' should be installed, but is not." % name)
        elif (not flag) and is_comm_installed(name, language=language):
            errors.append("Comm '%s' should NOT be installed, but is." % name)
    if errors:
        raise AssertionError("One or more languages was not installed as "
                             "expected\n\t%s" % "\n\t".join(errors))
    if _is_win:  # pragma: windows
        for k in ['HOME', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH']:
            print('%s = %s' % (k, os.environ.get(k, None)))
        if os.environ.get('HOMEDRIVE', None):
            assert(os.path.expanduser('~').startswith(os.environ['HOMEDRIVE']))
        else:
            assert(os.path.expanduser('~').lower().startswith('c:'))


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
    parser_bld = subparsers.add_parser(
        'build', help="Build the package.")
    parser_bld.add_argument(
        '--python', default=None,
        help="Version of python that package should be built for.")
    parser_bld.add_argument(
        '--verbose', action='store_true',
        help="Turn up verbosity of output from build step.")
    parser_dep = subparsers.add_parser(
        'deploy', help="Build and install package.")
    parser_dep.add_argument(
        '--python', default=None,
        help="Version of python that package should be built/installed for.")
    parser_dep.add_argument(
        '--without-build', action='store_true',
        help=("Perform installation steps without building first. (Assumes "
              "the package has already been built)."))
    parser_dep.add_argument(
        '--verbose', action='store_true',
        help="Turn up verbosity of output from deploy step.")
    parser_ver = subparsers.add_parser(
        'verify', help="Verify that the package was installed correctly.")
    args = parser.parse_args()
    if args.operation in ['env', 'setup']:
        setup_package_on_ci(args.method, args.python)
    elif args.operation == 'build':
        build_package_on_ci(args.method, python=args.python,
                            verbose=args.verbose)
    elif args.operation == 'deploy':
        deploy_package_on_ci(args.method, python=args.python,
                             without_build=args.without_build,
                             verbose=args.verbose)
    elif args.operation == 'verify':
        verify_package_on_ci(args.method)
