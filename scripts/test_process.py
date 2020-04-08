import pprint
from yggdrasil import tools
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


def show_diff(old, new):
    diff = set(old) - set(new)
    for x in diff:
        print(b'    %s' % x)


def make_driver(**kwargs):
    old = tools.get_fds()
    out = ConnectionDriver('test', **kwargs)
    new = tools.get_fds()
    print('created')
    show_diff(new, old)
    return out, new, old


def check_driver(method, **kwargs):
    x, old, old0 = make_driver()
    if method == 'terminate':
        x.terminate()
    elif method == 'delete':
        del x
    else:
        raise NotImplementedError
    new = tools.get_fds()
    print('%s closed' % method)
    show_diff(old, new)
    print('%s leaked' % method)
    show_diff(new, old0)
    if method != 'delete':
        del x


check_driver('terminate')
check_driver('delete')

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
