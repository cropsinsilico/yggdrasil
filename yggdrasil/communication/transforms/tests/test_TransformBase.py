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
            for msg_in, msg_out in x.get('in/out', []):
                if isinstance(msg_out, type(BaseException)):
                    self.assert_raises(msg_out, inst, msg_in)
                else:
                    self.assert_equal(inst(msg_in), msg_out)

    def test_transform_type(self):
        r"""Test transform_type."""
        for x in self.get_options():
            inst = self.import_cls(**x.get('kwargs', {}))
            for typ_in, typ_out in x.get('in/out_t', []):
                self.assert_equal(inst.transform_datatype(typ_in),
                                  typ_out)
