#!/usr/bin/env python
import sys
import re
import copy

outfile = sys.stdout
blocks = {}
interface_members = {}
doxy_char = '///'


def strip_comments(s, re_comments):
    my_match = re_comments.match(s)
    if my_match is not None:
        return my_match.group(1)
    else:
        return s


def format_dims_as_cpp(dim):
    out = ''
    if dim:
        for x in dim.split(','):
            if x.strip() in [':', '*']:
                out += '[]'
            else:
                out += '[%s]' % x.strip()
    return out


def format_argument(add_mods=False, as_fortran=False, **arg):
    if as_fortran:
        return arg['name']
    typename = arg.get('type', 'in')
    if add_mods and arg.get('type_mods', None):
        if (add_mods == 'cpp'):
            typename += '<%s>' % arg['type_mods'].strip('()').strip()
        else:
            typename += arg['type_mods']
    out = '%s %s' % (typename, arg['name'])
    if (not add_mods) or (add_mods == 'cpp'):
        dims = []
        if (not add_mods) and arg.get('len', None):
            dims.append(arg['len'])
        if arg.get('dim', None):
            dims.append(arg['dim'])
        out += format_dims_as_cpp(','.join(dims))
    return out


def format_function_str(name=None, args=None, arg_props={}, result_props={},
                        as_fortran=False, add_mods=False, **kwargs):
    if args:
        arglist = args.split(',')
        args = ''
        for arg in arglist:
            if args:
                args += ', '
            iarg_props = arg_props.get(arg, {})
            iarg_props.setdefault('name', arg)
            args += format_argument(add_mods=add_mods, as_fortran=as_fortran,
                                    **iarg_props)
    if as_fortran:
        out = "%s %s(%s)" % (kwargs['type'], name, args)
        if kwargs.get('type', None) in ['function', 'FUNCTION']:
            out += ' result(%s)' % result_props['name']
        return out
    if not result_props.get('type', None):
        result_props['type'] = kwargs.get('type', None)
    result_props['name'] = name
    result_name = format_argument(add_mods=add_mods, as_fortran=as_fortran,
                                  **result_props)
    return "%s(%s)" % (result_name, args)


def write_interface(interface, keep_original_code=False):
    global doxy_char
    interface['doxy'] += ['%s\n%s Interface members:\n%s ```\n'
                          % (doxy_char, doxy_char, doxy_char)]
    keys_to_join = {'type': 'in',
                    'name': '',
                    'mods': '',
                    'dim': '',
                    'len': ''}
    args0 = None
    args = []
    joined_args = {}
    joined_result = {k: [] for k in keys_to_join.keys()}
    for x in interface['members'].values():
        iargs = x['args'].split(',')
        if args0 is None:
            args0 = copy.deepcopy(iargs)
            args = [[a] for a in args0]
            for a in args0:
                joined_args[a] = {k: [] for k in keys_to_join.keys()}
        assert(len(iargs) == len(args0))
        for i, a in enumerate(iargs):
            args[i].append(a)
        for a0, a in zip(args0, iargs):
            for k, default in keys_to_join.items():
                joined_args[a0][k].append(x['arg_props'][a].get(k, default))
        for k, default in keys_to_join.items():
            joined_result[k].append(x['result_props'].get(k, default))
        interface['doxy'].append(
            '%s   %s\n' % (doxy_char,
                           format_function_str(add_mods=True, **x)))
    interface['doxy'] += ['%s```\n' % doxy_char]
    # Join types
    args = [list(set(a)) for a in args]
    joined_args = {a: {k: list(set(v)) for k, v in akw.items()}
                   for a, akw in joined_args.items()}
    joined_result = {k: list(set(v)) for k, v in joined_result.items()}
    interface['args'] = args0
    interface['arg_props'] = {}
    for a, akw in joined_args.items():
        interface['arg_props'][a] = {'name': a}
        for k, default in keys_to_join.items():
            if len(akw[k]) == 1:
                interface['arg_props'][a][k] = akw[k][0]
            elif default:
                interface['arg_props'][a][k] = default
            else:
                interface['arg_props'][a][k] = None
    interface['result_props'] = {}
    for k, default in keys_to_join.items():
        if len(joined_result[k]) == 1:
            interface['result_props'][k] = joined_result[k][0]
        elif default:
            interface['result_props'][k] = default
        else:
            interface['result_props'][k] = None
    if interface['result_props']['type'] == 'in':
        interface['result_props']['type'] = next(
            iter(interface['members'].values()))['type']
    interface['result_props']['name'] = interface['name']
    interface['type'] = 'interface'
    interface['args'] = ','.join(interface['args'])
    write_function(interface, keep_original_code=keep_original_code)


