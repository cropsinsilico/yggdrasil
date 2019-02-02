import sys
import numpy as np
from yggdrasil.interface.YggInterface import (
    YggRpcClient, YggOutput)


def main(iterations, client_index):
    r"""Function to execute client communication with server that computes
    numbers in the Fibonacci sequence.

    Args:
        iterations (int): The number of Fibonacci numbers to log.
        client_index (int): Index of the client in total list of clients.

    """

    print('Hello from Python client%d: iterations = %d ' % (client_index,
                                                            iterations))

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = YggRpcClient("server_client%d" % client_index, "%d", "%d")
    log = YggOutput("output_log%d" % client_index, 'fib(%-2d) = %-2d\n')

    # Iterate over Fibonacci sequence
    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('client%d(Python): Calling fib(%d)' % (client_index, i))
        ret, result = rpc.call(np.int32(i))
        if not ret:
            raise RuntimeError('client%d(Python): RPC CALL ERROR' % client_index)
        fib = result[0]
        print('client%d(Python): Response fib(%d) = %d' % (client_index, i, fib))

        # Log result by sending it to the log connection
        ret = log.send(np.int32(i), fib)
        if not ret:
            raise RuntimeError('client%d(Python): SEND ERROR' % client_index)

    print('Goodbye from Python client%d' % client_index)

    
if __name__ == '__main__':
    # Take number of iterations from the first argument and the
    # client index from the second
    main(int(sys.argv[1]), int(sys.argv[2]))
