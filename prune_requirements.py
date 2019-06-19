# https://www.python.org/dev/peps/pep-0508/
from pip._vendor.packaging.requirements import Requirement, InvalidRequirement
import os
import sys


def prune(fname_in, fname_out=None):
    r"""Prune a requirements.txt file to remove/select dependencies that are
    dependent on the current environment.

    Args:
        fname_in (str): Full path to requirements file that should be read.
        fname_out (str, optional): Full path to requirements file that should be
            created. Defaults to None and is set to <fname_in>_pruned.txt.

    Returns:
        str: Full path to created file.

    """
    with open(fname_in, 'r') as fd:
        old_lines = fd.readlines()
    new_lines = []
    for line in old_lines:
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
        fname_out = '_pruned'.join(os.path.splitext(fname_in))
    with open(fname_out, 'w') as fd:
        fd.write('\n'.join(new_lines))
    return fname_out


if __name__ == "__main__":
    fname_in = sys.argv[1]
    fname_out = None
    if len(sys.argv) > 2:
        fname_out = sys.argv[2]
    fname_out = prune(fname_in, fname_out)
    print(fname_out)
