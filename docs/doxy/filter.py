#!/usr/bin/env python
import sys
import re

outfile = sys.stdout


def strip_comments(s, re_comments):
    my_match = re_comments.match(s)
    if my_match is not None:
        return my_match.group(1)
    else:
        return s


def filter(filename, out=sys.stdout):
    global outfile
    outfile = out
    if filename.endswith('.m'):
        re_comments = re.compile("([^\%]*)\%.*")  # noqa: W605
        re_doxy = re.compile(r"[^']*\%\>(.*)")
        re_function = re.compile(
            (r"(?P<type>^\s*function)\s*(?P<result>[\] \w\d,_\[]+=)?\s*"
             r"(?P<name>[.\w\d_-]*)\s"
             r"*\(?(?P<args>[\w\d\s,~]*)\)?(%?.*)"))
        re_interface = None
        re_interface_end = None
        re_interface_member = None
    elif filename.endswith('.f90'):
        re_comments = re.compile("([^\!]*)\!.*")  # noqa: W605
        re_doxy = re.compile(r"[^']*\!\>(.*)")
        re_function = re.compile(
            (r"\s*(?P<type>function|subroutine)\s*(?P<name>[.\w\d_-]*)\s"
             r"*\(?(?P<args>[\w\d\s,~]*)\)?(?P<result>\s*result\(\s*\w\s*\))?"
             r"(%?.*)"))
        re_interface = re.compile(r"\s*interface\s+(?P<name>[.\w\d_]+)\s*$")
        re_interface_end = re.compile(
            r"\s*end\s+interface\s+(?P<name>[.\w\d_]*)\s*$")
        re_interface_member = re.compile(
            r"\s*(?P<type>([.\w\d_]+\s+)+)(?P<name>[.\w\d_]+)\s*$")
    else:
        f = open(filename)
        outfile.write(f.read())
        return
    # Get namespace
    # rem = os.path.splitext(os.path.splitdrive(filename)[-1])[0]
    # namespace = ''
    # while rem not in ['', '/', '\\', '\\\\']:
    #     rem, new = os.path.split(rem)
    #     if new not in ['..', '.']:
    #         if namespace:
    #             namespace = new + '.' + namespace
    #         else:
    #             namespace = new
    #     if new == 'yggdrasil':
    #         break
    in_interface = False
    interface_doxy = {}
    interface_members = {}
    interface_complete = []
    try:
        f = open(filename)
        r = f.readlines()
        doxygen_comments = []
        for s in r:
            doxy = re_doxy.match(s)
            s_strip = strip_comments(s, re_comments)
            s_func = re_function.match(s_strip)
            s_int = None
            s_mem = None
            s_int_end = None
            if re_interface:
                s_int = re_interface.match(s_strip)
            if in_interface:
                s_int_end = re_interface_end.match(s_strip)
            if in_interface and (not s_int_end):
                s_mem = re_interface_member.match(s_strip)
            if (doxy is not None):
                doxygen_comments.append("/// " + doxy.group(1) + "\n")
            elif s_func is not None:
                args = s_func.group('args')
                if args:
                    args = 'in ' + args.replace(',', ',in ')
                this_interface = interface_members.pop(s_func.group('name'),
                                                       None)
                if this_interface:
                    this_interface_doxy = interface_doxy[this_interface]
                    if this_interface not in interface_complete:
                        for x in this_interface_doxy:
                            outfile.write(x)
                        outfile.write("%s %s(%s);\n" % (
                            s_func.group('type'), this_interface, args))
                        interface_complete.append(this_interface)
                    if not doxygen_comments:
                        doxygen_comments = this_interface_doxy
                for x in doxygen_comments:
                    outfile.write(x)
                outfile.write("%s %s(%s);\n" % (
                    s_func.group('type'), s_func.group('name'), args))
                doxygen_comments = []
            elif s_int:
                in_interface = s_int.group('name')
                interface_doxy[in_interface] = doxygen_comments
                doxygen_comments = []
            elif s_mem:
                interface_members[s_mem.group('name')] = in_interface
            elif s_int_end:
                in_interface = False
            elif not re_comments.match(s):
                doxygen_comments = []
    except IOError as e:
        sys.stderr.write(e[1] + "\n")


if len(sys.argv) != 2:
    print("usage: ", sys.argv[0], " filename")
    sys.exit(1)

# Filter the specified file and print the result to stdout
filename = sys.argv[1]
filter(filename)
sys.exit(0)
