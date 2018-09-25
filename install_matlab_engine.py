import os
import sys
import subprocess
PY_MAJOR_VERSION = sys.version_info[0]


def install_matlab(as_user=False):
    r"""Attempt to install the MATLAB engine API for Python.

    Arguments:
        as_user (bool, optional): If True, the install will be called with
            --user for a local install. Defaults to False.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    # Check to see if its already installed
    try:
        import matlab.engine
        return True
    except ImportError:
        pass
    # Get location of matlab root
    mtl_id = '=MATLABROOT='
    cmd = "fprintf('" + mtl_id + "%s" + mtl_id + "', matlabroot); exit();"
    mtl_cmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
               '-r', '%s' % cmd]
    try:
        mtl_proc = subprocess.check_output(mtl_cmd)
        if PY_MAJOR_VERSION == 3:
            mtl_proc = mtl_proc.decode("utf-8")
    except BaseException:
        return False
    if mtl_id not in mtl_proc:
        return False
    mtl_root = mtl_proc.split(mtl_id)[-2]
    # Install engine API
    mtl_setup = os.path.join(mtl_root, 'extern', 'engines', 'python')
    if not os.path.isdir(mtl_setup):
        return False
    blddir = os.path.join(os.path.expanduser('~'), 'matlab_python_api')
    if not os.path.isdir(blddir):
        os.mkdir(blddir)
    cmd = [sys.executable, 'setup.py',
           'build', '--build-base=%s' % blddir,
           'install']
    if '--user' in sys.argv:
        cmd.append('--user')
    try:
        result = subprocess.check_output(cmd, cwd=mtl_setup)
        if PY_MAJOR_VERSION == 3:
            result = result.decode("utf-8")
        print(result)
    except subprocess.CalledProcessError:
        return False
    return True


if __name__ == "__main__":
    out = install_matlab(as_user=('--user' in sys.argv))
    if out:
        print("MATLAB engine installed.")
    else:
        raise Exception("Failed to install MATLAB engine.")
