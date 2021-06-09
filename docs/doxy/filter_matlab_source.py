#!/usr/bin/env python
import sys
import re

outfile = sys.stdout

# regular expression
# re to search doxygen-comments
re_doxy = re.compile(r"[^']*\%\>(.*)")


def filter(filename, out=sys.stdout):
    global outfile
    outfile = out
    try:
        f = open(filename)
        r = f.readlines()
        for s in r:
            doxy = re_doxy.match(s)
            if doxy is None:
                outfile.write(s)
        sys.stderr.write("OK\n")
    except IOError as e:
        sys.stderr.write(e[1] + "\n")


if len(sys.argv) != 2:
    print("usage: ", sys.argv[0], " filename")
    sys.exit(1)

# Filter the specified file and print the result to stdout
filename = sys.argv[1]
filter(filename)
sys.exit(0)
