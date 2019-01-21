from __future__ import print_function
import sys
import numpy as np
from yggdrasil.interface.YggInterface import (
    YggRpcClient, YggInput, YggOutput)


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCli: iterations = %d ' % iterations)

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    ymlfile = YggInput("yaml_in")
    rpc = YggRpcClient("rpcFibSrv_rpcFibCli", "%d", "%d %d")
    log = YggOutput("output_log")

    # Read entire contents of yaml
    ret, ycontent = ymlfile.recv()
    if not ret:
        raise RuntimeError('rpcFibCli(P): RECV ERROR')
    print('rpcFibCli: yaml has %d lines' % len(ycontent.split(b'\n')))

    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('rpcFibCli(P): fib(->%-2d) ::: ' % i, end='')
        ret, fib = rpc.rpcCall(np.int32(i))
        if not ret:
            raise RuntimeError('rpcFibCli(P): RPC CALL ERROR')

        # Log result by sending it to the log connection
        s = 'fib(%2d<-) = %-2d<-\n' % tuple(fib)
        print(s, end='')
        ret = log.send(s)
        if not ret:
            raise RuntimeError('rpcFibCli(P): SEND ERROR')

    print('Goodbye from Python rpcFibCli')

    
if __name__ == '__main__':
    fibClient(sys.argv[1:])
