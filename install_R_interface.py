import os
import sys
import subprocess
PY_MAJOR_VERSION = sys.version_info[0]


def install_R_interface(with_sudo=False):
    r"""Attempt to install the R interface.

    Args:
        with_sudo (bool, optional): If True, the R installation script will be
            called with sudo. Defaults to False. Only valid for unix style
            operating systems.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    print("install_R_interface", sys.platform)
    root_dir = os.path.dirname(__file__)
    lang_dir = os.path.join(root_dir, 'yggdrasil', 'languages')
    kwargs = {'cwd': lang_dir}
    if sys.platform in ['win32', 'cygwin']:
        # kwargs['shell'] = True
        # R_cmd = ['call', os.path.join(lang_dir, 'install_interface_R.bat')]
        R_cmd = [os.path.join(lang_dir, 'install_interface_R.bat')]
    else:
        R_cmd = ['./install_interface_R.sh']
        if with_sudo:
            R_cmd.insert(0, 'sudo')
    try:
        print("Calling", R_cmd)
        R_proc = subprocess.check_output(R_cmd, **kwargs)
        if PY_MAJOR_VERSION == 3:
            R_proc = R_proc.decode("utf-8")
        print("output", R_proc)
    except BaseException as e:
        print('Error installing R interface:\n%s' % e)
        return False
    return True


if __name__ == "__main__":
    out = install_R_interface(with_sudo=('sudo' in sys.argv))
    if out:
        print("R interface installed.")
    else:
        raise Exception("Failed to install R interface.")