def write_function(in_function, keep_original_code=False):
    global outfile
    if keep_original_code:
        pass
    else:
        for x in in_function['doxy']:
            outfile.write(x)
        if not in_function.get('interface', False):
            outfile.write("%s;\n\n" % format_function_str(**in_function))


def write_typedef(typedef, keep_original_code=False):
    global outfile
    if keep_original_code:
        pass
    else:
        for x in typedef['doxy']:
            outfile.write(x)
        outfile.write("struct %s {\n" % typedef['name'])
        for x in typedef['members'].values():
            outfile.write('  %s;' % (
                format_argument(add_mods='cpp', **x)))
            if x['doxy']:
                outfile.write(' //!<%s' % x['doxy'])
            outfile.write('\n')
        outfile.write("};\n\n")


def on_interface_begin(line, m, doxy, keep_original_code=False):
    v = m.groupdict()
    v.update(doxy=doxy,
             members={},
             member_list=[])
    return v


def on_interface_end(x, line, m, keep_original_code=False):
    pass


def on_interface_member(x, line, m, keep_original_code=False):
    global interface_members
    global blocks
    if m:
        blocks['interface'][x['name']]['member_list'].append(m.group('name'))
        interface_members[m.group('name')] = x['name']


def on_function_begin(line, m, doxy, keep_original_code=False):
    v = m.groupdict()
    v.update(interface=interface_members.pop(v['name'], None),
             doxy=doxy)
    if v['args']:
        v['args'] = ','.join([x.strip() for x in v['args'].split(',')])
    if keep_original_code and v['interface'] and (not doxy):
        global outfile
        global blocks
        for x in blocks['interface'][v['interface']]['doxy']:
            outfile.write('  ' + x)
    return v


def on_function_end(x, line, m, keep_original_code=False):
    if x['interface']:
        interface = blocks['interface'][x['interface']]
        interface['members'][x['name']] = x
        if len(interface['members']) == len(interface['member_list']):
            write_interface(interface, keep_original_code=keep_original_code)
    else:
        write_function(x, keep_original_code=keep_original_code)


def on_function_member(x, line, m, keep_original_code=False):
    if m:
        io_var = parse_io(m)
        if x['args'] and any([a in x['args'].split(',')
                              for a in io_var['args']]):
            x.setdefault('arg_props', {})
            for a in x['args'].split(','):
                if a in io_var['args']:
                    x['arg_props'][a] = io_var
                    x['arg_props'][a]['name'] = a
                    break
        elif x['result'] and (x['result'] in io_var['args']):
            x['result_props'] = io_var
            x['result_props']['name'] = x['name']


def on_typedef_begin(line, m, doxy, keep_original_code=False):
    v = m.groupdict()
    v.update(members={},
             doxy=doxy)
    return v


def on_typedef_end(x, line, m, keep_original_code=False):
    write_typedef(x, keep_original_code=keep_original_code)


def on_typedef_member(x, line, m, keep_original_code=False):
    if m:
        typedef = parse_io(m)
        x['members'][typedef['name']] = typedef
    elif not line.strip():
        pass
    # else:
    #     print(line)
    #     import pdb; pdb.set_trace()


def parse_io(m):
    out = m.groupdict()
    typename = m.group('type')
    if typename == '*':
        typename = 'any'
    mods = []
    dim = ''
    if m.group('kind'):
        mods.append('kind=%s' % m.group('kind'))
    if m.group('len'):
        mods.append('len=%s' % m.group('len'))
    if m.group('dim'):
        dim = m.group('dim')
    elif m.group('dim2'):
        dim = m.group('dim2')
    # elif m.group('len'):
    #     dim = m.group('len')
    if mods:
        out['type_mods'] = '(%s)' % ','.join(mods)
    out.update(type=typename, dim=dim,
               args=[x.strip() for x in m.group('name').split(',')])
    out['name'] = ','.join(out['args'])
    return out


def after_parse(re_exp, line, v):
    global outfile
    if ((re_exp.get('keep_original_code', False)
         and (v is not None)
         and (not v.get('interface', False)))):
        if isinstance(line, list):
            for x in line:
                outfile.write(x)
        else:
            outfile.write(line)


