"""Tools for accessing examples from python."""
import os


ex_dict = {'hello': ('python', 'matlab', 'c', 'cpp'),
           'SaM': ('python', 'matlab', 'c', 'cpp', 'all'),
           'ascii_io': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'rpcFib': ('python', 'matlab', 'c', 'all')}


yamls = {}
for k, lang in ex_dict.items():
    yamls[k] = {}
    if k is 'rpcFib':
        for l in lang:
            if l == 'all':
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, 'python')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sCliPar_%s.yml' % (k, 'cpp')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, 'c'))]
            else:
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sCliPar_%s.yml' % (k, l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, l))]
    else:
        for l in lang:
            yamls[k][l] = os.path.join(os.path.dirname(__file__), k,
                                       '%s_%s.yml' % (k, l))
                                   
              
# yaml_list = [
#     ('ascii_io_python', 'ascii_io', 'ascii_io_Python'),
#     ('ascii_io_matlab', 'ascii_io', 'ascii_io_Matlab'),
#     ('ascii_io_gcc', 'ascii_io', 'ascii_io_GCC'),
#     ('ascii_io_all', 'ascii_io', 'ascii_io_all'),
#     ('sam_python', 'SaM', 'SaM_Python'),
#     ('sam_matlab', 'SaM', 'SaM_Matlab'),
#     ('sam_gcc', 'SaM', 'SaM_GCC'),
#     ('sam_all', 'SaM-multi', 'integrated'),
#     ('hello_python', 'python', 'hellopython'),
#     ('hello_matlab', 'matlab', 'helloMatlab'),
#     ('hello_gcc', ('cpp', 'hello'), 'hello_c.yml'),
#     ('rpcfib_python', ('python', 'rpcFib'),
#      ('rpcFibCli', 'rpcFibCliPar', 'rpcFibSrv')),
#     ('rpcfib_matlab', ('matlab', 'rpcFib'),
#      ('rpcFibCli', 'rpcFibCliPar', 'rpcFibSrv')),
#     ('rpcfib_gcc', ('cpp', 'rpcFib'),
#      ('rpcFibCli', 'rpcFibCliPar', 'rpcFibSrv'))
# ]
# yamls = {}
# for k, d, f in yaml_list:
#     if isinstance(d, str):
#         dtup = [d]
#     else:
#         dtup = list(d)
#     alldir = os.path.join(os.path.dirname(__file__), *dtup)
#     if isinstance(f, str):
#         yamls[k] = os.path.join(alldir, f + '.yml')
#     else:
#         yamls[k] = []
#         for iyml in f:
#             yamls[k].append(
#                 os.path.join(alldir, iyml + '.yml'))


__all__ = ['yamls']
