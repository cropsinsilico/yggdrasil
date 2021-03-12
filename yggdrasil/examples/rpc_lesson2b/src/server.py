import os
import numpy as np
from yggdrasil.interface.YggInterface import YggInput, YggRpcServer


def get_fibonacci(n):
    r"""Compute the nth number of the Fibonacci sequence.

    Args:
        n (int): Index of the Fibonacci number in the Fibonacci sequence that
            should be returned.

    Returns:
        int: The nth Fibonacci number.

    """
    pprev = 0
    prev = 1
    result = 1
    fib_no = 1
    while fib_no < n:
        result = prev + pprev
        pprev = prev
        prev = result
        fib_no = fib_no + 1
    return result


def main():
    r"""Function to execute server communication and computation in a loop."""

    model_copy = os.environ['YGG_MODEL_COPY']
    print('Hello from Python server%s!' % model_copy)

    # Get parameters
    inp = YggInput("params")
    retval, params = inp.recv()
    if not retval:
        raise RuntimeError('server%s: ERROR receiving parameters' % model_copy)
    print('server%s: Parameters = %s' % (model_copy, params))

    # Create server-side rpc conneciton using model name
    rpc = YggRpcServer("server", "%d", "%d")

    # Continue receiving requests until the connection is closed when all
    # clients have disconnected.
    while True:
        print('server%s(P): receiving...' % model_copy)
        retval, rpc_in = rpc.recv()
        if not retval:
            print('server: end of input')
            break

        # Compute fibonacci number
        n = rpc_in[0]
        print('server%s(P): Received request for Fibonacci number %d'
              % (model_copy, n))
        result = get_fibonacci(n)
        print('server%s(P): Sending response for Fibonacci number %d: %d'
              % (model_copy, n, result))

        # Send response back
        flag = rpc.send(np.int32(result))
        if not flag:
            raise RuntimeError('server%s(P): ERROR sending'
                               % model_copy)

    print('Goodbye from Python server%s' % model_copy)

    
if __name__ == '__main__':
    main()
