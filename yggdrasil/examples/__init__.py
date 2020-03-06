"""Tools for accessing examples from python."""
import os
import glob
import logging
from yggdrasil import tools, languages, serialize


# TODO: This can be generated from the drivers
ext_map = {'python': '.py',
           'matlab': '.m',
           'r': '.R',
           'c': '.c',
           'cpp': '.cpp',
           'executable': '',
           'make': '.cpp',
           'cmake': '.cpp'}
for lang in tools.get_supported_lang():
    if lang.lower() not in ext_map:
        ext_map[lang.lower()] = languages.get_language_ext(lang)
_example_dir = os.path.dirname(__file__)


def register_example(example_dir):
    r"""Register an example based on the contents of the director.

    Args:
        example_dir (str): Full path to a directory potentially containing an
            example.

    Returns:
        tuple (list, dict, dict): A list of available languages, a dictionary
            mapping from language to YAML specification files for the example,
            and a dictionary mapping from language to source files for the
            example.

    """
    # Check that the source directory and test exist
    example_base = os.path.basename(example_dir)
    srcdir = os.path.join(example_dir, 'src')
    testfile = os.path.join(_example_dir, 'tests',
                            'test_%s.py' % example_base)
    if not os.path.isfile(testfile):  # pragma: no cover
        # TODO: Automate test creation
        logging.error("Missing test file: %s" % testfile)
    assert(os.path.isdir(srcdir))
    # Determine which languages are present in the example
    lang_avail = []
    lang_search = None
    if example_base in ['rpcFib', 'maxMsg']:
        lang_search = example_base + 'Cli_%s.yml'
        lang_avail += ['all', 'all_nomatlab']
    elif example_base.startswith('rpc_'):
        lang_search = 'client_%s.yml'
    elif example_base == 'root_to_shoot':
        lang_avail += ['all', 'all_nomatlab', 'c', 'python']
    elif example_base == 'fakeplant':
        lang_avail += ['all', 'all_nomatlab', 'c', 'cpp', 'matlab', 'python']
    elif example_base in ['types', 'transforms']:
        lang_avail += tools.get_supported_lang()
        for k in ['cmake', 'make', 'lpy', 'executable']:
            lang_avail.remove(k)
    else:
        lang_search = example_base + '_%s.yml'
    if lang_search is not None:
        for match in glob.glob(os.path.join(example_dir, lang_search % '*')):
            lang = serialize.process_message(os.path.basename(match), lang_search)[0]
            if lang == 'valgrind':
                continue
            lang_avail.append(lang.lower())
    lang_avail = tuple(sorted(lang_avail))
    # Get YAML and source files for each language
    out_yml = {}
    out_src = {}
    src_is_abs = False
    for lang in lang_avail:
        yml_names = []
        src_names = []
        if example_base == 'rpcFib':
            if lang == 'all':
                lang_set = ('python', 'matlab', 'c')
            elif lang == 'all_nomatlab':
                lang_set = ('python', 'cpp', 'c')
            else:
                lang_set = (lang, lang, lang)
            yml_names = ['%sCli_%s.yml' % (example_base, lang_set[0]),
                         '%sCliPar_%s.yml' % (example_base, lang_set[1]),
                         '%sSrv_%s.yml' % (example_base, lang_set[2])]
            src_names = ['%sCli%s' % (example_base, ext_map[lang_set[0]]),
                         '%sCliPar%s' % (example_base, ext_map[lang_set[1]]),
                         '%sSrv%s' % (example_base, ext_map[lang_set[2]])]
        elif example_base == 'maxMsg':
            if lang == 'all':
                lang_set = ('python', 'matlab')
            elif lang == 'all_nomatlab':
                lang_set = ('python', 'c')
            else:
                lang_set = (lang, lang)
            yml_names = ['%sCli_%s.yml' % (example_base, lang_set[0]),
                         '%sSrv_%s.yml' % (example_base, lang_set[1])]
            src_names = ['%sCli%s' % (example_base, ext_map[lang_set[0]]),
                         '%sSrv%s' % (example_base, ext_map[lang_set[1]])]
        elif example_base.startswith('rpc_'):
            # TODO: Create server examples in other languages
            yml_names = ['server_python.yml',
                         'client_%s.yml' % lang]
            src_names = ['server.py', 'client%s' % ext_map[lang]]
        elif example_base == 'root_to_shoot':
            if lang.startswith('all'):
                yml_names = ['root.yml', 'shoot.yml', 'root_to_shoot.yml']
                src_names = ['root.c', 'shoot.py']
            elif lang == 'python':
                yml_names = ['shoot.yml', 'shoot_files.yml']
                src_names = ['shoot.py']
            elif lang == 'c':
                yml_names = ['root.yml', 'root_files.yml']
                src_names = ['root.c']
        elif example_base == 'fakeplant':
            if lang.startswith('all'):
                yml_names = ['canopy.yml', 'light.yml', 'photosynthesis.yml',
                             'fakeplant.yml']
                src_names = ['canopy.cpp', 'light.c', 'photosynthesis.py']
                if lang == 'all_nomatlab':
                    yml_names.append('growth_python.yml')
                    src_names.append('growth.py')
                else:
                    yml_names.append('growth.yml')
                    src_names.append('growth.m')
            elif lang == 'python':
                yml_names = ['photosynthesis.yml']
                src_names = ['photosynthesis.py']
            elif lang == 'c':
                yml_names = ['light.yml', 'light_files.yml']
                src_names = ['light.c']
            elif lang == 'cpp':
                yml_names = ['canopy.yml', 'canopy_files.yml']
                src_names = ['canopy.cpp']
            elif lang == 'matlab':
                yml_names = ['growth.yml', 'growth_files.yml']
                src_names = ['growth.m']
        elif example_base in ['types', 'transforms']:
            yml_names = ['%s.yml' % example_base]
            src_names = ['src.py', 'dst.py']
        else:
            src_is_abs = True
            yml_names = ['%s_%s.yml' % (example_base, lang)]
            if lang.startswith('all'):
                src_names = []
                for lsrc in lang_avail:
                    if lsrc.startswith('all'):
                        continue
                    elif (lang == 'all_nomatlab') and (lsrc == 'matlab'):
                        continue
                    src_names += sorted(
                        glob.glob(os.path.join(srcdir,
                                               '*' + ext_map[lsrc])))
            else:
                src_names = sorted(
                    glob.glob(os.path.join(srcdir, '*' + ext_map.get(lang, ''))))
        out_yml[lang] = [os.path.join(example_dir, y) for y in yml_names]
        if src_is_abs:
            out_src[lang] = src_names
        else:
            out_src[lang] = [os.path.join(srcdir, s) for s in src_names]
        if len(out_yml[lang]) == 1:
            out_yml[lang] = out_yml[lang][0]
        if len(out_src[lang]) == 1:
            out_src[lang] = out_src[lang][0]
    return lang_avail, out_yml, out_src


def discover_examples(parent_dir=None):
    r"""Discover examples under the provided parent directory.

    Args:
        parent_dir (str, optional): Parent directory containing example
            directories. Defaults to the directory containing this function if
            not provided.

    Returns:

    Raises:

    """
    out = {'lang': {}, 'yml': {}, 'src': {}}
    if parent_dir is None:
        parent_dir = _example_dir
    for match in sorted(glob.glob(os.path.join(parent_dir, '*'))):
        if match.endswith(('tests', '_')) or (not os.path.isdir(match)):
            continue
        match_base = os.path.basename(match)
        iout = register_example(match)
        for i, k in enumerate(['lang', 'yml', 'src']):
            out[k][match_base] = iout[i]
    return out['lang'], out['yml'], out['src']


ex_dict, yamls, source = discover_examples()


__all__ = ['yamls', 'source']
