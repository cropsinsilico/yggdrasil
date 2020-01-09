import os
import sys
import uuid
import tempfile
import subprocess
import logging
import argparse
PY_MAJOR_VERSION = sys.version_info[0]
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


name_in_pragmas = 'R'
lang_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
desc_file = os.path.join(lang_dir, 'R', 'DESCRIPTION')


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
        parser = argparse.ArgumentParser("Run R installation script.")
    parser.add_argument('--sudoR', action='store_true', dest='sudo',
                        help='Run R installation steps with sudo.')
    parser.add_argument('--skip-r-requirements', '--skip_r_requirements',
                        action='store_true',
                        help='Don\'t install dependencies.')
    parser.add_argument('--update-r-requirements', '--update_r_requirements',
                        action='store_true',
                        help='Update the requirements.')
    return parser


def write_makevars(fname=None):
    r"""Write a makevars file with CC, CFLAGS, etc. values set based on the
    environment variables of the same name.

    Args:
        fname (str, optional): Full path to file where the files should be
            saved. Defaults to os.path.join("~", ".R", "Makevars").

    Returns:
        tuple(str, str): Full path to file where Makevars was written and the
            file indicated by the previous value of the R_MAKEVARS_USER
            environment variable. None is returned for either/both if a file is
            not written and/or the environment variable wasn't set.

    """
    if fname is None:
        fname = os.path.expanduser(os.path.join("~", ".R", "Makevars_temp"))
        if sys.platform in ['win32', 'cygwin']:
            fname += '.win'
    if os.path.isfile(fname):
        logger.info("Makevars file already exists: %s" % fname)
        return None, None
    lines = []
    for x in ['CC', 'CFLAGS', 'CXX', 'CXXFLAGS']:
        env = os.environ.get(x, '')
        if not env:
            continue
        lines.append('%s=%s' % (x, env))
    if lines:
        logger.info("Writing Makevars to %s" % fname)
        if not os.path.isdir(os.path.dirname(fname)):
            os.mkdir(os.path.dirname(fname))
        with open(fname, 'w') as fd:
            fd.write('\n'.join(lines))
        old_makevars = os.environ.get('R_MAKEVARS_USER', None)
        os.environ['R_MAKEVARS_USER'] = fname
        return fname, old_makevars
    else:
        logger.info("Nothing to be written to the Makevars file")
    return None, None


def restore_makevars(makevars, old_makevars):
    r"""Restore original makevars environemnt variable and remove temporary file.

    Args:
       makevars (str): Full path to the file where the temporary Makevars file
           was written. If None, nothing is done.
       old_makevars (str): Full path to the file where the old Makevars file
           is as defined by the environment variable R_MAKEVARS_USER.

    """
    if makevars is None:
        return
    if os.path.isfile(makevars):
        os.remove(makevars)
    if old_makevars:
        os.environ['R_MAKEVARS_USER'] = old_makevars
    else:
        if 'R_MAKEVARS_USER' in os.environ:
            del os.environ['R_MAKEVARS_USER']


def install_packages(package_list, update=False, repos=None, **kwargs):
    r"""Install R packages from CRAN.

    Args:
        package_list (str, list): One or more R packages that should be
            installed.
        update (bool, optional): If True, existing packages will be removed
            and then re-installed. If False, nothing will be done for existing
            packages. Defaults to False.
        repos (str, optional): Mirror where packages should be installed from.
            Defaults to 'http://cloud.r-project.org'.
        **kwargs: Additional keyword arguments are passed to call_R.

    Returns:
        bool: True if call was successful, False otherwise.

    """
    if not isinstance(package_list, list):
        package_list = [package_list]
    req_list = 'c(%s)' % ', '.join(['\"%s\"' % x for x in package_list])
    if repos is None:
        repos = 'http://cloud.r-project.org'
    if update:
        # R_cmd = ['install.packages(%s, repos="%s")' % (req_list, repos)]
        R_cmd = ['req <- %s' % req_list,
                 'for (x in req) {',
                 '  if (is.element(x, installed.packages()[,1])) {',
                 '    remove.packages(x)',
                 '  }',
                 '  install.packages(x, dep=TRUE, repos="%s")' % repos,
                 '}']
    else:
        R_cmd = ['req <- %s' % req_list,
                 'for (x in req) {',
                 '  if (!is.element(x, installed.packages()[,1])) {',
                 '    install.packages(x, dep=TRUE, repos="%s")' % repos,
                 '  } else {',
                 '    print(sprintf("%s already installed.", x))',
                 '  }',
                 '}']
    if not call_R(R_cmd, **kwargs):
        logger.error("Error installing dependencies: %s" % ', '.join(package_list))
        return False
    logger.info("Installed dependencies: %s" % ', '.join(package_list))
    return True

            
