from __future__ import print_function
import sys
import numpy as np
from yggdrasil.interface.YggInterface import YggRpcClient


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCliPar: iterations = %d' % iterations)

    # Create RPC connection with server
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = YggRpcClient("rpcFibSrv_rpcFibCliPar", "%d", "%d %d")

    # Send all of the requests to the server
    for i in range(1, iterations + 1):
        print('rpcFibCliPar(P): fib(->%-2d) ::: ' % i)
        ret = rpc.rpcSend(np.int32(i))
        if not ret:
            raise RuntimeError('rpcFibCliPar(P): SEND FAILED')

    # Receive responses for all requests that were sent
    for i in range(1, iterations + 1):
        ret, fib = rpc.rpcRecv()
        if not ret:
            raise RuntimeError('rpcFibCliPar(P): RECV FAILED')
        print('rpcFibCliPar(P): fib(%2d<-) = %-2d<-' % tuple(fib))

    print('Goodbye from Python rpcFibCliPar')

    
if __name__ == '__main__':
    fibClient(sys.argv[1:])
