import sys
import numpy as np
from yggdrasil.interface.YggInterface import (
    YggRpcClient, YggOutput)


def main(iterations):
    r"""Function to execute client communication with server that computes
    numbers in the Fibonacci sequence.

    Args:
        iterations (int): The number of Fibonacci numbers to log.

    """

    print('Hello from Python client: iterations = %d ' % iterations)

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = YggRpcClient("server_client", "%d", "%d")
    log = YggOutput("output_log", 'fib(%-2d) = %-2d\n')

    # Iterate over Fibonacci sequence
    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('client(Python): Calling fib(%d)' % i)
        ret, result = rpc.call(np.int32(i))
        if not ret:
            raise RuntimeError('client(Python): RPC CALL ERROR')
        fib = result[0]
        print('client(Python): Response fib(%d) = %d' % (i, fib))

        # Log result by sending it to the log connection
        ret = log.send(np.int32(i), fib)
        if not ret:
            raise RuntimeError('client(Python): SEND ERROR')

    print('Goodbye from Python client')

    
if __name__ == '__main__':
    # Take number of iterations from the first argument
    main(int(sys.argv[1]))
