import os
import tempfile
from yggdrasil import tools, platform
from yggdrasil.tests import YggTestClass, assert_equal, assert_warns


class DummyTarget(object):
    r"""Class to wrap for testing the ProxyObject class."""

    def __init__(self):
        self.b = 2

    def __call__(self, x):
        print(x)

    def __bytes__(self):
        return b'hello'

    def __hash__(self):
        return 1

    def __eq__(self, other):
        return True


class DummyProxyObject(tools.ProxyObject):
    r"""Class for testing corner cases of the ProxyObject."""

    __slots__ = ['a']

    def __init__(self, *args, **kwargs):
        self.a = 1
        super(DummyProxyObject, self).__init__(*args, **kwargs)


def test_ProxyObject():
    r"""Test corner casses of the ProxyObject class."""
    x = DummyProxyObject(DummyTarget())
    repr(x)
    str(x)
    bytes(x)
    bool(x)
    hash(x)
    x(1)
    assert(x == 1)
    for k in ['a', 'b']:
        delattr(x, k)
        assert(not hasattr(x, k))


def make_temp(fname_base, count=1):
    r"""Create temporary copies of same file with different extensions."""
    fname_base = fname_base.lower()
    tempdir = os.path.normcase(os.path.normpath(tempfile.gettempdir()))
    if (tempdir + os.pathsep) not in os.environ['PATH']:
        os.environ['PATH'] = os.pathsep.join([tempdir, os.environ.get('PATH')])
    fname_pattern = fname_base + '.*'
    fname = os.path.join(tempdir, fname_base)
    out = []
    for i in range(count):
        fname_i = '%s.%d' % (fname, i)
        out.append(fname_i)
        if not os.path.isfile(fname_i):
            with open(fname_i, 'w') as fd:
                fd.write('Test file %d' % i)
    return tempdir, fname_pattern, out


def make_temp_single():
    r"""Create single temporary file."""
    return make_temp('single_test_file')


def make_temp_multiple():
    r"""Create multiple temporary files."""
    return make_temp('multiple_test_file', count=2)


def test_bytes2str():
    r"""Test bytes2str."""
    vals = [(b'hello', 'hello'),
            ('hello', 'hello'),
            ((b'a', b'b'), ('a', 'b')),
            ({'a': b'a', 'b': b'b'}, {'a': 'a', 'b': 'b'}),
            ([b'a', b'b'], ['a', 'b']),
            ([b'a', [b'b', b'c']], ['a', ['b', 'c']])]
    for x, exp in vals:
        assert_equal(tools.bytes2str(x, recurse=True), exp)


def test_str2bytes():
    r"""Test str2bytes."""
    vals = [('hello', b'hello'),
            (b'hello', b'hello'),
            (('a', 'b'), (b'a', b'b')),
            ({'a': 'a', 'b': 'b'}, {'a': b'a', 'b': b'b'}),
            (['a', 'b'], [b'a', b'b']),
            (['a', ['b', 'c']], [b'a', [b'b', b'c']])]
    for x, exp in vals:
        assert_equal(tools.str2bytes(x, recurse=True), exp)


def test_timer_context():
    r"""Test timer_context."""
    with tools.timer_context("Test timeout: {elapsed}"):
        print("timer context body")


def test_display_source():
    r"""Test display_source."""
    fname = os.path.abspath(__file__)
    tools.display_source([fname], number_lines=True)
    tools.display_source([fname], return_lines=True)
    tools.display_source(test_display_source)
    fname_txt = os.path.join(tempfile.gettempdir(), 'unknown_example.invalid')
    with open(fname_txt, 'w') as fd:
        fd.write('hello')
    try:
        tools.display_source(fname_txt)
    finally:
        os.remove(fname_txt)


def test_display_source_diff():
    r"""Test display_source_diff."""
    fname1 = os.path.abspath(__file__)
    fname2 = os.path.join(tempfile.gettempdir(), os.path.basename(fname1))
    with open(fname1, 'r') as fd:
        lines = fd.read()
    with open(fname2, 'w') as fd:
        fd.write(lines[:int(len(lines) / 2)] + 'additional')
    try:
        tools.display_source_diff(fname1, fname2, number_lines=True)
        tools.display_source_diff(fname1, fname2, return_lines=True)
        tools.display_source_diff(test_display_source_diff,
                                  test_display_source_diff)
    finally:
        os.remove(fname2)


def test_get_shell():
    r"""Test get_shell."""
    tools.get_shell()


def test_in_powershell():
    r"""Test in_powershell."""
    tools.in_powershell()


def test_get_conda_prefix():
    r"""Test get_conda_prefix."""
    tools.get_conda_prefix()

    
def test_get_conda_env():
    r"""Test get_conda_env."""
    tools.get_conda_env()


def test_get_python_c_library():
    r"""Test get_python_c_library."""
    tools.get_python_c_library(allow_failure=True)
    

def test_get_supported():
    r"""Test get_supported_<platforms/lang/comm>."""
    tools.get_supported_platforms()
    tools.get_supported_lang()
    tools.get_supported_comm()


def test_get_installed():
    r"""Test get_installed_<lang/comm>."""
    tools.get_installed_lang()
    tools.get_installed_comm()


def test_is_comm_installed():
    r"""Test is_comm_installed for any."""
    assert(tools.is_comm_installed('zmq', language='any'))


def test_locate_file():
    r"""Test file location method."""
    # Missing file
    assert(not tools.locate_file('missing_file.fake'))
    assert(not tools.locate_file(['missing_file.fake']))
    # Single file
    sdir, spat, sans = make_temp_single()
    sout = tools.locate_file(spat, verification_func=os.path.isfile)
    assert(isinstance(sout, (bytes, str)))
    assert_equal(sout, sans[0])
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    with assert_warns(RuntimeWarning):
        mout = tools.locate_file([mpat])
        assert(isinstance(mout, (bytes, str)))
        assert_equal(mout, mans[0])
    

def test_find_all():
    r"""Test find_all."""
    # Missing file
    assert(not tools.find_all('missing_file.fake', 'invalid'))
    # Single file
    sdir, spat, sans = make_temp_single()
    sout = tools.find_all(spat, sdir)
    assert(isinstance(sout, list))
    assert_equal(sout, sans)
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    mout = tools.find_all(mpat, mdir)
    assert(isinstance(mout, list))
    assert_equal(mout, mans)


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
    # Test w/o shell
    if platform._is_win:  # pragma: windows
        args = ['cmd', '/c', 'cd']
    else:
        args = ['pwd']
    p = tools.popen_nobuffer(args)
    out, err = p.communicate()
    res = tools.bytes2str(out).splitlines()[0]
    assert_equal(res, ans)
    # Test w/ shell
    if platform._is_win:  # pragma: windows
        args = 'cd'
    else:
        args = 'pwd'
    p = tools.popen_nobuffer(args, shell=True)
    out, err = p.communicate()
    res = tools.bytes2str(out).splitlines()[0]
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
        self.instance.warn(1)
        self.instance.error(1)
        self.instance.exception(1)
        try:
            raise Exception("Test exception")
        except Exception:
            self.instance.exception(1)
        self.instance.printStatus()
        self.instance.printStatus(return_str=True)
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = True
        self.instance.special_debug(1)
        self.instance.suppress_special_debug = False
        self.instance.interface_info(1)
        self.instance.language_info([])(1)
        self.instance.language_info('python')(1)

    def test_wait_on_function(self):
        r"""Test functionality of async wait on function."""
        def func():
            return False
        self.instance.wait_on_function(func, timeout=0.0,
                                       polling_interval=0.0,
                                       quiet=True)

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
