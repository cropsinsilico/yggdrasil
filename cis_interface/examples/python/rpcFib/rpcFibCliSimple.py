
import logging
import os
import sys
from PsiInterface import *

def fibClient(args):
    print 'fibcli(P): hello ', args[0], ' iterations'
    iterations = int(args[0])
    inchan = PsiInput("cli_input")
    outchan = PsiOutput("cli_output")

    log = PsiOutput("output_log")
    ymlfile = PsiInput("yaml_in")
    ycontent = str(ymlfile.recv())
    print 'input file contents: '
    print ycontent

    for i in range(1, iterations+1):
        outb = "%d" % (i)
        print 'fibcli(P): fib(->%s) ::: ' % outb,
        ret = outchan.send(outb)
        if not ret:
            print 'send error'
            sys.exit(-1)
        ret, data = inchan.recv()
        if not ret:
            print 'recv error'
            sys.exit(-1)
        s = 'results: %s' % data
        print s
        log.send(s+'\n')

    print 'rpcFibCli:  python says goodbye'
    sys.exit(0)

if __name__ == '__main__':
    logLevel = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        logLevel = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DEBUG' in os.environ:
        rmqLogLevel = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(level=logLevel, stream=sys.stdout, \
	format=sys.argv[0].split('/')[-1]+': %(message)s')
    fibClient(sys.argv[1:])
