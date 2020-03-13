import pprint
from yggdrasil.tests import YggTestClass


class TestTransformBase(YggTestClass):
    r"""Test for TransformBase communication flass."""

    transform = 'TransformBase'
    skip_comm_check = True
    
    @property
    def cls(self):
        r"""str: Communication class."""
        return self.transform

    @property
    def mod(self):
        r"""str: Absolute module import."""
        return 'yggdrasil.communication.transforms.%s' % self.cls

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = {}
        opt = self.get_options()
        if opt:
            out = opt[0].get('kwargs', {})
        return out

    def test_transform(self):
        r"""Test transform."""
        for x in self.get_options():
            inst = self.import_cls(**x.get('kwargs', {}))
            for msg_in, msg_exp in x.get('in/out', []):
                if isinstance(msg_exp, type(BaseException)):
                    self.assert_raises(msg_exp, inst, msg_in)
                else:
                    msg_out = inst(msg_in)
                    try:
                        self.assert_equal(msg_out, msg_exp)
                    except BaseException:  # pragma: debug
                        for t, x in zip(['in', 'expected', 'out'],
                                        [msg_in, msg_exp, msg_out]):
                            print('%s:' % t)
                            pprint.pprint(x)
                        raise

    def test_transform_type(self):
        r"""Test transform_type."""
        for x in self.get_options():
            inst = self.import_cls(**x.get('kwargs', {}))
            for typ_in, typ_exp in x.get('in/out_t', []):
                if isinstance(typ_exp, type(BaseException)):
                    self.assert_raises(typ_exp, inst.validate_datatype,
                                       typ_in)
                else:
                    inst.validate_datatype(typ_in)
                    typ_out = inst.transform_datatype(typ_in)
                    try:
                        self.assert_equal(typ_out, typ_exp)
                    except BaseException:  # pragma: debug
                        for t, x in zip(['in', 'expected', 'out'],
                                        [typ_in, typ_exp, typ_out]):
                            print('%s:' % t)
                            pprint.pprint(x)
                        raise

    def test_transform_empty(self):
        r"""Test transform of empty bytes message."""
        self.assert_equal(self.instance(b'', no_init=True), b'')
