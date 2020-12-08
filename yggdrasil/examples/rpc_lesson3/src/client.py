from yggdrasil.languages.Python.YggInterface import YggRpcClient


def model_function(in_buf):
    # The global_scope keyword is required to ensure that the comm persists
    # between function calls
    rpc = YggRpcClient('server_client', global_scope=True)
    print("client(Python): %s" % in_buf)
    ret, result = rpc.call(in_buf)
    if not ret:
        raise RuntimeError('client(Python): RPC CALL ERROR')
    out_buf = result
    return out_buf
