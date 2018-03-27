"""Tools for accessing examples from python."""
import os


ex_dict = {'gs_lesson1': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson2': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson3': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson4': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson5': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io1': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io2': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io3': ('python', 'matlab', 'c', 'cpp'),
           'hello': ('python', 'matlab', 'c', 'cpp'),
           'model_error': ('python', 'matlab', 'c', 'cpp'),
           'SaM': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'ascii_io': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'rpcFib': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'maxMsg': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'timed_pipe': ('python', 'matlab', 'c', 'cpp')}
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
        for ilang in lang:
            if ilang == 'all':
                cli_l = 'python'
                par_l = 'matlab'
                srv_l = 'c'
            elif ilang == 'all_nomatlab':
                cli_l = 'python'
                par_l = 'cpp'
                srv_l = 'c'
            else:
                cli_l = ilang
                par_l = ilang
                srv_l = ilang
            yamls[k][ilang] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, cli_l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sCliPar_%s.yml' % (k, par_l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, srv_l))]
            source[k][ilang] = [os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%sCli%s' % (k, ext_map[cli_l])),
                                os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%sCliPar%s' % (k, ext_map[par_l])),
                                os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%sSrv%s' % (k, ext_map[srv_l]))]
    elif k is 'maxMsg':
        for ilang in lang:
            if ilang == 'all':
                cli_l = 'python'
                srv_l = 'matlab'
            elif ilang == 'all_nomatlab':
                cli_l = 'python'
                srv_l = 'c'
            else:
                cli_l = ilang
                srv_l = ilang
            yamls[k][ilang] = [os.path.join(os.path.dirname(__file__), k,
                                            '%sCli_%s.yml' % (k, cli_l)),
                               os.path.join(os.path.dirname(__file__), k,
                                            '%sSrv_%s.yml' % (k, srv_l))]
            source[k][ilang] = [os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%s%s' % (k, ext_map[cli_l])),
                                os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%s%s' % (k, ext_map[srv_l]))]
    elif k in ['gs_lesson4', 'gs_lesson5',
               'formatted_io1', 'formatted_io2', 'formatted_io3']:
        for ilang in lang:
            yamls[k][ilang] = os.path.join(os.path.dirname(__file__), k,
                                           '%s_%s.yml' % (k, ilang))
            source[k][ilang] = [os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%s_modelA%s' % (k, ext_map[ilang])),
                                os.path.join(os.path.dirname(__file__), k, 'src',
                                             '%s_modelB%s' % (k, ext_map[ilang]))]
    else:
        for ilang in lang:
            yamls[k][ilang] = os.path.join(os.path.dirname(__file__), k,
                                           '%s_%s.yml' % (k, ilang))
            if ilang.startswith('all'):
                source[k][ilang] = []
                for lsrc in lang:
                    if lsrc.startswith('all'):
                        continue
                    if ilang == 'all_nomatlab' and lsrc == 'matlab':
                        continue
                    source[k][ilang].append(
                        os.path.join(os.path.dirname(__file__), k, 'src',
                                     '%s%s' % (k, ext_map[lsrc])))
            else:
                source[k][ilang] = os.path.join(os.path.dirname(__file__), k, 'src',
                                                '%s%s' % (k, ext_map[ilang]))
                                   
              
__all__ = ['yamls', 'source']
