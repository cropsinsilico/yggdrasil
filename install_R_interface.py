import os
import sys
import subprocess
PY_MAJOR_VERSION = sys.version_info[0]


def install_R_interface():
    r"""Attempt to install the R interface.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    root_dir = os.path.dirname(__file__)
    lang_dir = os.path.join(root_dir, 'yggdrasil', 'languages')
    kwargs = {'cwd': lang_dir}
    if sys.platform in ['win32', 'cygwin']:
        kwargs['shell'] = True
        R_cmd = ['call', os.path.join(lang_dir, 'install_interface_R.bat')]
    else:
        R_cmd = ['./install_interface_R.sh']
    try:
        R_proc = subprocess.check_output(R_cmd, **kwargs)
        if PY_MAJOR_VERSION == 3:
            R_proc = R_proc.decode("utf-8")
    except BaseException as e:
        print('Error installing R interface:\n%s' % e)
        return False
    return True


if __name__ == "__main__":
    out = install_R_interface()
    if out:
        print("R interface installed.")
    else:
        raise Exception("Failed to install R interface.")
