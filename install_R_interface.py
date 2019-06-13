import os
import sys
import glob
import subprocess
PY_MAJOR_VERSION = sys.version_info[0]


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


def install_R_interface(with_sudo=False, skip_requirements=False):
    r"""Attempt to install the R interface.

    Args:
        with_sudo (bool, optional): If True, the R installation script will be
            called with sudo. Defaults to False. Only valid for unix style
            operating systems.
        skip_requirements (bool, optional): If True, the requirements will not
            be installed. Defaults to False.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    print("install_R_interface", sys.platform)
    root_dir = os.path.dirname(__file__)
    lang_dir = os.path.join(root_dir, 'yggdrasil', 'languages')
    if sys.platform in ['win32', 'cygwin']:
        R_exe = 'R.exe'
    else:
        R_exe = 'R'
    kwargs = {'cwd': lang_dir}
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
        R_cmd = [R_exe, '-e', R_call]
        # R -e 'install.packages(c("reticulate", "zeallot", "bit64"), repos="http://cloud.r-project.org")'
        if not make_call(R_cmd, with_sudo=with_sudo, **kwargs):
            return False
    # Install package
    if sys.platform in ['win32', 'cygwin']:
        # kwargs['shell'] = True
        # R_cmd = ['call', os.path.join(lang_dir, 'install_interface_R.bat')]
        R_cmd = [os.path.join(lang_dir, 'install_interface_R.bat')]
    else:
        R_cmd = ['./install_interface_R.sh']
    return make_call(R_cmd, with_sudo=with_sudo, **kwargs)


if __name__ == "__main__":
    out = install_R_interface(with_sudo=('sudo' in sys.argv),
                              skip_requirements=('--skip_requirements'
                                                 in sys.argv))
    if out:
        print("R interface installed.")
    else:
        raise Exception("Failed to install R interface.")
