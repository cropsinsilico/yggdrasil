import pytest
from tests import TestComponentBase as base_class
import collections
import numpy as np
import copy
from yggdrasil.communication import new_comm


@pytest.mark.usefixtures("pandas_equality_patch")
class TestTransformBase(base_class):
    r"""Test for TransformBase communication flass."""

    _component_type = 'transform'
    
    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, transform):
        r"""Subtype of component being tested."""
        return transform

    @pytest.fixture(scope="class", autouse=True)
    def transform(self, request):
        r"""str: Transformation being tested."""
        return request.param

    @pytest.fixture
    def testing_options(self, python_class, options):
        r"""Testing options."""
        if 'explicit_testing_options' in options:
            return copy.deepcopy(options['explicit_testing_options'])
        return python_class.get_testing_options(**options)
    
    @pytest.fixture
    def instance_kwargs(self, testing_options):
        r"""Keyword arguments for a new instance of the tested class."""
        out = {}
        if testing_options:
            out = dict(testing_options[0].get('kwargs', {}))
        return out

    @pytest.fixture(scope="class")
    def assert_iterator_equality(self, nested_approx):
        r"""Check for equality between iterators."""
        from collections.abc import Iterator

        def iterator_equality_w(a, b):
            if isinstance(a, Iterator) and isinstance(b, Iterator):
                assert(list(copy.deepcopy(a))
                       == nested_approx(list(copy.deepcopy(b))))
            else:
                assert(a == nested_approx(b))
        return iterator_equality_w

    def test_transform(self, python_class, testing_options,
                       assert_iterator_equality):
        r"""Test transform."""
        for x in testing_options:
            inst = python_class(**x.get('kwargs', {}))
            for msg_in, msg_exp in x.get('in/out', []):
                # if isinstance(msg_in, collections.abc.Iterator):
                #     msg_in0 = copy.deepcopy(msg_in)
                # else:
                #     msg_in0 = msg_in
                if isinstance(msg_exp, type(BaseException)):
                    with pytest.raises(msg_exp):
                        inst(msg_in)
                else:
                    msg_out = inst(msg_in)
                    assert_iterator_equality(msg_out, msg_exp)

    def test_transform_type(self, python_class, testing_options):
        r"""Test transform_type."""
        for x in testing_options:
            inst = python_class(**x.get('kwargs', {}))
            for typ_in, typ_exp in x.get('in/out_t', []):
                if isinstance(typ_exp, type(BaseException)):
                    with pytest.raises(typ_exp):
                        inst.validate_datatype(typ_in)
                else:
                    inst.validate_datatype(typ_in)
                    typ_out = inst.transform_datatype(typ_in)
                    assert(typ_out == typ_exp)

    def test_transform_empty(self, instance):
        r"""Test transform of empty bytes message."""
        assert(instance(b'', no_init=True) == b'')

    def test_send_comm(self, class_name, python_class, testing_options,
                       timeout, nested_approx):
        r"""Test transform within send comm."""
        if class_name in ['PandasTransform', 'ArrayTransform']:
            pytest.skip("Transformation negated on send")
        for x in testing_options:
            if (((not x.get('in/out', False))
                 or isinstance(x['in/out'][0][1],
                               type(BaseException)))):  # pragma: debug
                continue
            msg_in, msg_out = x['in/out'][0]
            send_comm = new_comm('test_send', reverse_names=True,
                                 direction='send', use_async=False,
                                 transform=[python_class(**x.get('kwargs', {}))])
            recv_comm = new_comm('test_recv', **send_comm.opp_comm_kwargs())
            if isinstance(msg_in, collections.abc.Iterator):
                msg_out_list = list(msg_out)
                msg_out = iter(msg_out_list)
            else:
                msg_out_list = [msg_out]
            try:
                for imsg_out in msg_out_list:
                    flag = send_comm.send(msg_in, timeout=timeout)
                    assert(flag)
                    if class_name in ['IterateTransform']:
                        for iimsg_out in imsg_out:
                            flag, msg_recv = recv_comm.recv(timeout=timeout)
                            assert(flag)
                            assert(msg_recv == nested_approx(iimsg_out))
                        msg_recv = imsg_out
                    elif ((class_name in ['FilterTransform'])
                          and isinstance(imsg_out, collections.abc.Iterator)):
                        assert(recv_comm.n_msg_recv == 0)
                        flag, msg_recv = recv_comm.recv(timeout=0.0)
                        assert(flag)
                        assert(msg_recv == b'')
                        msg_recv = imsg_out
                    elif ((class_name in ['MapFieldsTransform',
                                          'SelectFieldsTransform'])
                          and isinstance(imsg_out, np.ndarray)):
                        flag, msg_recv = recv_comm.recv_array(timeout=timeout)
                    else:
                        flag, msg_recv = recv_comm.recv(timeout=timeout)
                    assert(flag)
                    assert(msg_recv == nested_approx(imsg_out))
            finally:
                send_comm.close(linger=True)
                recv_comm.close(linger=True)
                send_comm.disconnect()
                recv_comm.disconnect()
                del send_comm
                del recv_comm

    def test_recv_comm(self, class_name, python_class, testing_options,
                       timeout, assert_iterator_equality):
        r"""Test transform within recv comm."""
        for x in testing_options:
            if (((not x.get('in/out', False))
                 or isinstance(x['in/out'][0][1],
                               type(BaseException)))):  # pragma: debug
                continue
            msg_in, msg_out = x['in/out'][0]
            send_comm = new_comm('test_send', reverse_names=True,
                                 direction='send', use_async=False)
            recv_comm = new_comm('test_recv',
                                 transform=[python_class(**x.get('kwargs', {}))],
                                 **send_comm.opp_comm_kwargs())
            if isinstance(msg_in, collections.abc.Iterator):
                msg_out_list = list(msg_out)
                msg_out = iter(msg_out_list)
            else:
                msg_out_list = [msg_out]
            try:
                flag = send_comm.send(msg_in, timeout=timeout)
                assert(flag)
                for imsg_out in msg_out_list:
                    if (((class_name in ['MapFieldsTransform',
                                         'SelectFieldsTransform'])
                         and isinstance(imsg_out, np.ndarray))):
                        flag, msg_recv = recv_comm.recv_array(timeout=timeout)
                    else:
                        flag, msg_recv = recv_comm.recv(timeout=timeout)
                    assert(flag)
                    assert_iterator_equality(msg_recv, imsg_out)
            finally:
                send_comm.close(linger=True)
                recv_comm.close(linger=True)
                send_comm.disconnect()
                recv_comm.disconnect()
                del send_comm
                del recv_comm
