"""Tools for accessing examples from python."""
import os


ex_dict = {'hello': ('python', 'matlab', 'c', 'cpp'),
           'model_error': ('python', 'matlab', 'c', 'cpp'),
           'SaM': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'ascii_io': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'rpcFib': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'maxMsg': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab')}


yamls = {}
for k, lang in ex_dict.items():
    yamls[k] = {}
    if k is 'rpcFib':
        for l in lang:
            if l == 'all':
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, 'python')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sCliPar_%s.yml' % (k, 'matlab')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, 'c'))]
            elif l == 'all_nomatlab':
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
    elif k is 'maxMsg':
        for l in lang:
            if l == 'all':
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, 'python')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, 'matlab'))]
            elif l == 'all_nomatlab':
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, 'python')),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, 'c'))]
            else:
                yamls[k][l] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, l))]
    else:
        for l in lang:
            yamls[k][l] = os.path.join(os.path.dirname(__file__), k,
                                       '%s_%s.yml' % (k, l))
                                   
              
__all__ = ['yamls']
