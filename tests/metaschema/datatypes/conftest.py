import pytest
import copy
import numpy as np


@pytest.fixture(scope="session")
def container_values():
    r"""list: Value for container tests"""
    return [np.float32(1),
            b'hello', u'hello',
            {'nested': np.int64(2)},
            [np.complex128(4), np.uint8(0)]]


@pytest.fixture(scope="session")
def container_values_count(container_values):
    r"""int: Number of container values."""
    return len(container_values)


@pytest.fixture(scope="session")
def container_definitions():
    r"""list: Definitions for container types."""
    return [{'type': 'float',
             'precision': 32,
             'units': ''},
            {'type': 'bytes',
             'precision': 40,
             'units': ''},
            {'type': 'unicode',
             'precision': 40,
             'units': ''},
            {'type': 'object',
             'properties': {'nested': {'type': 'int',
                                       'precision': 64,
                                       'units': ''}}},
            {'type': 'array',
             'items': [{'type': 'complex',
                        'precision': 128,
                        'units': ''},
                       {'type': 'uint',
                        'precision': 8,
                        'units': ''}]}]


@pytest.fixture(scope="session")
def container_typedefs(container_definitions):
    r"""list: Typedefs for container types."""
    out = []
    for v in container_definitions:
        itypedef = {'type': v['type']}
        if v['type'] == 'object':
            itypedef['properties'] = copy.deepcopy(v['properties'])
        elif v['type'] == 'array':
            itypedef['items'] = copy.deepcopy(v['items'])
        out.append(itypedef)
    return out


@pytest.fixture(scope="session")
def ply_test_value():
    r"""Complex example Ply dictionary."""
    vcoords = np.array([[0, 0, 0, 0, 1, 1, 1, 1],
                        [0, 0, 1, 1, 0, 0, 1, 1],
                        [0, 1, 1, 0, 0, 1, 1, 0]], 'float32').T
    vcolors = np.array([[255, 255, 255, 255, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 255, 255, 255, 255]], 'uint8').T
    eindexs = np.array([[0, 1, 2, 3, 2],
                        [1, 2, 3, 0, 0]], 'int32')
    ecolors = np.array([[255, 255, 255, 255, 0],
                        [255, 255, 255, 255, 0],
                        [255, 255, 255, 255, 0]], 'uint8')
    out = {'material': 'fake_material', 'vertices': [], 'edges': [],
           'faces': [{'vertex_index': [0, 1, 2]},
                     {'vertex_index': [0, 2, 3]},
                     {'vertex_index': [7, 6, 5, 4]},
                     {'vertex_index': [0, 4, 5, 1]},
                     {'vertex_index': [1, 5, 6, 2]},
                     {'vertex_index': [2, 6, 7, 3]},
                     {'vertex_index': [3, 7, 4, 0]}]}
    for i in range(len(vcoords)):
        ivert = {}
        for j, k in enumerate('xyz'):
            ivert[k] = vcoords[i, j]
        for j, k in enumerate(['red', 'green', 'blue']):
            ivert[k] = vcolors[i, j]
        out['vertices'].append(ivert)
    for i in range(len(eindexs)):
        iedge = {}
        for j, k in enumerate(['vertex1', 'vertex2']):
            iedge[k] = eindexs[i, j]
        for j, k in enumerate(['red', 'green', 'blue']):
            iedge[k] = ecolors[i, j]
        out['edges'].append(iedge)
    for f in out['faces']:
        f['vertex_index'] = [np.int32(x) for x in f['vertex_index']]
    return out


@pytest.fixture(scope="session")
def ply_test_value_simple(ply_test_value):
    r"""Simple example Ply dictionary."""
    return {'vertices': copy.deepcopy(ply_test_value['vertices']),
            'faces': [{'vertex_index': [0, 1, 2]},
                      {'vertex_index': [0, 2, 3]}]}


@pytest.fixture(scope="session")
def ply_test_value_int64(ply_test_value):
    r"""Version of example Ply dictionary using 64bit integers."""
    out = copy.deepcopy(ply_test_value)
    for f in out['faces']:
        f['vertex_index'] = [np.int64(x) for x in f['vertex_index']]
    return out


@pytest.fixture(scope="session")
def obj_test_value(ply_test_value):
    r"""Complex example Obj dictionary."""
    out = {'vertices': [], 'faces': [], 'lines': [],
           'params': [{'u': 0.0, 'v': 0.0, 'w': 0.5},
                      {'u': 0.0, 'v': 0.0}],
           'normals': [{'i': 0.0, 'j': 0.0, 'k': 0.0},
                       {'i': 1.0, 'j': 1.0, 'k': 1.0}],
           'texcoords': [{'u': 0.0, 'v': 0.0, 'w': 0.5},
                         {'u': 1.0, 'v': 0.5},
                         {'u': 1.0}],
           'points': [[0, 2]],
           'curves': [{'starting_param': 0.0, 'ending_param': 1.0,
                       'vertex_indices': [0, 1]}],
           'curve2Ds': [[0, 1]],
           'surfaces': [{
               'starting_param_u': 0.0, 'ending_param_u': 1.0,
               'starting_param_v': 0.0, 'ending_param_v': 1.0,
               'vertex_indices': [{'vertex_index': 0,
                                   'texcoord_index': 0,
                                   'normal_index': 0},
                                  {'vertex_index': 1,
                                   'texcoord_index': 1,
                                   'normal_index': 1}]}]}
    out['material'] = ply_test_value['material']
    out['vertices'] = copy.deepcopy(ply_test_value['vertices'])
    out['vertices'][0]['w'] = 0.5
    for f in ply_test_value['faces']:
        new = [{'vertex_index': x, 'texcoord_index': 0, 'normal_index': 0}
               for x in f['vertex_index']]
        out['faces'].append(new)
    for e in ply_test_value['edges']:
        new = [{'vertex_index': e['vertex%d' % x]} for x in [1, 2]]
        out['lines'].append(new)
    return out


@pytest.fixture(scope="session")
def obj_test_value_simple(obj_test_value):
    r"""Simple example Obj dictionary."""
    out = {'vertices': copy.deepcopy(obj_test_value['vertices']),
           'normals': copy.deepcopy(obj_test_value['normals']),
           'texcoords': copy.deepcopy(obj_test_value['texcoords']),
           'faces': [[{'vertex_index': 0, 'normal_index': 0},
                      {'vertex_index': 1, 'normal_index': 0},
                      {'vertex_index': 2, 'normal_index': 0}],
                     [{'vertex_index': 0, 'normal_index': 1},
                      {'vertex_index': 2, 'normal_index': 1},
                      {'vertex_index': 3, 'normal_index': 1}]]}
    for f in out['faces']:
        for fv in f:
            fv['texcoord_index'] = 0
    for v in out['vertices']:
        v.pop('w', None)
    for t in out['texcoords']:
        t.pop('w', None)
        t.setdefault('v', 0.0)
    return out
