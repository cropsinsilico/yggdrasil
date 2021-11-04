import pytest
import os
import tempfile
from yggdrasil import tools, platform
from tests import TestClassBase as base_class


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
        assert(tools.bytes2str(x, recurse=True) == exp)


def test_str2bytes():
    r"""Test str2bytes."""
    vals = [('hello', b'hello'),
            (b'hello', b'hello'),
            (('a', 'b'), (b'a', b'b')),
            ({'a': 'a', 'b': 'b'}, {'a': b'a', 'b': b'b'}),
            (['a', 'b'], [b'a', b'b']),
            (['a', ['b', 'c']], [b'a', [b'b', b'c']])]
    for x, exp in vals:
        assert(tools.str2bytes(x, recurse=True) == exp)


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


def test_is_language_alias():
    r"""Test is_language_alias."""
    assert(tools.is_language_alias('c++', 'cpp'))
    assert(tools.is_language_alias('r', 'R'))
    assert(tools.is_language_alias('MATLAB', 'matlab'))
    

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
    assert(sout == sans[0])
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    with pytest.warns(RuntimeWarning):
        mout = tools.locate_file([mpat], show_alternates=True)
        assert(isinstance(mout, (bytes, str)))
        assert(mout == mans[0])
    

def test_find_all():
    r"""Test find_all."""
    # Missing file
    assert(not tools.find_all('missing_file.fake', 'invalid'))
    # Single file
    sdir, spat, sans = make_temp_single()
    sout = tools.find_all(spat, sdir)
    assert(isinstance(sout, list))
    assert(sout == sans)
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    mout = tools.find_all(mpat, mdir)
    assert(isinstance(mout, list))
    assert(mout == mans)


def test_locate_path():
    r"""Test file location."""
    # Search for current file
    fdir, fname = os.path.split(__file__)
    basedir = os.path.dirname(fdir)
    fpath = tools.locate_path(fname, basedir=basedir)
    assert(fpath)
    assert(__file__ in fpath)
    # assert(__file__ == fpath)
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
    assert(res == ans)
    # Test w/ shell
    if platform._is_win:  # pragma: windows
        args = 'cd'
    else:
        args = 'pwd'
    p = tools.popen_nobuffer(args, shell=True)
    out, err = p.communicate()
    res = tools.bytes2str(out).splitlines()[0]
    assert(res == ans)


def test_eval_kwarg():
    r"""Ensure strings & objects properly evaluated."""
    vals = [None, True, False, ['one', 'two'], 'one']
    for v in vals:
        assert(tools.eval_kwarg(v) == v)
        assert(tools.eval_kwarg(str(v)) == v)
    assert(tools.eval_kwarg("'one'") == 'one')
    assert(tools.eval_kwarg('"one"') == 'one')


class TestYggClass(base_class):
    r"""Test basic behavior of YggTestClass."""

    _cls = 'YggClass'
    _mod = 'yggdrasil.tools'

    @pytest.fixture
    def namespace(self, uuid):
        return f'TESTING_{uuid}'

    @pytest.fixture
    def instance_kwargs(self, timeout, polling_interval):
        r"""Keyword arguments for a new instance of the tested class."""
        return {'timeout': timeout,
                'sleeptime': polling_interval}
        
    def test_prints(self, instance):
        r"""Test logging at various levels."""
        instance.display(1)
        instance.info(1)
        instance.debug(1)
        instance.verbose_debug(1)
        instance.critical(1)
        instance.warning(1)
        instance.warn(1)
        instance.error(1)
        instance.exception(1)
        try:
            raise Exception("Test exception")
        except Exception:
            instance.exception(1)
        instance.printStatus()
        instance.printStatus(return_str=True)
        instance.special_debug(1)
        instance.suppress_special_debug = True
        instance.special_debug(1)
        instance.suppress_special_debug = False
        instance.interface_info(1)
        instance.language_info([])(1)
        instance.language_info('python')(1)

    def test_wait_on_function(self, instance):
        r"""Test functionality of async wait on function."""
        def func():
            return False
        instance.wait_on_function(func, timeout=0.0,
                                  polling_interval=0.0,
                                  quiet=True)

    def test_timeout(self, instance):
        r"""Test functionality of timeout."""
        # Test w/o timeout
        instance.start_timeout(10, key='fake_key')
        assert(not instance.check_timeout(key='fake_key'))
        # Test errors
        with pytest.raises(KeyError):
            instance.start_timeout(0.1, key='fake_key')
        instance.stop_timeout(key='fake_key')
        with pytest.raises(KeyError):
            instance.check_timeout()
        with pytest.raises(KeyError):
            instance.check_timeout(key='fake_key')
        with pytest.raises(KeyError):
            instance.stop_timeout(key='fake_key')
        # Test w/ timeout
        T = instance.start_timeout(0.001)  # instance.sleeptime)
        while not T.is_out:
            instance.sleep()
        assert(instance.check_timeout())
        instance.stop_timeout(quiet=True)
