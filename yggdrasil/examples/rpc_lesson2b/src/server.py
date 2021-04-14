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

    print('Hello from Python server%s!' % os.environ['YGG_MODEL_COPY'])

    # Get parameters
    inp = YggInput("params")
    retval, params = inp.recv()
    if not retval:
        raise RuntimeError('server%s: ERROR receiving parameters'
                           % os.environ['YGG_MODEL_COPY'])
    print('server%s: Parameters = %s'
          % (os.environ['YGG_MODEL_COPY'], params))

    # Create server-side rpc conneciton using model name
    rpc = YggRpcServer("server", "%d", "%d")

    # Continue receiving requests until the connection is closed when all
    # clients have disconnected.
    while True:
        print('server%s: receiving...' % os.environ['YGG_MODEL_COPY'])
        retval, rpc_in = rpc.recv()
        if not retval:
            print('server: end of input')
            break

        # Compute fibonacci number
        n = rpc_in[0]
        print('server%s: Received request for Fibonacci number %d'
              % (os.environ['YGG_MODEL_COPY'], n))
        result = get_fibonacci(n)
        print('server%s: Sending response for Fibonacci number %d: %d'
              % (os.environ['YGG_MODEL_COPY'], n, result))

        # Send response back
        flag = rpc.send(np.int32(result))
        if not flag:
            raise RuntimeError('server%s: ERROR sending'
                               % os.environ['YGG_MODEL_COPY'])

    print('Goodbye from Python server%s' % os.environ['YGG_MODEL_COPY'])

    
if __name__ == '__main__':
    main()
