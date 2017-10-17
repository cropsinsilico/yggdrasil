"""Tools for accessing examples from python."""
import os


ex_dict = {'gs_lesson1': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson2': ('python', 'matlab', 'c', 'cpp'),
           'hello': ('python', 'matlab', 'c', 'cpp'),
           'model_error': ('python', 'matlab', 'c', 'cpp'),
           'SaM': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'ascii_io': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'rpcFib': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'maxMsg': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab')}
ext_map = {'python': '.py',
           'matlab': '.m',
           'c': '.c',
           'cpp': '.cpp'}


yamls = {}
source = {}
for k, lang in ex_dict.items():
    yamls[k] = {}
    source[k] = {}
    if k is 'rpcFib':
        for l in lang:
            if l == 'all':
                cli_l = 'python'
                par_l = 'matlab'
                srv_l = 'c'
            elif l == 'all_nomatlab':
                cli_l = 'python'
                par_l = 'cpp'
                srv_l = 'c'
            else:
                cli_l = l
                par_l = l
                srv_l = l
            yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                        '%sCli_%s.yml' % (k, cli_l)),
                           os.path.join(os.path.dirname(__file__), k,
                                        '%sCliPar_%s.yml' % (k, par_l)),
                           os.path.join(os.path.dirname(__file__), k,
                                        '%sSrv_%s.yml' % (k, srv_l))]
            source[k][l] = [os.path.join(os.path.dirname(__file__), k, 'src', 
                                         '%sCli%s' % (k, ext_map[cli_l])),
                            os.path.join(os.path.dirname(__file__), k, 'src',
                                         '%sCliPar%s' % (k, ext_map[par_l])),
                            os.path.join(os.path.dirname(__file__), k, 'src',
                                         '%sSrv%s' % (k, ext_map[srv_l]))]
    elif k is 'maxMsg':
        for l in lang:
            if l == 'all':
                cli_l = 'python'
                srv_l = 'matlab'
            elif l == 'all_nomatlab':
                cli_l = 'python'
                srv_l = 'c'
            else:
                cli_l = l
                srv_l = l
            yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                        '%sCli_%s.yml' % (k, cli_l)),
                           os.path.join(os.path.dirname(__file__), k,
                                        '%sSrv_%s.yml' % (k, srv_l))]
            source[k][l] = [os.path.join(os.path.dirname(__file__), k, 'src',
                                         '%s%s' % (k, ext_map[cli_l])),
                            os.path.join(os.path.dirname(__file__), k, 'src',
                                         '%s%s' % (k, ext_map[srv_l]))]
    else:
        for l in lang:
            yamls[k][l] = os.path.join(os.path.dirname(__file__), k,
                                       '%s_%s.yml' % (k, l))
            if l.startswith('all'):
                source[k][l] = []
                for lsrc in lang:
                    if lsrc.startswith('all'):
                        continue
                    if l == 'all_nomatlab' and lsrc == 'matlab':
                        continue
                    source[k][l].append(
                        os.path.join(os.path.dirname(__file__), k, 'src',
                                     '%s%s' % (k, ext_map[lsrc])))
            else:
                source[k][l] = os.path.join(os.path.dirname(__file__), k, 'src',
                                            '%s%s' % (k, ext_map[l]))
                                   
              
__all__ = ['yamls', 'source']
