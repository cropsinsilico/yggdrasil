#!/usr/bin/python
import os
import sys
import signal
import numpy as np
from cis_interface.interface.PsiInterface import *

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal_handler)
	
	in1 = PsiInput('input1')
	in2 = PsiInput('static')
	out1 = PsiOutput('output')
	
	adata = in1.recv()
	bdata = in2.recv()
	
	a = int(adata[0])
	b = int(bdata[0])
	sum = a+b
	
	outdata = 'Sum = ' + str(sum)
	out1.send(outdata)


