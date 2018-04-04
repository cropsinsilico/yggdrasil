from __future__ import print_function
import sys
from cis_interface.interface.CisInterface import CisInput, CisOutput


def runhello():
    print('Hello from Python')

    # Ins/outs matching with the the model yaml
    inf = CisInput('inFile')
    outf = CisOutput('outFile')
    inq = CisInput('helloQueueIn')
    outq = CisOutput('helloQueueOut')
    print("hello(P): Created I/O channels")

    # Receive input from a local file
    ret, buf = inf.recv()
    if not ret:
        print('hello(P): ERROR FILE RECV')
        sys.exit(-1)
    print('hello(P): Received %d bytes from file: %s' % (len(buf), buf))

    # Send output to the output queue
    ret = outq.send(buf)
    if not ret:
        print('hello(P): ERROR QUEUE SEND')
        sys.exit(-1)
    print('hello(P): Sent to outq')

    # Receive input form the input queue
    ret, buf = inq.recv()
    if not ret:
        print('hello(P): ERROR QUEUE RECV')
        sys.exit(-1)
    print('hello(P): Received %d bytes from queue: %s' % (len(buf), buf))

    # Send output to a local file
    ret = outf.send(buf)
    if not ret:
        print('hello(P): ERROR FILE SEND')
        sys.exit(-1)
    print('hello(P): Sent to outf')

    print('Goodbye from Python')

    
if __name__ == '__main__':
    runhello()
