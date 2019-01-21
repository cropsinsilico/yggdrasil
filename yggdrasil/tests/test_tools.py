import os
from yggdrasil import tools, platform  # , backwards
from yggdrasil.tests import assert_equal


def test_get_installed_lang():
    r"""Test get_installed_lang."""
    tools.get_installed_lang()


def test_get_installed_comm():
    r"""Test get_installed_comm."""
    tools.get_installed_comm()


def test_locate_path():
    r"""Test file location."""
    # Search for current file
    fdir, fname = os.path.split(__file__)
    basedir = os.path.dirname(fdir)
    fpath = tools.locate_path(fname, basedir=basedir)
    assert(fpath)
    assert(__file__ in fpath)
    # assert_equal(__file__, fpath)
    # Search for invalid file
    fname = 'invalid_file.ext'
    fpath = tools.locate_path(fname, basedir=basedir)
    assert(not fpath)


def test_popen_nobuffer():
    r"""Test open of process without buffer."""
    ans = os.getcwd()  # + '\n'
    # ans = backwards.as_bytes(ans)
    # Test w/o shell
    if platform._is_win:  # pragma: windows
        args = ['cmd', '/c', 'cd']
    else:
        args = ['pwd']
    p = tools.popen_nobuffer(args)
    out, err = p.communicate()
    res = out.decode('utf-8').splitlines()[0]
    assert_equal(res, ans)
    # Test w/ shell
    if platform._is_win:  # pragma: windows
        args = 'cd'
    else:
        args = 'pwd'
    p = tools.popen_nobuffer(args, shell=True)
    out, err = p.communicate()
    res = out.decode('utf-8').splitlines()[0]
    assert_equal(res, ans)


def test_eval_kwarg():
    r"""Ensure strings & objects properly evaluated."""
    vals = [None, True, False, ['one', 'two'], 'one']
    for v in vals:
        assert_equal(tools.eval_kwarg(v), v)
        assert_equal(tools.eval_kwarg(str(v)), v)
    assert_equal(tools.eval_kwarg("'one'"), 'one')
    assert_equal(tools.eval_kwarg('"one"'), 'one')
