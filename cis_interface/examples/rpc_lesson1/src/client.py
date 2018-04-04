import sys
from cis_interface.interface.CisInterface import (
    CisRpcClient, CisOutput)


def main(iterations):
    r"""Function to execute client communication with server that computes
    numbers in the Fibonacci sequence.

    Args:
        iterations (int): The number of Fibonacci numbers to log.

    Returns:
        int: Exit code. Negative if an error occurred.

    """

    exit_code = 0
    print('Hello from Python client: iterations = %d ' % iterations)

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = CisRpcClient("server_client", "%d", "%d")
    log = CisOutput("output_log", 'fib(%-2d) = %-2d\n')

    # Iterate over Fibonacci sequence
    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('client(Python): Calling fib(%d)' % i)
        ret, result = rpc.call(i)
        if not ret:
            print('client(Python): RPC CALL ERROR')
            exit_code = -1
            break
        fib = result[0]
        print('client(Python): Response fib(%d) = %d' % (i, fib))

        # Log result by sending it to the log connection
        ret = log.send(i, fib)
        if not ret:
            print('client(Python): SEND ERROR')
            exit_code = -1
            break

    print('Goodbye from Python client')
    return exit_code

    
if __name__ == '__main__':
    # Take number of iterations from the first argument
    exit_code = main(int(sys.argv[1]))
    sys.exit(exit_code)
