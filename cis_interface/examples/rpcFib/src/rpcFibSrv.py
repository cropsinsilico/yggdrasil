from __future__ import print_function
import sys
from cis_interface.interface.CisInterface import CisRpcServer
from cis_interface.tools import sleep


def fibServer(args):

    sleeptime = float(args[0])
    print('Hello from Python rpcFibSrv: sleeptime = %f' % sleeptime)

    # Create server-side rpc conneciton using model name
    rpc = CisRpcServer("rpcFibSrv", "%d", "%d %d")

    # Continue receiving requests until error occurs (the connection is closed
    # by all clients that have connected).
    while True:
        print('rpcFibSrv(P): receiving...')
        retval, rpc_in = rpc.rpcRecv()
        if not retval:
            print('rpcFibSrv(P): end of input')
            break

        # Compute fibonacci number
        print('rpcFibSrv(P): <- input %d' % rpc_in[0], end='')
        pprev = 0
        prev = 1
        result = 1
        fib_no = 1
        arg = rpc_in[0]
        while fib_no < arg:
            result = prev + pprev
            pprev = prev
            prev = result
            fib_no = fib_no + 1
        print(' ::: ->(%2d %2d)' % (arg, result))

        # Sleep and then send response back
        sleep(float(sleeptime))
        flag = rpc.rpcSend(arg, result)
        if not flag:
            print('rpcFibSrv(P): ERROR sending')
            break

    print('Goodbye from Python rpcFibSrv')
    sys.exit(0)

    
if __name__ == '__main__':
    fibServer(sys.argv[1:])
