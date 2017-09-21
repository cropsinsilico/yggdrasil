"""This modules offers various tools."""
from subprocess import Popen, PIPE
import sysv_ipc
import time
from cis_interface import backwards


# OS X limit is 2kb
PSI_MSG_MAX = 1024 * 2
PSI_MSG_EOF = backwards.unicode2bytes("EOF!!!")
_registered_queues = {}


def eval_kwarg(x):
    r"""If x is a string, eval it. Otherwise just return it.

    Args:
        x (str, obj): String to be evaluated as an object or an object.

    Returns:
        obj: Evaluation result of x for strings if x is a string. x otherwise.

    """
    if isinstance(x, str):
        try:
            return eval(x)
        except NameError:
            return x
    return x


def get_queue(qid=None):
    r"""Create or return a sysv_ipc.MessageQueue and register it.

    Args:
        qid (int, optional): If provided, ID for existing queue that should be
           returned. Defaults to None and a new queue is returned.

    Returns:
        :class:`sysv_ipc.MessageQueue`: Message queue.

    """
    kwargs = dict(max_message_size=PSI_MSG_MAX)
    if qid is None:
        kwargs['flags'] = sysv_ipc.IPC_CREX
    mq = sysv_ipc.MessageQueue(qid, **kwargs)
    key = str(mq.key)
    if key not in _registered_queues:
        _registered_queues[key] = mq
    return mq


def remove_queue(mq):
    r"""Remove a sysv_ipc.MessageQueue and unregister it.

    Args:
        mq (:class:`sysv_ipc.MessageQueue`) Message queue.
    
    Raises:
        KeyError: If the provided queue is not registered.

    """
    key = str(mq.key)
    if key not in _registered_queues:
        raise KeyError("Queue not registered.")
    _registered_queues.pop(key)
    mq.remove()
    

def ipcs(options=[]):
    r"""Get the output from running the ipcs command.

    Args:
        options (list): List of flags that should be used. Defaults to an empty
            list.

    Returns:
        list: Captured output.

    """
    cmd = ' '.join(['ipcs'] + options)
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    output, err = p.communicate()
    exit_code = p.returncode
    if exit_code != 0:  # pragma: debug
        print(err.decode('utf-8'))
        raise Exception("Error on spawned process. See output.")
    return output.decode('utf-8')


def ipc_queues():
    r"""Get a list of active IPC queues.

    Returns:
       list: List of IPC queues.

    """
    skip_lines = [
        '------ Message Queues --------',
        'key        msqid      owner      perms      used-bytes   messages    ',
        '']
    out = ipcs(['-q']).split('\n')
    qlist = []
    for l in out:
        if l not in skip_lines:
            qlist.append(l)
    return qlist


def ipcrm(options=[]):
    r"""Remove IPC constructs using the ipcrm command.

    Args:
        options (list): List of flags that should be used. Defaults to an empty
            list.

    """
    cmd = ' '.join(['ipcrm'] + options)
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    output, err = p.communicate()
    exit_code = p.returncode
    if exit_code != 0:  # pragma: debug
        print(err.decode('utf-8'))
        raise Exception("Error on spawned process. See output.")
    print(output.decode('utf-8'))


def ipcrm_queues(queue_keys=None):
    r"""Delete existing IPC queues.

    Args:
        queue_keys (list, str, optional): A list of keys for queues that should
            be removed. Defaults to all existing queues.

    """
    if queue_keys is None:
        queue_keys = [l.split()[0] for l in ipc_queues()]
    if isinstance(queue_keys, str):
        queue_keys = [queue_keys]
    for q in queue_keys:
        ipcrm(["-Q %s" % q])


class TimeOut(object):
    r"""Class for checking if a period of time has been elapsed.

    Args:
        max_time (float): Maximum period of time that should elapsed before
            'is_out' returns True.

    Attributes:
        max_time (float): Maximum period of time that should elapsed before
            'is_out' returns True.
        start_time (float): Result of time.time() at start.

    """

    def __init__(self, max_time):
        self.max_time = max_time
        self.start_time = time.clock()

    @property
    def elapsed(self):
        r"""float: Total time that has elapsed since the start."""
        return time.clock() - self.start_time
    
    @property
    def is_out(self):
        r"""bool: True if there is not any time remaining. False otherwise."""
        if not self.max_time:
            return False
        return (self.elapsed > self.max_time)
