import nose.tools as nt
from cis_interface import tools


def test_is_zmq_installed():
    r"""Test determination if zmq is installed or not."""
    tools.is_zmq_installed()
    

def test_is_ipc_installed():
    r"""Test determination if ipc is installed or not."""
    tools.is_ipc_installed()


def test_eval_kwarg():
    r"""Ensure strings & objects properly evaluated."""
    vals = [None, True, False, ['one', 'two'], 'one']
    for v in vals:
        nt.assert_equal(tools.eval_kwarg(v), v)
        nt.assert_equal(tools.eval_kwarg(str(v)), v)
    nt.assert_equal(tools.eval_kwarg("'one'"), 'one')
    nt.assert_equal(tools.eval_kwarg('"one"'), 'one')