def get_regex(filename):
    out = {}
    if filename.endswith('.m'):
        out.update(
            language='matlab',
            comment_char="%",
            doxy_char="%>",
            comments=re.compile(r"([^\%]*)\%.*"),  # noqa: W605
            doxy=re.compile(r"[^']*\%\>(.*)"),
            function_begin=re.compile(
                r"(?P<type>^\s*function)\s*(?P<result>[\] \w\d,_\[]+=)?\s*"
                r"(?P<name>[.\w\d_-]*)\s"r"*\(?(?P<args>[\w\d\s,~]*)\)?"
                r"(?:(%?.*)|(?P<cont>\.\.\.\s*$))"),
            function_end=re.compile(r"^\s*end\;?"))
        out['continue'] = re.compile(r"(?P<body>.*)\s*\.\.\.\s*$")
    elif filename.endswith('.f90'):
        out.update(
            language='fortran',
            comment_char="!",
            # keep_original_code=True,
            comments=re.compile("([^\!]*)\!.*"),  # noqa: W605
            doxy_char="!>",
            doxy=re.compile(r"[^']*\!\>(.*)"),
            function_begin=re.compile(
                r"\s*(?P<type>function|subroutine|FUNCTION|SUBROUTINE)\s*"
                r"(?P<name>[.\w\d_-]*)\s"
                r"*\((?P<args>[\w\d\s,~]*)(\)|(?P<cont>\&))?"
                r"(?:\s+(?:result|RESULT)\s*"
                r"\(\s*(?P<result>[.\w\d_-]+)\s*\))?\s*$"),
            function_partial=re.compile(
                r"(?P<args>[\w\d\s,~]*)(\)|(?P<cont>\&))?"
                r"(?:\s+(?:result|RESULT)\s*"
                r"\(\s*(?P<result>[.\w\d_-]+)\s*\))?\s*$"),
            function_end=re.compile(
                r"\s*(?:end|END)\s+(?:function|subroutine|"
                r"FUNCTION|SUBROUTINE)"
                r"\s+(?P<name>[.\w\d_-]+)\s*$"),
            function_member=re.compile(
                r"\s*(?:(?:type|TYPE|class|CLASS)\()?"
                r"(?P<type>[.\w\d_]+)(?:\))?"
                r"(?:\(\s*(?:"
                r"(?:(?:(?:kind\s*=\s*)?(?P<kind>[.\w\d_]+))|"
                r"(?:(?:len|LEN)\s*=\s*(?P<len>[\:\*\d]+)))(?:\s*\,\s*)?"
                r")+\s*\))?"
                r"(?:(?:\s*\,\s*)(?:"
                r"(?:(?:intent|INTENT)\((?P<dir>in|out|inout)\))|"
                r"(?:(?:dimension|DIMENSION)\((?P<dim>[\:\*\d\,]+)\))|"
                r"(?P<modifier>optional|OPTIONAL|target|TARGET|value|VALUE|"
                r"pointer|POINTER)"
                r"))*"
                r"\s+\:\:\s+(?P<name>[.\w\d_\, ]+)(?:\((?P<dim2>[\:\,]+)\))?"
                r"(?:\s*(?:\=|\=\>)\s*(?P<val>.+))?\s*$"),
            typedef_begin=re.compile(
                r"\s*(?:type|TYPE)\s*\:\:\s*(?P<name>[.\w\d_]+)\s*$"),
            typedef_end=re.compile(
                r"\s*(?:end|END)\s+(?:type|TYPE)\s+(?P<name>[.\w\d_]+)\s*$"),
            typedef_member=re.compile(
                r"\s*(?:(?:type|TYPE|class|CLASS)\()?"
                r"(?P<type>[.\w\d_\*]+)(?:\))?"
                r"(?:\(\s*(?:"
                r"(?:(?:(?:kind\s*=\s*)?(?P<kind>[.\w\d_]+))|"
                r"(?:(?:len|LEN)\s*=\s*(?P<len>[\:\*\d]+)))(?:\s*\,\s*)?"
                r")+\s*\))?"
                r"(?:(?:\s*\,\s*)(?:"
                r"(?:(?:intent|INTENT)\((?P<dir>in|out|inout)\))|"
                r"(?:(?:dimension|DIMENSION)\((?P<dim>[\:\*\d\, ]+)\))|"
                r"(?P<modifier>optional|OPTIONAL|target|TARGET|value|VALUE|"
                r"pointer|POINTER)"
                r"))*"
                r"\s+\:\:\s+(?P<name>[.\w\d_\, ]+)(?:\((?P<dim2>[\:\,]+)\))?"
                r"(?:\s*(?:\=|\=\>)\s*(?P<val>[\.\w\d_\(\)]+))?\s*"
                r"(?:\!\<(?P<doxy>.*))?\s*$"),
            interface_begin=re.compile(
                r"\s*(?:interface|INTERFACE)\s+(?P<name>[.\w\d_]+)\s*$"),
            interface_end=re.compile(
                r"\s*(?:end|END)\s+(?:interface|INTERFACE)\s+"
                r"(?P<name>[.\w\d_]*)\s*$"),
            interface_member=re.compile(
                r"\s*(?P<type>([.\w\d_]+\s+)+)(?P<name>[.\w\d_]+)\s*$"),
            ignore_begin=re.compile(
                r"\s*\!\s+BEGIN\s+DOXYGEN_SHOULD_SKIP_THIS\s*$"),
            ignore_end=re.compile(
                r"\s*\!\s+END\s+DOXYGEN_SHOULD_SKIP_THIS\s*$"),
        )
        out['continue'] = re.compile(r"(?P<body>.*)\s*\&\s*$")
    else:
        pass
    # out['comments'] = re.compile(
    #     r"([^\{}]*)\%.*".format(out['comment_char']))  # noqa: W605
    return out


