from yggdrasil.tests import YggTestClass


class TestFilterBase(YggTestClass):
    r"""Test for FilterBase communication flass."""

    filter = 'FilterBase'
    skip_comm_check = True
    
    @property
    def cls(self):
        r"""str: Communication class."""
        return self.filter

    @property
    def mod(self):
        r"""str: Absolute module import."""
        return 'yggdrasil.communication.filters.%s' % self.cls

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = {}
        opt = self.get_options()
        if opt:
            out = opt[0].get('kwargs', {})
        return out

    def test_filter(self):
        r"""Test filter."""
        for x in self.get_options():
            inst = self.import_cls(**x.get('kwargs', {}))
            for msg in x.get('pass', []):
                self.assert_equal(inst(msg), True)
            for msg in x.get('fail', []):
                self.assert_equal(inst(msg), False)
            for msg, err in x.get('error', []):
                self.assert_raises(err, inst, msg)
