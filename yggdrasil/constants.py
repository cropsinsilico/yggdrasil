"""Constants used by yggdrasil."""


# Hard coded to speed-up imports, but there should be a script
# to modify/generate this
LANG2EXT = {'python': '.py',
            'matlab': '.m',
            'r': '.R',
            'c': '.c',
            'cpp': '.cpp',
            'c++': '.cpp',
            'fortran': '.f90',
            'yaml': '.yml'}
EXT2LANG = {v: k for k, v in LANG2EXT.items()}
LANGUAGES = {
    'compiled': [
        'c', 'c++', 'fortran', 'osr', 'cmake', 'make'],
    'interpreted': [
        'python', 'matlab', 'r', 'sbml', 'lpy'],
    'other': [
        'executable', 'timesync']}
LANGUAGES['all'] = (
    LANGUAGES['compiled']
    + LANGUAGES['interpreted']
    + LANGUAGES['other'])
LANGUAGES_WITH_ALIASES = {
    'compiled': [
        'c', 'c++', 'cpp', 'cxx', 'fortran', 'osr', 'cmake', 'make'],
    'interpreted': [
        'python', 'matlab', 'r', 'R', 'sbml', 'lpy'],
    'other': [
        'executable', 'timesync']}
LANGUAGES_WITH_ALIASES['all'] = (
    LANGUAGES_WITH_ALIASES['compiled']
    + LANGUAGES_WITH_ALIASES['interpreted']
    + LANGUAGES_WITH_ALIASES['other'])
