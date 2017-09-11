"""Tools for accessing examples from python."""
import os


ex_dict = {'hello': ('python', 'matlab', 'c'),
           'ascii_io': ('python', 'matlab', 'c', 'all')}


yamls = {}
for k, lang in ex_dict.items():
    yamls[k] = {}
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
