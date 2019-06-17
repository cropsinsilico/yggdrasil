import os
import sys
import subprocess
import logging
PY_MAJOR_VERSION = sys.version_info[0]


name_in_pragmas = 'R'


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
        print("Calling", sys.platform, with_sudo, R_cmd)
        R_proc = subprocess.check_output(R_cmd, **kwargs)
        if PY_MAJOR_VERSION == 3:
            R_proc = R_proc.decode("utf-8")
        print("Output:\n%s" % R_proc)
        out = True
    except BaseException as e:
        print('Error installing R interface:\n%s' % e)
        out = False
    return out


def requirements_from_description(fname):
    r"""Read R requirements from the Imports & Depends sections of the package
    description.

    Args:
        fname (str): Full path to the description file.

    Returns:
        list: List of R requirements from the Imports & Depends sections.

    """
    out = []
    in_section = False
    with open(fname, 'r') as fd:
        for x in fd.readlines():
            if x.startswith(('Imports:', 'Depends:')):
                in_section = True
            elif in_section:
                if x.startswith('  '):
                    out.append(x.strip().strip(','))
                else:
                    in_section = False
    return out


def install(with_sudo=None, skip_requirements=None):
    r"""Attempt to install the R interface.

    Args:
        with_sudo (bool, optional): If True, the R installation script will be
            called with sudo. Defaults to None and will be set based on sys.argv
            and environment variable YGG_USE_SUDO_FOR_R. Only valid for unix
            style operating systems.
        skip_requirements (bool, optional): If True, the requirements will not
            be installed. Defaults to None and is set based on if the flag
            '--skip_requirements' is in sys.argv.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    # Parse input
    if with_sudo is None:
        with_sudo = (('sudo' in sys.argv) or ('--sudoR' in sys.argv)
                     or (os.environ.get('YGG_USE_SUDO_FOR_R', '0') == '1'))
    if skip_requirements is None:
        skip_requirements = ('--skip_requirements' in sys.argv)
    # Set platform dependent things
    lang_dir = os.path.dirname(os.path.dirname(__file__))
    if sys.platform in ['win32', 'cygwin']:
        R_exe = 'R.exe'
        # pkg_ext = '.zip'
    else:
        R_exe = 'R'
        # pkg_ext = '.tar.gz'
    kwargs = {'cwd': lang_dir, 'with_sudo': with_sudo}
    # Install requirements
    if not skip_requirements:
        desc_file = os.path.join(lang_dir, 'R', 'DESCRIPTION')
        assert(os.path.isfile(desc_file))
        requirements = requirements_from_description(desc_file)
        if (sys.platform in ['win32', 'cygwin']) and ('rtools' not in requirements):
            requirements.append('rtools')
        requirements = list(set(requirements))
        R_call = ('install.packages(c(%s), repos="http://cloud.r-project.org")'
                  % ', '.join(['\"%s\"' % x for x in requirements]))
        depend_cmd = [R_exe, '-e', R_call]
        if not make_call(depend_cmd, **kwargs):
            logging.error("Error installing dependencies.")
            return False
        logging.info("Installed dependencies.")
    # Build packages
    build_cmd = [R_exe, 'CMD', 'build', 'R']
    if not make_call(build_cmd, **kwargs):
        logging.error("Error building R interface.")
        return False
    logging.info("Built R interface.")
    # Install package
    package_name = 'yggdrasil_0.1.tar.gz'
    install_cmd = [R_exe, '-e',
                   ("'install.packages(\"%s\", "
                    "repos=NULL, type=\"source\")'") % package_name]
    # if sys.platform in ['win32', 'cygwin']:
    #     install_cmd = [R_exe, '-e',
    #                    ("'install.packages(\"%s\", "
    #                     "repos=NULL, type=\"source\")'") % package_name]
    # else:
    #     install_cmd = [R_exe, 'CMD', 'INSTALL', package_name]
    if not make_call(install_cmd, **kwargs):
        logging.error("Error installing R interface from the built package.")
        return False
    logging.info("Installed R interface.")
    return True


if __name__ == "__main__":
    out = install()
    if out:
        print("R interface installed.")
    else:
        raise Exception("Failed to install R interface.")
