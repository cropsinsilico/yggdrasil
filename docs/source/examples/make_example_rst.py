import os
from cis_interface.examples import source, yamls
rst_dir = os.path.dirname(__file__)

lang2print = {'python': 'Python',
              'matlab': 'Matlab',
              'c': 'C',
              'cpp': 'C++',
              'all': 'Mixed',
              'all_nomatlab': 'Mixed w/o Matlab'}


def get_rst_file(k, l):
    rst_file = os.path.join(rst_dir, '%s_%s.rst' % (k, l))
    return rst_file


for k, src in source.items():
    links = []
    for l in sorted(src.keys()):
        rst_file = get_rst_file(k, l)
        links.append("`%s <%s>`__" % (lang2print[l], rst_file))
    alternate_line = "(Example in: %s)\n" % ", ".join(links)
    for l, s in src.items():
        if l.startswith('all'):
            continue
        rst_file = get_rst_file(k, l)
        include_line = ".. literalinclude:: %s\n" % s
        with open(rst_file, 'w') as fd:
            fd.write(include_line)
            fd.write("\n")
            fd.write(alternate_line)
