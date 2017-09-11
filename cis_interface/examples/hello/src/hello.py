import sys
from cis_interface.interface.PsiInterface import PsiInput, PsiOutput
import os
import logging
from logging import info, debug


def runhello():
    info('hello python from %s', os.getcwd())

    # Ins/outs matching with the the model yaml
    inf = PsiInput('inFile')
    outf = PsiOutput('outFile')
    inq = PsiInput('helloQueueIn')
    outq = PsiOutput('helloQueueOut')
    info("created channels")

    # Receive input from a local file
    flag, buf = inf.recv()
    info('got %d bytes on inf', len(buf))

    # Send output to the output queue
    outq.send(buf)
    info('sent to outq')

    # Receive input form the input queue
    flag, buf = inq.recv()
    info('got %d bytes on inq', len(buf))

    # Send output to a local file
    outf.send(buf)
    info('sent output to outf')
    info("bye")
    

if __name__ == '__main__':
    logLevel = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        logLevel = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DEBUG' in os.environ:
        rmqLogLevel = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(
        level=logLevel, stream=sys.stdout,
        format=sys.argv[0].split('/')[-1] + ': %(message)s')
    runhello()
