#!/usr/bin/env python
import sys
import re

outfile = sys.stdout


def filter(filename, out=sys.stdout):
    global outfile
    outfile = out
    if filename.endswith('.m'):
        re_doxy = re.compile(r"[^']*\%\>(.*)")
    elif filename.endswith('.f90'):
        re_doxy = re.compile(r"[^']*\!\>(.*)")
    else:
        f = open(filename)
        outfile.write(f.read())
        return
    try:
        f = open(filename)
        r = f.readlines()
        for s in r:
            doxy = re_doxy.match(s)
            if doxy is None:
                outfile.write(s)
    except IOError as e:
        sys.stderr.write(e[1] + "\n")


if len(sys.argv) != 2:
    print("usage: ", sys.argv[0], " filename")
    sys.exit(1)

# Filter the specified file and print the result to stdout
filename = sys.argv[1]
filter(filename)
sys.exit(0)
