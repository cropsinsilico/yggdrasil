"""This modules offers various tools."""
from subprocess import Popen, PIPE


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
    if exit_code != 0:
        print(err.decode('utf-8'))
        raise Exception("Error on spawned process. See output.")
    print(output.decode('utf-8'))


def ipcrm_queues():
    r"""Delete existing IPC queues."""
    ipcrm(['--all=msg'])

