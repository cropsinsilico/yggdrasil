"""Constants used by yggdrasil."""
import numpy as np
from collections import OrderedDict
# No other yggdrasil modules should be import here
# TODO: Move platform constants into this module?
from yggdrasil import platform


# Type related constants
NUMPY_NUMERIC_TYPES = [
    'int',
    'uint',
    'float',
    'complex',
]
NUMPY_STRING_TYPES = [
    'bytes',
    'unicode',
    'str',
]
NUMPY_TYPES = NUMPY_NUMERIC_TYPES + NUMPY_STRING_TYPES
FLEXIBLE_TYPES = [
    'string',
    'bytes',
    'unicode',
]
PYTHON_SCALARS = OrderedDict([
    ('float', [float]),
    ('int', [int]),
    ('uint', []),
    ('complex', [complex]),
    ('string', [bytes]),
    ('bytes', [bytes]),
    ('unicode', [str]),
    ('number', [float]),
    ('integer', [int]),
])
VALID_TYPES = OrderedDict([(k, k) for k in NUMPY_NUMERIC_TYPES])
VALID_TYPES.update([
    ('string', 'bytes'),
    ('bytes', 'bytes'),
    ('unicode', 'str'),
    ('number', 'float'),
    ('integer', 'int'),
])
NUMPY_PRECISIONS = {
    'float': [16, 32, 64],
    'int': [8, 16, 32, 64],
    'uint': [8, 16, 32, 64],
    'complex': [64, 128],
}
if not platform._is_win:
    # Not available on windows
    NUMPY_PRECISIONS['float'].append(128)
    NUMPY_PRECISIONS['complex'].append(256)
for T, T_NP in VALID_TYPES.items():
    PYTHON_SCALARS[T].append(np.dtype(T_NP).type)
    if T in NUMPY_PRECISIONS:
        PYTHON_SCALARS[T] += [np.dtype(T_NP + str(P)).type
                              for P in NUMPY_PRECISIONS[T]]
PYTHON_SCALARS['int'].append(np.signedinteger)
PYTHON_SCALARS['uint'].append(np.unsignedinteger)
ALL_PYTHON_SCALARS = []
for k, v in PYTHON_SCALARS.items():
    PYTHON_SCALARS[k] = tuple(v)
    ALL_PYTHON_SCALARS += list(v)
ALL_PYTHON_SCALARS = tuple(set(ALL_PYTHON_SCALARS))
ALL_PYTHON_ARRAYS = (np.ndarray,)
ENCODING_SIZES = {
    "UTF8": 4,
    "UCS4": 4,
    "ASCII": 1
}


# Serialization constants
FMT_CHAR = b'%'
YGG_MSG_HEAD = b'YGG_MSG_HEAD'
DEFAULT_COMMENT = b'# '
DEFAULT_DELIMITER = b'\t'
DEFAULT_NEWLINE = b'\n'
FMT_CHAR_STR = FMT_CHAR.decode("utf-8")
DEFAULT_COMMENT_STR = DEFAULT_COMMENT.decode("utf-8")
DEFAULT_DELIMITER_STR = DEFAULT_DELIMITER.decode("utf-8")
DEFAULT_NEWLINE_STR = DEFAULT_NEWLINE.decode("utf-8")
DEFAULT_DATATYPE = {'type': 'scalar', 'subtype': 'string'}


# Communication constants
YGG_MSG_EOF = b'EOF!!!'
YGG_MSG_BUF = 1024 * 2
YGG_CLIENT_INI = b'YGG_BEGIN_CLIENT'
YGG_CLIENT_EOF = b'YGG_END_CLIENT'


# ======================================================
# Do not edit this file past this point as the following
# is generated by yggdrasil.schema.update_constants
# ======================================================


