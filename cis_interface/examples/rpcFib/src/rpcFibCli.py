from __future__ import print_function
import sys
from cis_interface.interface.CisInterface import (
    CisRpcClient, CisInput, CisOutput)
from cis_interface import backwards


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCli: iterations = %d ' % iterations)

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    ymlfile = CisInput("yaml_in")
    rpc = CisRpcClient("rpcFibSrv_rpcFibCli", "%d", "%d %d")
    log = CisOutput("output_log")

    # Read entire contents of yaml
    ret, ycontent = ymlfile.recv()
    if not ret:
        print('rpcFibCli(P): RECV ERROR')
        sys.exit(-1)
    print('rpcFibCli: yaml has %d lines' % len(ycontent.split(
        backwards.unicode2bytes('\n'))))

    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('rpcFibCli(P): fib(->%-2d) ::: ' % i, end='')
        ret, fib = rpc.rpcCall(i)
        if not ret:
            print('rpcFibCli(P): RPC CALL ERROR')
            sys.exit(-1)

        # Log result by sending it to the log connection
        s = 'fib(%2d<-) = %-2d<-\n' % fib
        print(s, end='')
        ret = log.send(s)
        if not ret:
            print('rpcFibCli(P): SEND ERROR')
            sys.exit(-1)

    print('Goodbye from Python rpcFibCli')
    sys.exit(0)

    
if __name__ == '__main__':
    fibClient(sys.argv[1:])
