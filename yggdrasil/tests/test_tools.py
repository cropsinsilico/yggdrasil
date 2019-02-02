import os
from yggdrasil import tools, platform
from yggdrasil.tests import YggTestClass, assert_equal


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


class TestYggClass(YggTestClass):
    r"""Test basic behavior of YggTestClass."""

    _cls = 'YggClass'
    _mod = 'yggdrasil.tools'

    def __init__(self, *args, **kwargs):
        super(TestYggClass, self).__init__(*args, **kwargs)
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list += ['name', 'sleeptime', 'longsleep', 'timeout']
        self._inst_kwargs = {'timeout': self.timeout,
                             'sleeptime': self.sleeptime}
        self.debug_flag = False

    def test_attributes(self):
        r"""Assert that the driver has all of the required attributes."""
        for a in self.attr_list:
            if not hasattr(self.instance, a):  # pragma: debug
                raise AttributeError("Driver does not have attribute %s" % a)

    def test_prints(self):
        r"""Test logging at various levels."""
        self.instance.display(1)
        self.instance.info(1)
        self.instance.debug(1)
        self.instance.verbose_debug(1)
        self.instance.critical(1)
        self.instance.warning(1)
        self.instance.error(1)
        self.instance.exception(1)
        try:
            raise Exception("Test exception")
        except Exception:
            self.instance.exception(1)
        self.instance.printStatus()
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = True
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = False

    def test_timeout(self):
        r"""Test functionality of timeout."""
        # Test w/o timeout
        self.instance.start_timeout(10, key='fake_key')
        assert(not self.instance.check_timeout(key='fake_key'))
        # Test errors
        self.assert_raises(KeyError, self.instance.start_timeout,
                           0.1, key='fake_key')
        self.instance.stop_timeout(key='fake_key')
        self.assert_raises(KeyError, self.instance.check_timeout)
        self.assert_raises(KeyError, self.instance.check_timeout, key='fake_key')
        self.assert_raises(KeyError, self.instance.stop_timeout, key='fake_key')
        # Test w/ timeout
        T = self.instance.start_timeout(0.001)  # self.instance.sleeptime)
        while not T.is_out:
            self.instance.sleep()
        assert(self.instance.check_timeout())
        self.instance.stop_timeout(quiet=True)