def filter(filename, out=sys.stdout):
    global outfile
    global blocks
    global interface_members
    global doxy_char
    outfile = out
    re_exp = get_regex(filename)
    if re_exp.get('keep_original_code', False):
        doxy_char = re_exp['doxy_char']
    if not re_exp:
        f = open(filename)
        outfile.write(f.read())
        return
    context = {}
    prev = None
    try:
        f = open(filename)
        r = f.readlines()
        doxygen_comments = []
        for s in r:
            v = None
            # Check for previous line
            if prev:
                s = prev + s.lstrip()
                prev = None
            s_strip = strip_comments(s, re_exp['comments'])
            # Check for partial line
            s_cont = re_exp['continue'].match(s_strip)
            if s_cont:
                prev = s_cont.group('body')
                continue
            # Check if lines should be ignored
            if context.get('ignore', False):
                s_ignore = re_exp['ignore_end'].match(s)
                if s_ignore:
                    context.pop('ignore')
                continue
            elif 'ignore_begin' in re_exp:
                s_ignore = re_exp['ignore_begin'].match(s)
                if s_ignore:
                    context['ignore'] = True
                    continue
            # Check other contexts
            context_break = False
            for k, v in context.items():
                if not v:
                    continue
                context_break = True
                v['code'].append(s_strip)
                s_end = re_exp['%s_end' % k].match(s_strip)
                if s_end:
                    func = eval('on_%s_end' % k)
                    func(v, s, s_end,
                         keep_original_code=re_exp.get(
                             'keep_original_code', False))
                    context.pop(k)
                else:
                    s_mem = None
                    if ('%s_member' % k) in re_exp:
                        s_mem = re_exp['%s_member' % k].match(s)
                        func = eval('on_%s_member' % k)
                        func(v, s_strip, s_mem,
                             keep_original_code=re_exp.get(
                                 'keep_original_code', False))
                break
            if context_break:
                after_parse(re_exp, s, v)
                continue
            # Check for opening new contexts
            for k in re_exp.keys():
                if (k == 'ignore_begin') or (not k.endswith('_begin')):
                    continue
                k = k.split('_begin')[0]
                s_begin = re_exp['%s_begin' % k].match(s_strip)
                if s_begin:
                    context_break = True
                    func = eval('on_%s_begin' % k)
                    v = func(s_strip, s_begin, doxygen_comments,
                             keep_original_code=re_exp.get(
                                 'keep_original_code', False))
                    v['code'] = [s_strip]
                    blocks.setdefault(k, {})
                    blocks[k][v['name']] = v
                    after_parse(re_exp, doxygen_comments, v)
                    doxygen_comments = []
                    context[k] = v
                    break
            if context_break:
                after_parse(re_exp, s, v)
                continue
            # Check for doxygen comment
            if re_exp.get('doxy', False):
                doxy = re_exp['doxy'].match(s)
                if (doxy is not None):
                    doxygen_comments.append(doxy_char + doxy.group(1) + "\n")
                    continue
            after_parse(re_exp, s, v)
    except IOError as e:
        sys.stderr.write(e[1] + "\n")


if len(sys.argv) != 2:
    print("usage: ", sys.argv[0], " filename")
    sys.exit(1)

# Filter the specified file and print the result to stdout
filename = sys.argv[1]
filter(filename)
sys.exit(0)
