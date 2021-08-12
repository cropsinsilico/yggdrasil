import os
from yggdrasil.languages.Python.YggInterface import YggRpcClient


def model_function(in_buf):
    # Get the number of threads from an environment variable set in the yaml
    nthreads = int(os.environ["NTHREAD"])
    for i in range(nthreads):
    
        # The global_scope keyword is required to ensure that the comm
        # persists between function calls
        rpc = YggRpcClient('server_client', global_scope=True)
        print("client(Python:%d): %s" % (i, in_buf))
        ret, result = rpc.call(in_buf)
        if not ret:
            raise RuntimeError('client(Python:%d): RPC CALL ERROR' % i)
        out_buf = result

    return out_buf
