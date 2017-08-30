
import sys
from cis_interface.interface.PsiInterface import *
import os
import logging
from logging import *


def runhello():
    debug('hello python from %s', os.getcwd())

    # Ins/outs matching with the the model yaml
    inf = PsiInput('inFile')
    outf = PsiOutput('outFile')
    inq = PsiInput('helloQueueIn')
    outq = PsiOutput('helloQueueOut')
    info("created channels")

    buf = inf.recv()
    debug('got %d bytes on inf', len(buf))
    outq.send(buf)
    debug('sent to outq')
    buf = inq.recv()
    debug('got %d bytes on inq', len(buf))
    outf.send(buf)
    debug('sent output to outf')
    debug("bye")

if __name__ == '__main__':
    logLevel = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        logLevel = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DEBUG' in os.environ:
        rmqLogLevel = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(level=logLevel, stream=sys.stdout, 
	format=sys.argv[0].split('/')[-1]+': %(message)s')
    runhello()
    