def call_R(R_cmd, **kwargs):
    r"""Call R commands, checking output.

    Args:
        R_cmd (list): List of R commands to run.
        **kwargs: Additional keyword arguments are passed to make_call.

    Returns:
        bool: True if the call was successful, False otherwise.

    """
    R_script = os.path.join(tempfile.gettempdir(),
                            'wrapper_%s.R' % (str(uuid.uuid4()).replace('-', '_')))
    with open(R_script, 'w') as fd:
        fd.write('\n'.join(R_cmd))
        logger.info('Running:\n    ' + '\n    '.join(R_cmd))
    try:
        out = make_call(['Rscript', R_script], **kwargs)
    finally:
        os.remove(R_script)
    return out


def make_call(R_cmd, with_sudo=False, **kwargs):
    r"""Call command, checking output.

    Args:
        R_cmd (list): List of command line executable to call and any arguments
           that should be passed to it.
        with_sudo (bool, optional): If True, the R installation script will be
            called with sudo. Defaults to False. Only valid for unix style
            operating systems.
        **kwargs: Additional keyword arguments are passed to subprocess.check_output.

    Returns:
        bool: True if the call was successful, False otherwise.

    """
    if with_sudo and (sys.platform not in ['win32', 'cygwin']):
        R_cmd.insert(0, 'sudo')
    try:
        logger.info("Calling %s on %s (with_sudo=%s)"
                    % (' '.join(R_cmd), sys.platform, with_sudo))
        R_proc = subprocess.check_output(R_cmd, **kwargs)
        if PY_MAJOR_VERSION == 3:
            R_proc = R_proc.decode("utf-8")
        logger.info("Output:\n%s" % R_proc)
        out = True
    except BaseException as e:
        logger.error('Error installing R interface:\n%s' % e)
        out = False
    return out


def requirements_from_description(fname=None):
    r"""Read R requirements from the Imports & Depends sections of the package
    description.

    Args:
        fname (str, optional): Full path to the description file. Defaults to
            desc_file.

    Returns:
        list: List of R requirements from the Imports & Depends sections.

    """
    out = []
    in_section = False
    if fname is None:
        fname = desc_file
    assert(os.path.isfile(fname))
    with open(fname, 'r') as fd:
        for x in fd.readlines():
            if x.startswith(('Imports:', 'Depends:')):
                in_section = True
            elif in_section:
                if x.startswith('  '):
                    out.append(x.strip().strip(','))
                else:
                    in_section = False
    out = list(set(out))
    return out


def install(args=None, with_sudo=None, skip_requirements=None,
            update_requirements=None):
    r"""Attempt to install the R interface.

    Args:
        args (argparse.Namespace, optional): Arguments parsed from the
            command line. Default to None and is created from sys.argv.
        with_sudo (bool, optional): If True, the R installation script will be
            called with sudo. Defaults to None and will be set based on args
            and environment variable YGG_USE_SUDO_FOR_R. Only valid for unix
            style operating systems.
        skip_requirements (bool, optional): If True, the requirements will not
            be installed. Defaults to None and is set based on if the flag
            '--skip-r-requirements' is in args.
        update_requirements (bool, optional): If True, the requirements will be
            updated. Defaults to False. Setting this to True, sets
            skip_requirements to False.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    # Parse input
    if args is None:
        args = update_argparser().parse_args()
    if with_sudo is None:
        with_sudo = ((os.environ.get('YGG_USE_SUDO_FOR_R', '0') == '1')
                     or args.sudo or ('sudo' in sys.argv))
        # or args.sudoR)
    if skip_requirements is None:
        skip_requirements = args.skip_r_requirements
    if update_requirements is None:
        update_requirements = args.update_r_requirements
    if update_requirements:
        skip_requirements = False
    # Set platform dependent things
    if sys.platform in ['win32', 'cygwin']:
        R_exe = 'R.exe'
    else:
        R_exe = 'R'
    kwargs = {'cwd': lang_dir, 'with_sudo': with_sudo}
    # Write Makevars for conda installation
    makevars = None
    old_makevars = None
    if os.environ.get('CONDA_PREFIX', ''):
        makevars, old_makevars = write_makevars()
    try:
        # Install requirements
        if not skip_requirements:
            requirements = requirements_from_description()
            if not install_packages(requirements, update=update_requirements, **kwargs):
                logger.error("Failed to install dependencies")
                restore_makevars(makevars, old_makevars)
                return False
            logger.info("Installed dependencies.")
        # Check to see if yggdrasil installed
        # Build packages
        build_cmd = [R_exe, 'CMD', 'build', 'R']
        if not make_call(build_cmd, **kwargs):
            logger.error("Error building R interface.")
            restore_makevars(makevars, old_makevars)
            return False
        logger.info("Built R interface.")
        # Install package
        package_name = 'yggdrasil_0.1.tar.gz'
        R_call = ("install.packages(\"%s\", verbose=TRUE,"
                  "repos=NULL, type=\"source\")") % package_name
        if not call_R([R_call], **kwargs):
            logger.error("Error installing R interface from the built package.")
            restore_makevars(makevars, old_makevars)
            return False
        logger.info("Installed R interface.")
    finally:
        restore_makevars(makevars, old_makevars)
    return True


if __name__ == "__main__":
    out = install()
    if out:
        logger.info("R interface installed.")
    else:
        raise Exception("Failed to install R interface.")
