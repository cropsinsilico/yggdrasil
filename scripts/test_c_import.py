import os
import subprocess


def dlltool_make_static(dll, dst=None, overwrite=False):
    r"""Create a static library from a DLL on windows using gendef and dlltool.

    Args:
        dll (str): Full path to the DLL file that should be converted.
        dst (str, optional): Full path to the location where the static file
            should be saved. Defaults to None and will be determined based on
            the path to dll.
        overwrite (bool, optional): If True, the static file will be created
            even if it already exists. Defaults to False.

    Returns:
        str: Full path to created static library.

    """
    # https://sourceforge.net/p/mingw-w64/wiki2/Answer%20generation%20of%20DLL
    # %20import%20library/
    base = os.path.splitext(os.path.basename(dll))[0]
    if not base.startswith('lib'):
        libbase = 'lib' + base
    else:
        libbase = base
    if dst is None:
        dst = libbase + '.a'
        # dst = os.path.join(os.path.dirname(dll), libbase + '.a')
    if (not os.path.isfile(dst)) or overwrite:
        cmds = [['gendef', dll],
                ['dlltool', '-D', dll, '-d', '%s.def' % base, '-l', dst]]
        for cmd in cmds:
            subprocess.check_call(cmd)
    assert(os.path.isfile(dst))
    return dst


# srcs = ['c:\\users\\meaga\\appdata\\local\\continuum\\miniconda3\\envs\\conda36\\library\\bin\\libzmq.dll',
# 	    'c:\\users\\meaga\\appdata\\local\\continuum\\miniconda3\\envs\\conda36\\library\\bin\\libczmq.dll',
# 	    'C:\\Users\\meaga\\AppData\\Local\\Continuum\\miniconda3\\envs\\conda36\\python36.dll']
srcs = ['python_wrapper.dll']
for src in srcs:
	print(dlltool_make_static(src))