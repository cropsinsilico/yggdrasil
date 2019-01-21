from __future__ import print_function
from yggdrasil.interface.YggInterface import YggInput, YggOutput


def runhello():
    print('Hello from Python')

    # Ins/outs matching with the the model yaml
    inf = YggInput('inFile')
    outf = YggOutput('outFile')
    inq = YggInput('helloQueueIn')
    outq = YggOutput('helloQueueOut')
    print("hello(P): Created I/O channels")

    # Receive input from a local file
    ret, buf = inf.recv()
    if not ret:
        raise RuntimeError('hello(P): ERROR FILE RECV')
    print('hello(P): Received %d bytes from file: %s' % (len(buf), buf))

    # Send output to the output queue
    ret = outq.send(buf)
    if not ret:
        raise RuntimeError('hello(P): ERROR QUEUE SEND')
    print('hello(P): Sent to outq')

    # Receive input form the input queue
    ret, buf = inq.recv()
    if not ret:
        raise RuntimeError('hello(P): ERROR QUEUE RECV')
    print('hello(P): Received %d bytes from queue: %s' % (len(buf), buf))

    # Send output to a local file
    ret = outf.send(buf)
    if not ret:
        raise RuntimeError('hello(P): ERROR FILE SEND')
    print('hello(P): Sent to outf')

    print('Goodbye from Python')

    
if __name__ == '__main__':
    runhello()
