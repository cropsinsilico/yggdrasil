import sys
from cis_interface.interface.CisInterface import (
    CisRpcClient, CisOutput)


def main(iterations, client_index):
    r"""Function to execute client communication with server that computes
    numbers in the Fibonacci sequence.

    Args:
        iterations (int): The number of Fibonacci numbers to log.
        client_index (int): Index of the client in total list of clients.

    Returns:
        int: Exit code. Negative if an error occurred.

    """

    exit_code = 0
    print('Hello from Python client%d: iterations = %d ' % (client_index,
                                                            iterations))

    # Set up connections matching yaml
    # RPC client-side connection will be $(server_name)_$(client_name)
    rpc = CisRpcClient("server_client%d" % client_index, "%d", "%d")
    log = CisOutput("output_log%d" % client_index, 'fib(%-2d) = %-2d\n')

    # Iterate over Fibonacci sequence
    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('client%d(Python): Calling fib(%d)' % (client_index, i))
        ret, result = rpc.call(i)
        if not ret:
            print('client%d(Python): RPC CALL ERROR' % client_index)
            exit_code = -1
            break
        fib = result[0]
        print('client%d(Python): Response fib(%d) = %d' % (client_index, i, fib))

        # Log result by sending it to the log connection
        ret = log.send(i, fib)
        if not ret:
            print('client%d(Python): SEND ERROR' % client_index)
            exit_code = -1
            break

    print('Goodbye from Python client%d' % client_index)
    return exit_code

    
if __name__ == '__main__':
    # Take number of iterations from the first argument and the
    # client index from the second
    exit_code = main(int(sys.argv[1]), int(sys.argv[2]))
    sys.exit(exit_code)
