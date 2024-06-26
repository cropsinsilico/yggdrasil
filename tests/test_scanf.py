import pytest
import itertools
from yggdrasil import scanf


@pytest.mark.parametrize(
    'fmt,val', [
        ("%g%+gj", complex(1)),
        ("%s", "hello"),
        ("%5s", "the"),
        (b"%s", b"hello"),
        ("%5s\t%ld\t%lf\t%lf%+lfj\n", ("one", 1, 1.0, complex(1, 1))),
        ("%ld", 1),
        ("%l64d", 1),
        ("%l64i", 1),
        ("%l64u", 1),
        ("%Lf", 1),
    ]
    + [(a + b, 1) for a, b in itertools.product(
        ["%", "%5.2", "%+5.2", "%-5.2", "% 5.2", "%05.2"],
        'dieEfFgGouxX'
    )]
    + [("%" + a + b, 1) for a, b in itertools.product(
        ['h', 'hh', 'l', 'll', 'j', 'z', 't'],
        ['d', 'i', 'u', 'o', 'x', 'X'])])
def test_scanf(fmt, val):
    r"""Test scanf."""
    if isinstance(val, tuple):
        val_tup = val
    else:
        val_tup = (val, )
    val_str = scanf.sprintf(fmt, *val_tup)
    # print(f"val_str = \"{val_str}\"")
    res = scanf.scanf(fmt, val_str)
    assert res == val_tup
