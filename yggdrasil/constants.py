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
        'c', 'c++', 'fortran'],
    'compiled_dsl': [
        'osr'],
    'interpreted': [
        'python', 'matlab', 'r'],
    'interpreted_dsl': [
        'sbml', 'lpy'],
    'build': [
        'cmake', 'make'],
    'other': [
        'executable', 'timesync']}
LANGUAGES['all'] = (
    LANGUAGES['compiled']
    + LANGUAGES['interpreted']
    + LANGUAGES['build']
    + LANGUAGES['other'])
LANGUAGES_WITH_ALIASES = {
    'compiled': [
        'c', 'c++', 'cpp', 'cxx', 'fortran'],
    'compiled_dsl': [
        'osr'],
    'interpreted': [
        'python', 'matlab', 'r', 'R'],
    'interpreted_dsl': [
        'sbml', 'lpy'],
    'build': [
        'cmake', 'make'],
    'other': [
        'executable', 'timesync']}
LANGUAGES_WITH_ALIASES['all'] = (
    LANGUAGES_WITH_ALIASES['compiled']
    + LANGUAGES_WITH_ALIASES['interpreted']
    + LANGUAGES_WITH_ALIASES['build']
    + LANGUAGES_WITH_ALIASES['other'])
COMPILER_ENV_VARS = {
    'c': {
        'exec': 'CC',
        'flags': 'CFLAGS'},
    'c++': {
        'exec': 'CXX',
        'flags': 'CXXFLAGS'},
    'fortran': {
        'exec': 'FC',
        'flags': 'FFLAGS'}}
COMPILATION_TOOL_VARS = {
    'ld': {
        'exec': 'LD',
        'flags': 'LDFLAGS'},
    'ar': {
        'exec': 'AR'},
    'libtool': {
        'exec': 'LIBTOOL'}}
