import os
import re
import sys
import uuid
import tempfile
import subprocess
import logging
import argparse
import shutil
import toml
PY_MAJOR_VERSION = sys.version_info[0]
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


name_in_pragmas = 'Julia'
lang_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
pkg_dir = os.path.join(os.path.dirname(__file__), 'Yggdrasil')
proj_file = os.path.join(pkg_dir, 'Project.toml')
if sys.platform in ['win32', 'cygwin']:
    pkg_dir = pkg_dir.replace('\\', '\\\\')


def update_argparser(parser=None):
    r"""Update argument parser with language specific arguments.

    Args:
        parser (argparse.ArgumentParser, optional): Existing argument parser
            that should be updated. Default to None and a new argument parser
            will be created.

    Returns:
        argparse.ArgumentParser: Argument parser with language specific arguments.

    """
    if parser is None:
        parser = argparse.ArgumentParser("Run Julia installation script.")
    parser.add_argument('--skip-julia-requirements',
                        action='store_true',
                        help='Don\'t install Julia dependencies.')
    parser.add_argument('--update-julia-requirements',
                        action='store_true',
                        help='Update the Julia requirements.')
    return parser


def install_packages(package_list, update=False, into_pkg=None,
                     **kwargs):
    r"""Install Julia packages from Pkg.

    Args:
        package_list (str, list): One or more Julia packages that should be
            installed.
        update (bool, optional): If True, existing packages will be removed
            and then re-installed. If False, nothing will be done for existing
            packages. Defaults to False.
        into_pkg (str, optional): Directory for package that Julia packages
            should be added to.
        **kwargs: Additional keyword arguments are passed to call_julia.

    Returns:
        bool: True if call was successful, False otherwise.

    """
    julia_cmd = ['using Pkg']
    if not isinstance(package_list, list):
        package_list = [package_list]
    regex_ver = (r'(?P<name>.+?)\s*(?:\(\s*(?P<comparison>[=<>]+?)\s*'
                 r'(?P<ver>[^\s=<>]+?)\s*\))?')
    req_ver = []
    req_nover = []
    req_cmd = []
    for x in package_list:
        out = re.fullmatch(regex_ver, x).groupdict()
        kws = {}
        if out['ver'] and ('=' in out['comparison']):
            kws['ver'] = out['ver']
        if kws:
            kws['name'] = out['name']
            req_ver.append(kws)
        else:
            req_nover.append(out['name'])
    if req_nover:
        for x in req_nover:
            if update:
                req_cmd += [f'Pkg.update("{x}")']
            else:
                req_cmd += [f'Pkg.add("{x}")']
    if req_ver:
        for x in req_ver:
            name = "\"%s\"" % x['name']
            args = x.get('args', '')
            if 'ver' in x:
                if args:
                    args += ', '
                args += 'version=\"%s\"' % x['ver']
            if update:
                req_cmd += ['Pkg.rm(%s)' % name]
            req_cmd += ['Pkg.add(%s, %s)' % (name, args)]
    julia_cmd += req_cmd
    if into_pkg:
        julia_cmd.append(f'Pkg.activate(\"{into_pkg}\")')
        julia_cmd += req_cmd
    if not call_julia(julia_cmd, **kwargs):
        logger.error("Error installing dependencies: %s" % ', '.join(package_list))
        return False
    logger.info("Installed dependencies: %s" % ', '.join(package_list))
    return True

            
def call_julia(julia_cmd, **kwargs):
    r"""Call Julia commands, checking output.

    Args:
        julia_cmd (list): List of Julia commands to run.
        **kwargs: Additional keyword arguments are passed to make_call.

    Returns:
        bool: True if the call was successful, False otherwise.

    """
    kwargs['env'] = set_env(kwargs.get('env', None))
    julia_script = os.path.join(tempfile.gettempdir(),
                                'wrapper_%s.jl' % (
                                    str(uuid.uuid4()).replace('-', '_')))
    with open(julia_script, 'w') as fd:
        fd.write('\n'.join(julia_cmd))
        logger.info('Running:\n    ' + '\n    '.join(julia_cmd))
    try:
        julia_exe = shutil.which('julia')
        if not julia_exe:
            julia_exe = 'julia'
        out = make_call([julia_exe, julia_script], **kwargs)
    finally:
        os.remove(julia_script)
    return out


