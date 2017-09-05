#!/usr/bin/python
import sys
import signal
from cis_interface.interface.PsiInterface import PsiInput, PsiOutput


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    print('Hello from Python!')
    in1 = PsiInput('pyinput1')
    in2 = PsiInput('pystatic')
    out1 = PsiOutput('pyoutput')

    adata = in1.recv()[1]
    print("Python received {} from pyinput1".format(adata))
    bdata = in2.recv()[1]
    print("Python received {} from pystatic".format(bdata))

    a = int(adata)
    b = int(bdata)
    sum = a + b

    outdata = str(sum)
    out1.send(outdata)
    print("Python sent {} to pyoutput".format(outdata))

    print('Goodbye from Python!')
