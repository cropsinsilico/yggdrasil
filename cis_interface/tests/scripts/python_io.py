import logging
from logging import debug
import os
import sys
from YggInterface import YggInput, YggOutput


def runhello():
    debug('hello pythonfiles from %s', os.getcwd())
    inf = YggInput('inFile')
    outf = YggOutput('outFile')
    fdata = inf.recv()
    debug('got input %s', fdata)
    print(fdata)
    outf.send(fdata)
    debug('sent output')
    debug('bye')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format=sys.argv[0].split('/')[-1] + ':%(message)s')
    runhello()
