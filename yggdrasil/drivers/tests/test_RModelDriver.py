import numpy as np
import pandas as pd
from collections import OrderedDict
import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestRModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for RModelDriver."""

    driver = "RModelDriver"


class TestRModelDriverNoInit(TestRModelParam,
                             parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for RModelDriver without init."""

    def test_is_library_installed(self):
        r"""Test is_library_installed for invalid library."""
        self.assert_equal(
            self.import_cls.is_library_installed('invalid_unicorn'),
            False)

    def test_language2python(self):
        r"""Test language2python."""
        test_vars = [('hello', b'hello'),
                     (b'hello', b'hello'),
                     (u'hello', b'hello'),
                     (('hello', ), (b'hello', )),
                     (['hello'], [b'hello']),
                     ({'a': 'hello'}, {'a': b'hello'})]
        for a, b in test_vars:
            self.assert_equal(self.import_cls.language2python(a), b)

    def test_python2language(self):
        r"""Test python2language."""
        test_vars = [('hello', 'hello'),
                     (b'hello', 'hello'),
                     (u'hello', 'hello'),
                     (np.string_('hello'), 'hello'),
                     ((b'hello', ), ('hello', )),
                     ([b'hello'], ['hello']),
                     ({b'a': b'hello'}, {'a': 'hello'}),
                     (OrderedDict([(b'a', b'hello')]),
                      OrderedDict([('a', 'hello')]))]
        test_vars.append((
            pd.DataFrame.from_dict({'a': np.zeros(5, dtype='int64'),
                                    'b': np.ones(5, dtype=bytes)}),
            pd.DataFrame.from_dict({'a': np.zeros(5, dtype='int32'),
                                    'b': np.ones(5, dtype=str)})))
        for a, b in test_vars:
            self.assert_equal(self.import_cls.python2language(a), b)


class TestRModelDriverNoStart(TestRModelParam,
                              parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for RModelDriver without start."""
    pass


class TestRModelDriver(TestRModelParam,
                       parent.TestInterpretedModelDriver):
    r"""Test runner for RModelDriver."""
    pass
