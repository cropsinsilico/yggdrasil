import nose.tools as nt
from cis_interface import backwards
from cis_interface.backwards import unicode


def test_assert_bytes():
    r"""Ensure that the proper byte types are identified."""
    if backwards.PY2:  # pragma: Python 2
        # backwards.assert_bytes(bytearray('hello', 'utf-8'))
        backwards.assert_bytes('hello')
        nt.assert_raises(AssertionError, backwards.assert_bytes,
                         unicode('hello'))
    else:  # pragma: Python 3
        # backwards.assert_bytes(bytearray('hello', 'utf-8'))
        backwards.assert_bytes(b'hello')
        nt.assert_raises(AssertionError, backwards.assert_bytes,
                         'hello')

        
def test_assert_unicode():
    r"""Ensure that the proper unicode types are identified."""
    if backwards.PY2:  # pragma: Python 2
        # backwards.assert_unicode(unicode('hello'))
        # nt.assert_raises(AssertionError, backwards.assert_unicode, 'hello')
        backwards.assert_unicode('hello')
        nt.assert_raises(AssertionError, backwards.assert_unicode,
                         unicode('hello'))
        nt.assert_raises(AssertionError, backwards.assert_unicode,
                         bytearray('hello', 'utf-8'))
    else:  # pragma: Python 3
        backwards.assert_unicode('hello')
        nt.assert_raises(AssertionError, backwards.assert_unicode, b'hello')
        nt.assert_raises(AssertionError, backwards.assert_unicode,
                         bytearray('hello', 'utf-8'))

        
def test_bytes2unicode():
    r"""Ensure what results is proper bytes type."""
    if backwards.PY2:  # pragma: Python 2
        res = backwards.unicode_type('hello')
        backwards.assert_unicode(res)
        nt.assert_equal(backwards.bytes2unicode('hello'), res)
        nt.assert_equal(backwards.bytes2unicode(unicode('hello')), res)
        nt.assert_equal(backwards.bytes2unicode(bytearray('hello', 'utf-8')), res)
        nt.assert_raises(TypeError, backwards.bytes2unicode, 1)
    else:  # pragma: Python 3
        res = 'hello'
        backwards.assert_unicode(res)
        nt.assert_equal(backwards.bytes2unicode('hello'), res)
        nt.assert_equal(backwards.bytes2unicode(b'hello'), res)
        nt.assert_equal(backwards.bytes2unicode(bytearray('hello', 'utf-8')), res)
        nt.assert_raises(TypeError, backwards.bytes2unicode, 1)


def test_unicode2bytes():
    r"""Ensure what results is proper bytes type."""
    if backwards.PY2:  # pragma: Python 2
        res = backwards.bytes_type('hello')
        backwards.assert_bytes(res)
        nt.assert_equal(backwards.unicode2bytes('hello'), res)
        nt.assert_equal(backwards.unicode2bytes(unicode('hello')), res)
        nt.assert_equal(backwards.unicode2bytes(bytearray('hello', 'utf-8')), res)
        nt.assert_raises(TypeError, backwards.unicode2bytes, 1)
    else:  # pragma: Python 3
        res = backwards.bytes_type('hello', 'utf-8')
        backwards.assert_bytes(res)
        nt.assert_equal(backwards.unicode2bytes('hello'), res)
        nt.assert_equal(backwards.unicode2bytes(b'hello'), res)
        nt.assert_equal(backwards.unicode2bytes(bytearray('hello', 'utf-8')), res)
        nt.assert_raises(TypeError, backwards.unicode2bytes, 1)


def test_match_stype():
    r"""Test string type matching."""
    if backwards.PY2:  # pragma: Python 2
        slist = ['hello', bytearray('hello'), unicode('hello')]
    else:  # pragma: Python 3
        slist = ['hello', b'hello', bytearray('hello', 'utf-8')]
    for s1 in slist:
        for s2 in slist:
            nt.assert_equal(backwards.match_stype(s1, s2), s1)
    nt.assert_raises(TypeError, backwards.match_stype, 1, 'hello')


def test_format_bytes():
    r"""Test formating of bytes string."""
    s0 = "%s, %s"
    ans = "one, one"
    arg0 = "one"
    args = (backwards.unicode2bytes(arg0), backwards.bytes2unicode(arg0))
    for cvt in [backwards.unicode2bytes, backwards.bytes2unicode]:
        res = backwards.format_bytes(cvt(s0), args)
        nt.assert_equal(res, cvt(ans))
            

def test_encode_escape():
    r"""Test escape encoding."""
    s = 'hello\nhello'
    ans = 'hello\\nhello'
    nt.assert_equal(backwards.encode_escape(s), ans)

    
def test_decode_escape():
    r"""Test esscape decoding."""
    s = 'hello\\nhello'
    ans = 'hello\nhello'
    nt.assert_equal(backwards.decode_escape(s), ans)
