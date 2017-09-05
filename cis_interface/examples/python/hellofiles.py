import logging
import os
import sys
from logging import debug
from cis_interface.interface.PsiInterface import PsiInput, PsiOutput


def runhello():
    debug('hello pythonfiles from %s', os.getcwd())
    inf = PsiInput('inFile')
    outf = PsiOutput('outFile')
    flag, fdata = inf.recv()
    debug('got input %s', (flag, fdata))
    outf.send(fdata)
    debug('sent output')
    debug('bye')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=sys.argv[0].split('/')[-1] + ':%(message)s')
    runhello()
