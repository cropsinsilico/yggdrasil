import pprint
import collections
import numpy as np
import copy
from yggdrasil.tests import YggTestClass
from yggdrasil.communication import new_comm


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

    def assert_equal_msg(self, a, b, **kwargs):
        r"""Assert that two message are the same.

        Args:
            a (object): Message for comarison.
            b (object): Expected message.
            original (object, None): Original message.

        """
        try:
            if ((isinstance(a, collections.abc.Iterator)
                 and isinstance(b, collections.abc.Iterator))):
                self.assert_equal(list(copy.deepcopy(a)), list(copy.deepcopy(b)))
            else:
                self.assert_equal(a, b)
        except BaseException:  # pragma: debug
            labels = ['expected', 'out']
            values = [b, a]
            if 'original' in kwargs:
                labels.insert(0, 'in')
                values.insert(0, kwargs['original'])
            for t, x in zip(labels, values):
                print('%s:' % t)
                if isinstance(x, collections.abc.Iterator):
                    print('iter(%s)' % pprint.pformat(list(x)))
                else:
                    pprint.pprint(x)
            raise

    def test_transform(self):
        r"""Test transform."""
        for x in self.get_options():
            inst = self.import_cls(**x.get('kwargs', {}))
            for msg_in, msg_exp in x.get('in/out', []):
                if isinstance(msg_in, collections.abc.Iterator):
                    msg_in0 = copy.deepcopy(msg_in)
                else:
                    msg_in0 = msg_in
                if isinstance(msg_exp, type(BaseException)):
                    self.assert_raises(msg_exp, inst, msg_in)
                else:
                    msg_out = inst(msg_in)
                    self.assert_equal_msg(msg_out, msg_exp, original=msg_in0)

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
                    self.assert_equal_msg(typ_out, typ_exp, original=typ_in)

    def test_transform_empty(self):
        r"""Test transform of empty bytes message."""
        self.assert_equal(self.instance(b'', no_init=True), b'')

    def test_send_comm(self):
        r"""Test transform within send comm."""
        if self.transform in ['pandas', 'PandasTransform',
                              'array', 'ArrayTransform']:
            # These transformation are negated on send
            return
        for x in self.get_options():
            if (((not x.get('in/out', False))
                 or isinstance(x['in/out'][0][1],
                               type(BaseException)))):  # pragma: debug
                continue
            msg_in, msg_out = x['in/out'][0]
            send_comm = new_comm('test_send', reverse_names=True,
                                 direction='send', use_async=False,
                                 transform=[self.import_cls(**x.get('kwargs', {}))])
            recv_comm = new_comm('test_recv', **send_comm.opp_comm_kwargs())
            if isinstance(msg_in, collections.abc.Iterator):
                msg_out_list = list(msg_out)
                msg_out = iter(msg_out_list)
            else:
                msg_out_list = [msg_out]
            try:
                for imsg_out in msg_out_list:
                    flag = send_comm.send(msg_in, timeout=self.timeout)
                    assert(flag)
                    if self.transform in ['iterate', 'IterateTransform']:
                        for iimsg_out in imsg_out:
                            flag, msg_recv = recv_comm.recv(timeout=self.timeout)
                            assert(flag)
                            self.assert_equal_msg(msg_recv, iimsg_out,
                                                  original=msg_in)
                        msg_recv = imsg_out
                    elif ((self.transform in ['filter', 'FilterTransform'])
                          and isinstance(imsg_out, collections.abc.Iterator)):
                        assert(recv_comm.n_msg_recv == 0)
                        flag, msg_recv = recv_comm.recv(timeout=0.0)
                        assert(flag)
                        self.assert_equal_msg(msg_recv, b'', original=msg_in)
                        msg_recv = imsg_out
                    elif ((self.transform in ['map', 'MapFieldsTransform',
                                              'select_fields', 'SelectFieldsTransform'])
                          and isinstance(imsg_out, np.ndarray)):
                        flag, msg_recv = recv_comm.recv_array(timeout=self.timeout)
                    else:
                        flag, msg_recv = recv_comm.recv(timeout=self.timeout)
                    assert(flag)
                    self.assert_equal_msg(msg_recv, imsg_out,
                                          original=msg_in)
            finally:
                send_comm.close()
                recv_comm.close()

    def test_recv_comm(self):
        r"""Test transform within recv comm."""
        for x in self.get_options():
            if (((not x.get('in/out', False))
                 or isinstance(x['in/out'][0][1],
                               type(BaseException)))):  # pragma: debug
                continue
            msg_in, msg_out = x['in/out'][0]
            send_comm = new_comm('test_send', reverse_names=True,
                                 direction='send', use_async=False)
            recv_comm = new_comm('test_recv',
                                 transform=[self.import_cls(**x.get('kwargs', {}))],
                                 **send_comm.opp_comm_kwargs())
            if isinstance(msg_in, collections.abc.Iterator):
                msg_out_list = list(msg_out)
                msg_out = iter(msg_out_list)
            else:
                msg_out_list = [msg_out]
            try:
                flag = send_comm.send(msg_in, timeout=self.timeout)
                assert(flag)
                for imsg_out in msg_out_list:
                    if (((self.transform in ['map', 'MapFieldsTransform',
                                             'select_fields', 'SelectFieldsTransform'])
                         and isinstance(imsg_out, np.ndarray))):
                        flag, msg_recv = recv_comm.recv_array(timeout=self.timeout)
                    else:
                        flag, msg_recv = recv_comm.recv(timeout=self.timeout)
                    assert(flag)
                    self.assert_equal_msg(msg_recv, imsg_out, original=msg_in)
            finally:
                send_comm.close()
                recv_comm.close()
