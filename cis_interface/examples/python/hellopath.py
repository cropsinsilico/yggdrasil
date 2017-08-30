
import sys
import os
import logging
from logging import *
import time
from cis_interface.interface.PsiInterface import *

def runhello():
    debug('hello python from %s', os.getcwd())
    time.sleep(10)
    debug('bye')
    input('press a key')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, 
        #stream=sys.stdout,
        filename='hello.log', 
        format=sys.argv[0].split('/')[-1]+':%(message)s')
    runhello()
  
