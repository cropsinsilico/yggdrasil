from __future__ import print_function
import sys
from cis_interface.interface.CisInterface import CisRpcClient


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCliPar: iterations = %d' % iterations)

    # Create RPC connection with server
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = CisRpcClient("rpcFibSrv_rpcFibCliPar", "%d", "%d %d")

    # Send all of the requests to the server
    for i in range(1, iterations + 1):
        print('rpcFibCliPar(P): fib(->%-2d) ::: ' % i)
        ret = rpc.rpcSend(i)
        if not ret:
            raise RuntimeError('rpcFibCliPar(P): SEND FAILED')

    # Receive responses for all requests that were sent
    for i in range(1, iterations + 1):
        ret, fib = rpc.rpcRecv()
        if not ret:
            raise RuntimeError('rpcFibCliPar(P): RECV FAILED')
        print('rpcFibCliPar(P): fib(%2d<-) = %-2d<-' % fib)

    print('Goodbye from Python rpcFibCliPar')

    
if __name__ == '__main__':
    fibClient(sys.argv[1:])