def set_env(env=None):
    r"""Set environment variables required to install yggdrasil package.

    Args:
        env (dict, optional): Dictionary to add environment variables to.

    Returns:
        dict: Updated dictionary.

    """
    if env is None:
        env = os.environ.copy()
    env['PYTHON'] = sys.executable
    julia_exe = shutil.which('julia')
    if ((julia_exe and env.get('CONDA_PREFIX', None)
         and julia_exe.startswith(env['CONDA_PREFIX'])
         and not env.get('JULIA_DEPOT_PATH', None))):
        env['JULIA_DEPOT_PATH'] = os.pathsep.join(
            [os.path.join(env['CONDA_PREFIX'], 'share', 'julia'), ''])
        env['JULIA_PROJECT'] = (
            f"@{os.path.basename(env['CONDA_PREFIX'])}")
        env['JULIA_LOAD_PATH'] = os.pathsep.join(
            ["@", env['JULIA_PROJECT'], "@stdlib"])
        env['CONDA_JL_HOME'] = env['CONDA_PREFIX']
        env['CONDA_JL_CONDA_EXE'] = env['CONDA_EXE']
        env['JULIA_SSL_CA_ROOTS_PATH'] = os.path.join(
            env['CONDA_PREFIX'], 'ssl', 'cacert.pem')
    return env


def make_call(julia_cmd, with_sudo=False, **kwargs):
    r"""Call command, checking output.

    Args:
        julia_cmd (list): List of command line executable to call and any
           arguments that should be passed to it.
        **kwargs: Additional keyword arguments are passed to subprocess.check_output.

    Returns:
        bool: True if the call was successful, False otherwise.

    """
    try:
        logger.info("Calling %s on %s"
                    % (' '.join(julia_cmd), sys.platform))
        if sys.platform in ['win32', 'cygwin']:
            kwargs.setdefault('shell', True)
        julia_proc = subprocess.check_output(julia_cmd, **kwargs)
        if PY_MAJOR_VERSION == 3:
            julia_proc = julia_proc.decode("utf-8")
        logger.info("Output:\n%s" % julia_proc)
        out = True
    except BaseException as e:
        logger.error('Error running Julia command:\n%s' % e)
        out = False
    return out


def requirements_from_project_toml(fname=None):
    r"""Read Julia requirements from the Imports & Depends sections of the
    package description.

    Args:
        fname (str, optional): Full path to the project toml. Defaults to
            proj_file.

    Returns:
        list: List of Julia requirements from the deps section.

    """
    if fname is None:
        fname = proj_file
    assert os.path.isfile(fname)
    contents = toml.load(fname)
    return list(contents['deps'].keys())


def install(args=None, skip_requirements=None, update_requirements=None):
    r"""Attempt to install the Julia interface.

    Args:
        args (argparse.Namespace, optional): Arguments parsed from the
            command line. Default to None and is created from sys.argv.
        skip_requirements (bool, optional): If True, the requirements will not
            be installed. Defaults to None and is set based on if the flag
            '--skip-julia-requirements' is in args.
        update_requirements (bool, optional): If True, the requirements will be
            updated. Defaults to False. Setting this to True, sets
            skip_requirements to False.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    # Parse input
    if args is None:
        args = update_argparser().parse_args()
    if skip_requirements is None:
        skip_requirements = args.skip_julia_requirements
    if update_requirements is None:
        update_requirements = args.update_julia_requirements
    if update_requirements:
        skip_requirements = False
    kwargs = {'cwd': lang_dir}
    for k in ['CONDA_PREFIX', 'CONDA_JL_HOME', 'CONDA_JL_CONDA_EXE',
              'JULIA_DEPOT_PATH', 'JULIA_LOAD_PATH', 'JULIA_PROJECT',
              'JULIA_SSL_CA_ROOTS_PATH']:
        print(f"Julia install: {k} = {os.environ.get(k, None)}")
    # Install requirements
    # TODO: Determine if develop calls install for deps
    requirements = requirements_from_project_toml()
    if not skip_requirements:
        if not install_packages(requirements, update=update_requirements,
                                into_pkg=pkg_dir, **kwargs):
            logger.error("Failed to install dependencies")
            return False
        logger.info("Installed dependencies.")
    # Check to see if yggdrasil installed
    # Build packages
    # build_cmd = ['using Pkg', 'Pkg.build(\"PyCall\")']
    # if not call_julia(build_cmd, **kwargs):
    #     logger.error("Error building Julia interface.")
    #     return False
    # logger.info("Built Julia interface.")
    # Install package
    if not call_julia(['using Pkg',
                       f'Pkg.develop(PackageSpec(path="{pkg_dir}"))']):
        logger.error("Error installing Julia interface.")
        return False
    # Check to see if Yggdrasil installed
    if not call_julia(['using Yggdrasil']):
        logger.error("Julia interface not installed.")
        return False
    logger.info("Installed Julia interface.")
    return True


if __name__ == "__main__":
    out = install()
    if out:
        logger.info("Julia interface installed.")
    else:
        raise Exception("Failed to install Julia interface.")
