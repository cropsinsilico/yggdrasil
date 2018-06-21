"""Tools for accessing examples from python."""
import os


ex_dict = {'gs_lesson1': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson2': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson3': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson4': ('python', 'matlab', 'c', 'cpp'),
           'gs_lesson4b': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io1': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io2': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io3': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io4': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io5': ('python', 'matlab', 'c', 'cpp'),
           'formatted_io6': ('python', 'matlab', 'c', 'cpp'),
           'rpc_lesson1': ('python', 'matlab', 'c', 'cpp'),
           'rpc_lesson2': ('python', 'matlab', 'c', 'cpp'),
           'hello': ('python', 'matlab', 'c', 'cpp'),
           'model_error': ('python', 'matlab', 'c', 'cpp'),
           'SaM': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'ascii_io': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'rpcFib': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'maxMsg': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab'),
           'timed_pipe': ('python', 'matlab', 'c', 'cpp'),
           'fakeplant': ('python', 'matlab', 'c', 'cpp', 'all', 'all_nomatlab')}
ext_map = {'python': '.py',
           'matlab': '.m',
           'c': '.c',
           'cpp': '.cpp'}
_example_dir = os.path.dirname(__file__)


yamls = {}
source = {}
for k, lang in ex_dict.items():
    yamls[k] = {}
    source[k] = {}
    idir = os.path.join(_example_dir, k)
    isrcdir = os.path.join(idir, 'src')
    for ilang in lang:
        # Get list of yaml & source files
        if k is 'rpcFib':
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
            yml_names = ['%sCli_%s.yml' % (k, cli_l),
                         '%sCliPar_%s.yml' % (k, par_l),
                         '%sSrv_%s.yml' % (k, srv_l)]
            src_names = ['%sCli%s' % (k, ext_map[cli_l]),
                         '%sCliPar%s' % (k, ext_map[par_l]),
                         '%sSrv%s' % (k, ext_map[srv_l])]
        elif k is 'maxMsg':
            if ilang == 'all':
                cli_l = 'python'
                srv_l = 'matlab'
            elif ilang == 'all_nomatlab':
                cli_l = 'python'
                srv_l = 'c'
            else:
                cli_l = ilang
                srv_l = ilang
            yml_names = ['%sCli_%s.yml' % (k, cli_l),
                         '%sSrv_%s.yml' % (k, srv_l)]
            src_names = ['%s%s' % (k, ext_map[cli_l]),
                         '%s%s' % (k, ext_map[srv_l])]
        elif k in ['gs_lesson4', 'gs_lesson4b',
                   'formatted_io1', 'formatted_io2', 'formatted_io3',
                   'formatted_io4', 'formatted_io5', 'formatted_io6']:
            yml_names = ['%s_%s.yml' % (k, ilang)]
            src_names = ['%s_modelA%s' % (k, ext_map[ilang]),
                         '%s_modelB%s' % (k, ext_map[ilang])]
        elif k in ['rpc_lesson1', 'rpc_lesson2']:
            yml_names = ['server_python.yml',
                         'client_%s.yml' % ilang]
            src_names = ['server.py', 'client%s' % ext_map[ilang]]
        elif k == 'fakeplant':
            if ilang.startswith('all'):
                yml_names = ['canopy.yml', 'light.yml', 'photosynthesis.yml',
                             'fakeplant.yml']
                src_names = ['canopy.cpp', 'light.c', 'photosynthesis.py']
                if ilang == 'all_nomatlab':
                    yml_names.append('growth_python.yml')
                    src_names.append('growth.py')
                else:
                    yml_names.append('growth.yml')
                    src_names.append('growth.m')
            elif ilang == 'python':
                yml_names = ['photosynthesis.yml', 'photosynthesis_files.yml']
                src_names = ['photosynthesis.py']
            elif ilang == 'c':
                yml_names = ['light.yml', 'light_files.yml']
                src_names = ['light.c']
            elif ilang == 'cpp':
                yml_names = ['canopy.yml', 'canopy_files.yml']
                src_names = ['canopy.cpp']
            elif ilang == 'matlab':
                yml_names = ['growth.yml', 'growth_files.yml']
                src_names = ['growth.m']
        else:
            yml_names = ['%s_%s.yml' % (k, ilang)]
            if ilang.startswith('all'):
                src_names = []
                for lsrc in lang:
                    if lsrc.startswith('all'):
                        continue
                    if ilang == 'all_nomatlab' and lsrc == 'matlab':
                        continue
                    src_names.append('%s%s' % (k, ext_map[lsrc]))
            else:
                src_names = ['%s%s' % (k, ext_map[ilang])]
        # Add full path to yaml & source files
        yamls[k][ilang] = [os.path.join(idir, y) for y in yml_names]
        source[k][ilang] = [os.path.join(isrcdir, s) for s in src_names]
        if len(yamls[k][ilang]) == 1:
            yamls[k][ilang] = yamls[k][ilang][0]
        if len(source[k][ilang]) == 1:
            source[k][ilang] = source[k][ilang][0]
                                   
              
__all__ = ['yamls', 'source']
