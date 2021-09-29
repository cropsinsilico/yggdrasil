import numpy as np
import pandas as pd
from collections import OrderedDict
import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestRModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for RModelDriver."""

    driver = "RModelDriver"

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestRModelParam, self).inst_kwargs
        out.setdefault('interpreter_flags', ['--vanilla'])
        return out


class TestRModelDriverNoInit(TestRModelParam,
                             parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for RModelDriver without init."""

    def test_is_library_installed(self):
        r"""Test is_library_installed for invalid library."""
        self.assert_equal(
            self.import_cls.is_library_installed('invalid_unicorn'),
            False)

    def test_python2language(self):
        r"""Test python2language."""
        test_vars = [(np.string_('hello'), 'hello'),
                     ((np.string_('hello'), ), ('hello', )),
                     ([np.string_('hello')], ['hello']),
                     ({np.string_('hello'): np.string_('hello')},
                      {'hello': 'hello'}),
                     (OrderedDict([(np.string_('hello'), np.string_('hello'))]),
                      OrderedDict([('hello', 'hello')]))]
        test_vars.append((
            pd.DataFrame.from_dict({'a': np.zeros(5, dtype='int64')}),
            pd.DataFrame.from_dict({'a': np.zeros(5, dtype='int32')})))
        for a, b in test_vars:
            self.assert_equal(self.import_cls.python2language(a), b)

    def test_install_model_dependencies(self, deps=None):
        r"""Test install_model_dependencies."""
        if deps is None:
            deps = ['units', 'zeallot',
                    {'package': 'units', 'arguments': '-v'}]
        super(TestRModelDriverNoInit, self).test_install_model_dependencies(
            deps=deps)


class TestRModelDriverNoStart(TestRModelParam,
                              parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for RModelDriver without start."""
    pass


class TestRModelDriver(TestRModelParam,
                       parent.TestInterpretedModelDriver):
    r"""Test runner for RModelDriver."""
    pass
