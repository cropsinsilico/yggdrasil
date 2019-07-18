# https://www.python.org/dev/peps/pep-0508/
from pip._vendor.packaging.requirements import Requirement, InvalidRequirement
import os
import sys


def prune(fname_in, fname_out=None):
    r"""Prune a requirements.txt file to remove/select dependencies that are
    dependent on the current environment.

    Args:
        fname_in (str, list): Full path to one or more requirements files that
            should be read.
        fname_out (str, optional): Full path to requirements file that should be
            created. Defaults to None and is set to <fname_in[0]>_pruned.txt.

    Returns:
        str: Full path to created file.

    """
    if not isinstance(fname_in, (list, tuple)):
        fname_in = [fname_in]
    new_lines = []
    for ifname_in in fname_in:
        with open(ifname_in, 'r') as fd:
            old_lines = fd.readlines()
        for line in old_lines:
            if line.startswith('#'):
                continue
            try:
                req = Requirement(line.strip())
                if req.marker and (not req.marker.evaluate()):
                    continue
                new_lines.append(req.name + str(req.specifier))
            except InvalidRequirement as e:
                print(e)
                continue
    # Write file
    if fname_out is None:
        fname_out = '_pruned'.join(os.path.splitext(fname_in[0]))
    with open(fname_out, 'w') as fd:
        fd.write('\n'.join(new_lines))
    return fname_out


if __name__ == "__main__":
    fname_in = sys.argv[1:]
    fname_out = prune(fname_in)
    print(fname_out)