# Component registry
COMPONENT_REGISTRY = {
    'comm': {
        'base': 'CommBase',
        'default': 'default',
        'key': 'commtype',
        'module': 'yggdrasil.communication',
        'subtypes': {
            'buffer': 'BufferComm',
            'default': 'DefaultComm',
            'ipc': 'IPCComm',
            'mpi': 'MPIComm',
            'rest': 'RESTComm',
            'rmq': 'RMQComm',
            'rmq_async': 'RMQAsyncComm',
            'value': 'ValueComm',
            'zmq': 'ZMQComm',
        },
    },
    'connection': {
        'base': 'ConnectionDriver',
        'default': None,
        'key': 'connection_type',
        'module': 'yggdrasil.drivers',
        'subtypes': {
            'connection': 'ConnectionDriver',
            'file_input': 'FileInputDriver',
            'file_output': 'FileOutputDriver',
            'input': 'InputDriver',
            'output': 'OutputDriver',
            'rpc_request': 'RPCRequestDriver',
            'rpc_response': 'RPCResponseDriver',
        },
    },
    'file': {
        'base': 'FileComm',
        'default': 'binary',
        'key': 'filetype',
        'module': 'yggdrasil.communication',
        'subtypes': {
            'ascii': 'AsciiFileComm',
            'binary': 'FileComm',
            'json': 'JSONFileComm',
            'map': 'AsciiMapComm',
            'mat': 'MatFileComm',
            'netcdf': 'NetCDFFileComm',
            'obj': 'ObjFileComm',
            'pandas': 'PandasFileComm',
            'pickle': 'PickleFileComm',
            'ply': 'PlyFileComm',
            'table': 'AsciiTableComm',
            'wofost': 'WOFOSTParamFileComm',
            'yaml': 'YAMLFileComm',
        },
    },
    'filter': {
        'base': 'FilterBase',
        'default': None,
        'key': 'filtertype',
        'module': 'yggdrasil.communication.filters',
        'subtypes': {
            'direct': 'DirectFilter',
            'function': 'FunctionFilter',
            'statement': 'StatementFilter',
        },
    },
    'model': {
        'base': 'ModelDriver',
        'default': 'executable',
        'key': 'language',
        'module': 'yggdrasil.drivers',
        'subtypes': {
            'R': 'RModelDriver',
            'c': 'CModelDriver',
            'c++': 'CPPModelDriver',
            'cmake': 'CMakeModelDriver',
            'cpp': 'CPPModelDriver',
            'cxx': 'CPPModelDriver',
            'dummy': 'DummyModelDriver',
            'executable': 'ExecutableModelDriver',
            'fortran': 'FortranModelDriver',
            'lpy': 'LPyModelDriver',
            'make': 'MakeModelDriver',
            'matlab': 'MatlabModelDriver',
            'mpi': 'MPIPartnerModel',
            'osr': 'OSRModelDriver',
            'python': 'PythonModelDriver',
            'r': 'RModelDriver',
            'sbml': 'SBMLModelDriver',
            'timesync': 'TimeSyncModelDriver',
        },
    },
    'serializer': {
        'base': 'SerializeBase',
        'default': 'default',
        'key': 'seritype',
        'module': 'yggdrasil.serialize',
        'subtypes': {
            'default': 'DefaultSerialize',
            'direct': 'DirectSerialize',
            'functional': 'FunctionalSerialize',
            'json': 'JSONSerialize',
            'map': 'AsciiMapSerialize',
            'mat': 'MatSerialize',
            'obj': 'ObjSerialize',
            'pandas': 'PandasSerialize',
            'pickle': 'PickleSerialize',
            'ply': 'PlySerialize',
            'table': 'AsciiTableSerialize',
            'wofost': 'WOFOSTParamSerialize',
            'yaml': 'YAMLSerialize',
        },
    },
    'transform': {
        'base': 'TransformBase',
        'default': None,
        'key': 'transformtype',
        'module': 'yggdrasil.communication.transforms',
        'subtypes': {
            'array': 'ArrayTransform',
            'direct': 'DirectTransform',
            'filter': 'FilterTransform',
            'function': 'FunctionTransform',
            'iterate': 'IterateTransform',
            'map_fields': 'MapFieldsTransform',
            'pandas': 'PandasTransform',
            'select_fields': 'SelectFieldsTransform',
            'statement': 'StatementTransform',
        },
    },
}

# Language driver constants
LANG2EXT = {
    'R': '.R',
    'c': '.c',
    'c++': '.cpp',
    'cpp': '.cpp',
    'cxx': '.cpp',
    'executable': '.exe',
    'fortran': '.f90',
    'lpy': '.lpy',
    'matlab': '.m',
    'osr': '.xml',
    'python': '.py',
    'r': '.R',
    'sbml': '.xml',
    'yaml': '.yml',
}
EXT2LANG = {v: k for k, v in LANG2EXT.items()}
LANGUAGES = {
    'compiled': [
        'c', 'c++', 'fortran'],
    'interpreted': [
        'R', 'matlab', 'python'],
    'build': [
        'cmake', 'make'],
    'dsl': [
        'lpy', 'osr', 'sbml'],
    'other': [
        'dummy', 'executable', 'mpi', 'timesync'],
}
LANGUAGES['all'] = (
    LANGUAGES['compiled']
    + LANGUAGES['interpreted']
    + LANGUAGES['build']
    + LANGUAGES['dsl']
    + LANGUAGES['other'])
