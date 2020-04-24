import threading
import multiprocessing
from multiprocessing import synchronize
import logging
from yggdrasil import tools, multitasking
from yggdrasil.communication.ZMQComm import ZMQComm
# from yggdrasil.communication.BufferComm import BufferComm
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from multiprocessing import reduction, freeze_support, get_context
context = get_context("spawn")


def test_method(x):
    # print(x)
    return


def test_object(z, key=None, index=''):
    try:
        proc = context.Process(target=test_method, args=(z,))
        proc.start()
        proc.join()
    except BaseException as e:
        if key is not None:
            print(index + str(key))
        print(index + 'Error: ' + str(e))
        if isinstance(z, dict):
            items = z.items()
        elif hasattr(z, '__getstate__'):
            items = z.__getstate__().items()
        else:
            items = z.__dict__.items()
        for k, v in items:
            if k in ['_config']:
                continue
            try:
                reduction.ForkingPickler.dumps(v)
            except BaseException:
                test_object(v, key=(k, type(v), v), index=(index + '  '))


if __name__ == '__main__':
    freeze_support()
    # z = multitasking.Task()
    # z = multitasking.YggTask()
    # z = ZMQComm.new_comm('test', dont_open=True)
    z = ConnectionDriver('test', method='thread')
    # z = BufferComm.new_comm('test')


    test_object(z)
