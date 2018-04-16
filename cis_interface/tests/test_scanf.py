import nose.tools as nt
from cis_interface import scanf


def test_scanf():
    r"""Test scanf."""
    num_codes = 'dieEfgGouxX'
    fmt_list = [("%g%+gj", complex(1)),
                ("%s", "hello"),
                ("%5s", "the"),
                ("%5s\t%ld\t%lf\t%lf%+lfj\n", ("one", 1, 1.0, complex(1, 1)))]
    fmt_list += [("%" + s, 1) for s in num_codes]
    fmt_list += [("%5.2" + s, 1) for s in num_codes]
    fmt_list += [("%+5.2" + s, 1) for s in num_codes]
    fmt_list += [("%-5.2" + s, 1) for s in num_codes]
    fmt_list += [("% 5.2" + s, 1) for s in num_codes]
    fmt_list += [("%05.2" + s, 1) for s in num_codes]
    for fmt, val in fmt_list:
        if isinstance(val, tuple):
            val_tup = val
        else:
            val_tup = (val, )
        new_tup = []
        for v in val_tup:
            if isinstance(v, complex):
                new_tup += [v.real, v.imag]
            else:
                new_tup.append(v)
        val_str = fmt % tuple(new_tup)
        res = scanf.scanf(fmt, val_str)
        nt.assert_equal(res, val_tup)
