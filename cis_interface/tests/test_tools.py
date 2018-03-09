import os
import nose.tools as nt
from cis_interface import tools, platform  # , backwards


def test_locate_path():
    r"""Test file location."""
    # Search for current file
    fdir, fname = os.path.split(__file__)
    basedir = os.path.dirname(fdir)
    fpath = tools.locate_path(fname, basedir=basedir)
    assert(fpath)
    assert(__file__ in fpath)
    # nt.assert_equal(__file__, fpath)
    # Search for invalid file
    fname = 'invalid_file.ext'
    fpath = tools.locate_path(fname, basedir=basedir)
    assert(not fpath)


def test_is_zmq_installed():
    r"""Test determination if zmq is installed or not."""
    tools.is_zmq_installed()
    

def test_is_ipc_installed():
    r"""Test determination if ipc is installed or not."""
    tools.is_ipc_installed()


def test_popen_nobuffer():
    r"""Test open of process without buffer."""
    ans = os.getcwd()  # + '\n'
    # ans = backwards.unicode2bytes(ans)
    # Test w/o shell
    if platform._is_win:  # pragma: windows
        args = ['cmd', '/c', 'cd']
    else:
        args = ['pwd']
    p = tools.popen_nobuffer(args)
    out, err = p.communicate()
    res = out.decode('utf-8').splitlines()[0]
    nt.assert_equal(res, ans)
    # Test w/ shell
    if platform._is_win:  # pragma: windows
        args = 'cd'
    else:
        args = 'pwd'
    p = tools.popen_nobuffer(args, shell=True)
    out, err = p.communicate()
    res = out.decode('utf-8').splitlines()[0]
    nt.assert_equal(res, ans)


def test_eval_kwarg():
    r"""Ensure strings & objects properly evaluated."""
    vals = [None, True, False, ['one', 'two'], 'one']
    for v in vals:
        nt.assert_equal(tools.eval_kwarg(v), v)
        nt.assert_equal(tools.eval_kwarg(str(v)), v)
    nt.assert_equal(tools.eval_kwarg("'one'"), 'one')
    nt.assert_equal(tools.eval_kwarg('"one"'), 'one')
