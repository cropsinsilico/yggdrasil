import os
from yggdrasil.examples import source, yamls
from yggdrasil import doctools


rst_dir = os.path.dirname(os.path.abspath(__file__))
toc_file = os.path.join(rst_dir, 'examples_toc.rst')
lang2print = {'python': 'Python',
              'matlab': 'Matlab',
              'cmake': 'CMake',
              'make': 'Make',
              'r': 'R',
              'R': 'R',
              'c': 'C',
              'cpp': 'C++',
              'all': 'Mixed',
              'all_nomatlab': 'Mixed w/o Matlab',
              'fortran': 'Fortran',
              'sbml': 'SBML',
              'osr': 'OpenSimRoot',
              'dummy': 'Dummy',
              'timesync': 'Timesync'}
_default_lang = ['python', 'cpp', 'c', 'R', 'fortran', 'matlab', 'sbml']


def get_file(fname, local=False):
    if local:
        return os.path.join(rst_dir, fname)
    else:
        return fname


def get_rst_file(k, local=False):
    return get_file('%s.rst' % (k), local=local)


def get_html_file(k, local=False):
    return get_file('%s.html' % (k), local=local)


def get_src_file(k, local=False):
    return get_file('%s_src.rst' % (k), local=local)


def get_yml_file(k, local=False):
    return get_file('%s_yml.rst' % (k), local=local)


def make_toc_file(key_list):
    with open(toc_file, 'w') as fd:
        write_toc_file(fd, key_list)


def make_rst_file(k):
    fname = get_rst_file(k, local=True)
    with open(fname, 'w') as fd:
        write_rst(fd, k)
    make_src_file(k)
    make_yml_file(k)

        
def make_src_file(k):
    fname = get_src_file(k, local=True)
    with open(fname, 'w') as fd:
        write_src_ref(fd, k)

        
def make_yml_file(k):
    fname = get_yml_file(k, local=True)
    with open(fname, 'w') as fd:
        write_yml_ref(fd, k)

        
def get_rel_path(fname, upone=False):
    if upone:
        top_dir = os.path.dirname(rst_dir)
    else:
        top_dir = rst_dir
    return os.path.relpath(fname, top_dir)


def get_default_lang(k):
    if k == 'rpc_lesson3b':
        return 'cpp'
    else:
        for x in _default_lang:
            if x in source[k]:
                return x


def write_src_ref(fd, k):
    default = get_default_lang(k)
    assert(default)
    write_src(fd, k, default, upone=True)
    fd.write('\n')
    write_ref_link(fd, k)

    
def write_yml_ref(fd, k):
    default = get_default_lang(k)
    assert(default)
    write_yml(fd, k, default, upone=True)
    fd.write('\n')
    write_ref_link(fd, k)


def write_ref_link(fd, k):
    fd.write("(`%s <%s>`__)\n" % ('Example in other languages',
                                  os.path.join('examples', get_html_file(k))))


def write_toc_file(fd, key_list):
    head = "Examples"
    fd.write('.. _examples_rst:\n\n%s\n' % head)
    fd.write((len(head) * '=') + '\n\n')
    data = {}
    for k in key_list:
        if not yamls[k]:
            continue
        key = ':ref:`%s_rst`' % k
        data[key] = get_readme(k)
    kwargs = {'key_column_name': 'Name', 'val_column_name': 'Description'}
    lines = doctools.dict2table(data, **kwargs)
    fd.write('\n'.join(lines))
    # fd.write(".. toctree::\n\n")
    # for k in key_list:
    #     fd.write("   %s\n" % get_rst_file(k).split('.rst')[0])
    # fd.write("\n")


def get_readme(k):
    yaml = next(iter(yamls[k].values()))
    if isinstance(yaml, list):
        yaml = yaml[0]
    readme = os.path.join(os.path.dirname(yaml), 'README.rst')
    if os.path.isfile(readme):
        with open(readme, 'r') as read_fd:
            contents = read_fd.read()
            return contents
    return ''
        

def write_rst(fd, k):
    head = '.. _%s_rst:\n\n%s' % (k, k)
    fd.write(head + '\n')
    fd.write((len(head) * '=') + '\n\n')
    readme = get_readme(k)
    if readme:
        fd.write('%s\n\n' % readme)
    fd.write('.. contents:: :local:\n\n')
    for lang in source[k]:
        write_lang(fd, k, lang)
        fd.write('\n')


def write_lang(fd, k, lang):
    head = '%s Version' % lang2print[lang]
    fd.write(head + '\n')
    fd.write((len(head) * '-') + '\n\n')
    write_src(fd, k, lang)
    fd.write('\n')
    write_yml(fd, k, lang)
    fd.write('\n')

    
def write_code_line(fd, s, upone=False, language=None,
                    replacements=[]):
    p = os.path.sep + get_rel_path(s, upone=True)
    if replacements:
        pdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        pnew = os.path.join(pdir, os.path.basename(s))
        if not os.path.isdir(pdir):
            os.mkdir(pdir)
        with open(s, 'r') as pfd:
            contents = pfd.read()
        for x, y in replacements:
            contents = contents.replace(x, y)
        with open(pnew, 'w') as pfd:
            pfd.write(contents)
        p = os.path.sep + get_rel_path(pnew, upone=True)
    ext2lang = {'.yml': 'yaml', '.py': 'python',
                '.c': 'c', '.cpp': 'c++', '.m': 'matlab'}
    if language is None:
        ext = os.path.splitext(p)[-1]
        language = ext2lang.get(ext, 'python')
    fd.write(".. literalinclude:: %s\n" % p)
    fd.write("   :language: %s\n" % language)
    fd.write("   :linenos:\n")
    # fd.write(".. include:: %s\n" % get_rel_path(s, upone=upone))
    # fd.write("   :code: %s\n" % language)
    # fd.write("   :number-lines:\n")
    fd.write("\n")


def write_src(fd, k, lang, upone=False):
    fd.write("Model Code:\n\n")
    if isinstance(source[k][lang], list):
        for s in source[k][lang]:
            write_code_line(fd, s, upone=upone)
    else:
        write_code_line(fd, source[k][lang], upone=upone)

    
def write_yml(fd, k, lang, upone=False):
    fd.write("Model YAML:\n\n")
    replacements = []
    if k.startswith('timesync'):
        replacements = [('{{TIMESYNC_TSTEP_A}}', '7'),
                        ('{{TIMESYNC_TSTEP_B}}', '1')]
    if isinstance(yamls[k][lang], list):
        for y in yamls[k][lang]:
            write_code_line(fd, y, upone=upone, language='yaml',
                            replacements=replacements)
    else:
        write_code_line(fd, yamls[k][lang], upone=upone, language='yaml',
                        replacements=replacements)

        
rst_examples = source.keys()
make_toc_file(rst_examples)
for k in rst_examples:
    if not yamls[k]:
        continue
    make_rst_file(k)
