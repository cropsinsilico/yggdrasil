import pprint
import time
import gc
from yggdrasil import tools
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from multiprocessing import freeze_support


def show_diff(old, new, cross=None):
    diff = set(old) - set(new)
    if cross is not None:
        diff = diff & cross
    print(' %d files' % len(diff))
    for x in diff:
        print(b'    %s' % x)
    return diff


def make_driver(**kwargs):
    kwargs['task_method'] = 'process'
    old = tools.get_fds()
    out = ConnectionDriver('test', **kwargs)
    new = tools.get_fds()
    print('created', end='')
    created = show_diff(new, old)
    return out, new, old, created


def check_driver(method, **kwargs):
    x, old, old0, created = make_driver()
    if method == 'terminate':
        x.terminate()
    elif method == 'delete':
        del x
    elif method == 'cleanup':
        x.cleanup()
    else:
        raise NotImplementedError
    gc.collect()
    time.sleep(1.0)
    new = tools.get_fds()
    print('%s closed' % method, end='')
    show_diff(old, new, created)
    print('%s leaked' % method, end='')
    show_diff(new, old0, created)
    if method != 'delete':
        del x


if __name__ == '__main__':
    freeze_support()
    check_driver('terminate')
    check_driver('delete')
    check_driver('cleanup')

    # # Try deletin individual attributes
    # x, old = make_driver()
    # for k in dir(x):
    #     if k.startswith('__') or (k in []):
    #         continue
    #     try:
    #         delattr(x, k)
    #         new = tools.get_fds()
    #         if len(new) < len(old):
    #             print(k)
    #             print('diff')
    #             show_diff(old, new)
    #         old = new
    #     except AttributeError:
    #         pass
