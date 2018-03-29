from __future__ import print_function
import sys
from cis_interface.interface.CisInterface import CisInput, CisOutput


def run():
    print('Hello from Python pipe_dst')

    # Ins/outs matching with the the model yaml
    inq = CisInput('input_pipe')
    outf = CisOutput('output_file')
    print("pipe_dst(P): Created I/O channels")

    # Continue receiving input from the queue
    count = 0
    while True:
        ret, buf = inq.recv()
        if not ret:
            print("pipe_dst(P): Input channel closed")
            break
        ret = outf.send(buf)
        if not ret:
            print("pipe_dst(P): SEND ERROR ON MSG %d" % count)
            sys.exit(-1)
        count += 1

    print('Goodbye from Python destination. Received %d messages.' % count)

    
if __name__ == '__main__':
    run()
