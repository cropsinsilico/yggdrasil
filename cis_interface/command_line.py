#!/usr/bin/python
import sys
import time
from logging import debug
import signal
import traceback
from cis_interface import runner


cisRunner = None
INTERRUPT_TIME = 0
COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


# pretty pprint
def pprint(*args):
    s = ''.join(str(i) for i in args)
    print(COLOR_TRACE + '{}' + COLOR_NORMAL.format(s))

    
def signal_handler(sigCaught, frame):  # pragma: no cover
    global INTERRUPT_TIME, cisRunner
    debug('CisRunner interrupted with signal %d', sigCaught)
    now = time.time()
    elapsed = now - INTERRUPT_TIME
    debug('CisRunner.handler: elapsed since last interrupt: %d', elapsed)
    INTERRUPT_TIME = now
    if elapsed < 5:
        pprint(' ')
        pprint('*********************************************************')
        pprint('*  Interrupted twice within 5 seconds:  shutting down   *')
        pprint('*********************************************************')
        # signal.siginterrupt(signal.SIGTERM, True)
        # signal.siginterrupt(signal.SIGINT, True)
        debug("CisRunner.closing all channels")
        if cisRunner:
            cisRunner.terminate()
        return 1
    else:
        pprint('')
        pprint('*********************************************************')
        pprint('*  Interrupted: Displaying channel summary              *')
        pprint('*  interrupt again (within 5 seconds) to exit           *')
        pprint('*********************************************************')
        if cisRunner:
            cisRunner.printStatus()
        pprint('*********************************************************')
    debug('CisRunner handler(%d) returns', sigCaught)
    return 0


def cisrun():
    global cisRunner
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.siginterrupt(signal.SIGTERM, False)
        signal.siginterrupt(signal.SIGINT, False)
        prog = sys.argv[0].split('/')[-1]
        models = sys.argv[1:]
        cisRunner = runner.get_runner(models, cis_debug_prefix=prog)
        cisRunner.run()
        debug("cisRunner returns, exiting")
    except Exception as ex:
        pprint("cisrun: exception: %s" % type(ex))
        print(traceback.format_exc())
    print('')


if __name__ == '__main__':
    cisrun()
    sys.exit(0)
