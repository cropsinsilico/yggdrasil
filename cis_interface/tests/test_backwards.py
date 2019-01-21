from cis_interface.tests import assert_equal, assert_raises
from cis_interface import backwards


def test_assert_bytes():
    r"""Ensure that the proper byte types are identified."""
    valid = [b'hello']
    if backwards.PY2:  # pragma: Python 2
        valid += ['hello']
        invalid = [u'hello']
    else:  # pragma: Python 3
        valid += []
        invalid = ['hello', u'hello']
    for v in valid:
        backwards.assert_bytes(v)
    for v in invalid:
        assert_raises(AssertionError, backwards.assert_bytes, v)

        
def test_assert_unicode():
    r"""Ensure that the proper unicode types are identified."""
    valid = [u'hello']
    if backwards.PY2:  # pragma: Python 2
        valid += []
        invalid = ['hello', b'hello']
    else:  # pragma: Python 3
        valid += ['hello']
        invalid = [b'hello']
    for v in valid:
        backwards.assert_unicode(v)
    for v in invalid:
        assert_raises(AssertionError, backwards.assert_unicode, v)
        

def test_assert_str():
    r"""Ensure that the proper str types are identified."""
    valid = ['hello']
    if backwards.PY2:  # pragma: Python 2
        valid += [b'hello']
        invalid = [u'hello']
    else:  # pragma: Python 3
        valid += [u'hello']
        invalid = [b'hello']
    for v in valid:
        backwards.assert_str(v)
    for v in invalid:
        assert_raises(AssertionError, backwards.assert_str, v)
        

def test_as_str():
    r"""Ensure what results is proper str type."""
    res = 'hello'
    vals = ['hello', b'hello', u'hello', bytearray('hello', 'utf-8')]
    for v in vals:
        backwards.assert_str(res)
        assert_equal(backwards.as_str(v), res)
    assert_raises(TypeError, backwards.as_str, 1)
    
        
def test_as_unicode():
    r"""Ensure what results is proper bytes type."""
    res = u'hello'
    vals = ['hello', b'hello', u'hello', bytearray('hello', 'utf-8')]
    for v in vals:
        backwards.assert_unicode(res)
        assert_equal(backwards.as_unicode(v), res)
    assert_raises(TypeError, backwards.as_unicode, 1)


def test_as_bytes():
    r"""Ensure what results is proper bytes type."""
    res = b'hello'
    vals = ['hello', b'hello', u'hello', bytearray('hello', 'utf-8')]
    for v in vals:
        backwards.assert_bytes(res)
        assert_equal(backwards.as_bytes(v), res)
    assert_raises(TypeError, backwards.as_bytes, 1)


def test_match_stype():
    r"""Test string type matching."""
    slist = ['hello', b'hello', u'hello', bytearray('hello', 'utf-8')]
    for s1 in slist:
        for s2 in slist:
            assert_equal(backwards.match_stype(s1, s2), s1)
    assert_raises(TypeError, backwards.match_stype, 1, 'hello')


def test_format_bytes():
    r"""Test formating of bytes string."""
    s0 = "%s, %s"
    ans = "one, one"
    arg0 = "one"
    args = (backwards.as_bytes(arg0), backwards.as_unicode(arg0))
    for cvt in [backwards.as_bytes, backwards.as_unicode]:
        res = backwards.format_bytes(cvt(s0), args)
        assert_equal(res, cvt(ans))
            

def test_encode_escape():
    r"""Test escape encoding."""
    s = 'hello\nhello'
    ans = 'hello\\nhello'
    assert_equal(backwards.encode_escape(s), ans)

    
def test_decode_escape():
    r"""Test esscape decoding."""
    s = 'hello\\nhello'
    ans = 'hello\nhello'
    assert_equal(backwards.decode_escape(s), ans)
