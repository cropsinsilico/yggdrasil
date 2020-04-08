import threading
import multiprocessing
from multiprocessing import synchronize
import logging
from yggdrasil import tools
from yggdrasil.communication.ZMQComm import ZMQComm
# from yggdrasil.communication.BufferComm import BufferComm
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from multiprocessing import reduction


z = ZMQComm.new_comm('test')
# z = ConnectionDriver('test')
# z = BufferComm.new_comm('test')

def test_object(z):
    try:
        reduction.ForkingPickler.dumps(z)
    except BaseException as e:
        print(e)
        for k, v in z.__dict__.items():
            if k in ['_config', 'context']:
                continue
            if isinstance(v, (threading._RLock, threading._CRLock,
                              threading.Event, threading.Thread,
                              logging.Logger,
                              multiprocessing.synchronize.RLock,
                              multiprocessing.synchronize.Event)):
                continue
            try:
                reduction.ForkingPickler.dumps(v)
            except BaseException:
                print(k, type(v))
                raise

test_object(z)
