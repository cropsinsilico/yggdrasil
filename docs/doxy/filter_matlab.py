#!/usr/bin/env python
import sys
import re
import os

outfile = sys.stdout

# regular expression
# re to strip comments from file
re_comments = re.compile("([^\%]*)\%.*")  # noqa: W605
# re to search doxygen-comments
re_doxy = re.compile(r"[^']*\%\>(.*)")
# re to search functions
re_function = re.compile(
    (r"(^\s*function)\s*([\] \w\d,_\[]+=)?\s*([.\w\d_-]*)\s"
     r"*\(?([\w\d\s,~]*)\)?(%?.*)"))


def strip_comments(s):
    global re_comments
    my_match = re_comments.match(s)
    if my_match is not None:
        return my_match.group(1)
    else:
        return s


def filter(filename, out=sys.stdout):
    global outfile
    outfile = out
    rem = os.path.splitext(os.path.splitdrive(filename)[-1])[0]
    namespace = ''
    while rem not in ['', '/', '\\', '\\\\']:
        rem, new = os.path.split(rem)
        if new not in ['..', '.']:
            if namespace:
                namespace = new + '.' + namespace
            else:
                namespace = new
        if new == 'yggdrasil':
            break
    try:
        f = open(filename)
        r = f.readlines()
        for s in r:
            doxy = re_doxy.match(s)
            s_strip = strip_comments(s)
            s_func = re_function.match(s_strip)
            if (doxy is not None):
                outfile.write("/// " + doxy.group(1) + "\n")
            elif s_func is not None:
                args = s_func.group(4)
                if args:
                    args = 'in ' + args.replace(',', ',in ')
                outfile.write("%s %s(%s);\n" % (
                    s_func.group(1), s_func.group(3), args))
    except IOError as e:
        sys.stderr.write(e[1] + "\n")


if len(sys.argv) != 2:
    print("usage: ", sys.argv[0], " filename")
    sys.exit(1)

# Filter the specified file and print the result to stdout
filename = sys.argv[1]
filter(filename)
sys.exit(0)
