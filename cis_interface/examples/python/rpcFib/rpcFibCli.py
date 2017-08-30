from __future__ import print_function
import logging
import os
import sys
from cis_interface.interface.PsiInterface import *
import socket


def fibClient(args):
    host = os.environ.get('PSI_HOST', 'NOT SET')
    namespace = os.environ.get('PSI_NAMESPACE', 'NOT SET')
    rank = os.environ.get('PSI_RANK', 'NOT SET')

    iterations = int(args[0])
    print('hello fibcli(P): system {} namespace {} rank {} iterations {}'.format(
        host, namespace, rank, iterations))
 
    rpc = PsiRpc("cli_fib", "%d", "cli_fib", "%d %d")
    log = PsiOutput("output_log")
    ymlfile = PsiInput("yaml_in")
    ycontent = str(ymlfile.recv())
    print('input file contents: ')
    print(ycontent)

    for i in range(1, iterations+1):
        print('fibcli(P): fib(->%-2d) ::: ' % i, end='')
        idx, fib = rpc.rpcCall(i)
        if not idx: # killed = False
            break
        s = 'fib(%2d<-) = %-2d<-' % fib # (tuple(i,fib(i))
        print(s)
        log.send(s+'\n')

    print('rpcFibCli:  python says goodbye')
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