LANGUAGES_WITH_ALIASES = {
    'compiled': [
        'c', 'c++', 'cpp', 'cxx', 'fortran'],
    'interpreted': [
        'R', 'matlab', 'python', 'r'],
    'build': [
        'cmake', 'make'],
    'dsl': [
        'lpy', 'osr', 'sbml'],
    'other': [
        'dummy', 'executable', 'mpi', 'timesync'],
}
LANGUAGES_WITH_ALIASES['all'] = (
    LANGUAGES_WITH_ALIASES['compiled']
    + LANGUAGES_WITH_ALIASES['interpreted']
    + LANGUAGES_WITH_ALIASES['build']
    + LANGUAGES_WITH_ALIASES['dsl']
    + LANGUAGES_WITH_ALIASES['other'])
ALIASED_LANGUAGES = {
    'R': [
        'R', 'r'],
    'c++': [
        'c++', 'cpp', 'cxx'],
}
COMPILER_ENV_VARS = {
    'c': {
        'exec': 'CC',
        'flags': 'CFLAGS',
    },
    'c++': {
        'exec': 'CXX',
        'flags': 'CXXFLAGS',
    },
    'fortran': {
        'exec': 'FC',
        'flags': 'FFLAGS',
    },
}
COMPILATION_TOOL_VARS = {
    'LIB': {
        'exec': None,
        'flags': None,
    },
    'LINK': {
        'exec': 'LINK',
        'flags': 'LDFLAGS',
    },
    'ar': {
        'exec': 'AR',
        'flags': None,
    },
    'cl': {
        'exec': 'CC',
        'flags': 'CFLAGS',
    },
    'cl++': {
        'exec': 'CXX',
        'flags': 'CXXFLAGS',
    },
    'clang': {
        'exec': 'CC',
        'flags': 'CFLAGS',
    },
    'clang++': {
        'exec': 'CXX',
        'flags': 'CXXFLAGS',
    },
    'cmake': {
        'exec': None,
        'flags': None,
    },
    'g++': {
        'exec': 'CXX',
        'flags': 'CXXFLAGS',
    },
    'gcc': {
        'exec': 'CC',
        'flags': 'CFLAGS',
    },
    'gfortran': {
        'exec': 'FC',
        'flags': 'FFLAGS',
    },
    'ld': {
        'exec': 'LD',
        'flags': 'LDFLAGS',
    },
    'libtool': {
        'exec': 'LIBTOOL',
        'flags': None,
    },
    'make': {
        'exec': None,
        'flags': None,
    },
    'nmake': {
        'exec': None,
        'flags': None,
    },
}
LANGUAGE_PROPERTIES = {
    'R': {
        'executable_type': 'interpreted',
        'full_language': True,
        'is_typed': False,
    },
    'c': {
        'executable_type': 'compiled',
        'full_language': True,
        'is_typed': True,
    },
    'c++': {
        'executable_type': 'compiled',
        'full_language': True,
        'is_typed': True,
    },
    'cmake': {
        'executable_type': 'build',
        'full_language': False,
        'is_typed': False,
    },
    'dummy': {
        'executable_type': 'other',
        'full_language': False,
        'is_typed': False,
    },
    'executable': {
        'executable_type': 'other',
        'full_language': False,
        'is_typed': False,
    },
    'fortran': {
        'executable_type': 'compiled',
        'full_language': True,
        'is_typed': True,
    },
    'lpy': {
        'executable_type': 'dsl',
        'full_language': False,
        'is_typed': False,
    },
    'make': {
        'executable_type': 'build',
        'full_language': False,
        'is_typed': False,
    },
    'matlab': {
        'executable_type': 'interpreted',
        'full_language': True,
        'is_typed': False,
    },
    'mpi': {
        'executable_type': 'other',
        'full_language': False,
        'is_typed': False,
    },
    'osr': {
        'executable_type': 'dsl',
        'full_language': False,
        'is_typed': False,
    },
    'python': {
        'executable_type': 'interpreted',
        'full_language': True,
        'is_typed': False,
    },
    'sbml': {
        'executable_type': 'dsl',
        'full_language': False,
        'is_typed': False,
    },
    'timesync': {
        'executable_type': 'other',
        'full_language': False,
        'is_typed': False,
    },
}
