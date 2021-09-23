from yggdrasil.communication import CommBase


def test_registry():
    r"""Test registry of comm."""
    comm_class = 'CommBase'
    key = 'key1'
    value = None
    assert(not CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key))
    assert(CommBase.get_comm_registry(None) == {})
    assert(CommBase.get_comm_registry(comm_class) == {})
    CommBase.register_comm(comm_class, key, value)
    assert(key in CommBase.get_comm_registry(comm_class))
    assert(CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key, dont_close=True))
    CommBase.register_comm(comm_class, key, value)
    assert(not CommBase.unregister_comm(comm_class, key))
