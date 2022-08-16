import copy
import warnings
import numpy as np
from yggdrasil.serialize.PlySerialize import PlySerialize, PlyDict, trimesh


class ObjDict(PlyDict):
    r"""Enhanced dictionary class for storing Obj information."""

    @classmethod
    def from_array_dict(cls, in_dict):
        r"""Get a version of the object from a dictionary of arrays."""
        kws = {}
        for k in ['material', 'vertices', 'params', 'normals', 'texcoords',
                  'lines', 'faces', 'points', 'curves', 'curve2Ds',
                  'surfaces']:
            if k in in_dict:
                kws[k] = copy.deepcopy(in_dict[k])
        if isinstance(kws.get('vertices', None), np.ndarray):
            old_vert = kws['vertices']
            nvert = old_vert.shape[1]
            assert(nvert in (3, 4))
            kws['vertices'] = [
                {k: old_vert[i, j] for j, k in enumerate('xyzw'[:nvert])
                 if ((j < 3) or (not np.isnan(old_vert[i, j])))}
                for i in range(old_vert.shape[0])]
        if isinstance(in_dict.get('vertex_colors', None), np.ndarray):
            old_colr = in_dict['vertex_colors']
            assert(old_colr.shape == (len(kws['vertices']), 3))
            for i in range(old_colr.shape[0]):
                for j, k in enumerate(['red', 'green', 'blue']):
                    kws['vertices'][i][k] = old_colr[i, j]
        if isinstance(kws.get('params', None), np.ndarray):
            old_parm = kws['params']
            nparm = old_parm.shape[1]
            assert(nparm in [2, 3])
            kws['params'] = [
                {k: old_parm[i, j] for j, k in enumerate('uvw'[:nparm])
                 if ((j < 2) or (not np.isnan(old_parm[i, j])))}
                for i in range(old_parm.shape[0])]
        if isinstance(kws.get('normals', None), np.ndarray):
            old_norm = kws['normals']
            assert(old_norm.shape[1] == 3)
            kws['normals'] = [
                {k: old_norm[i, j] for j, k in enumerate('ijk')}
                for i in range(old_norm.shape[0])]
        if isinstance(kws.get('texcoords', None), np.ndarray):
            old_texc = kws['texcoords']
            ntexc = old_texc.shape[1]
            assert(ntexc in [1, 2, 3])
            kws['texcoords'] = [
                {k: old_texc[i, j] for j, k in enumerate('uvw'[:ntexc])
                 if ((j < 1) or (not np.isnan(old_texc[i, j])))}
                for i in range(old_texc.shape[0])]
        # Composites of above
        if isinstance(kws.get('lines', None), np.ndarray):
            old_edge = kws['lines']
            assert(old_edge.shape[1] == 2)
            kws['lines'] = [
                [{'vertex_index': np.int32(old_edge[i, j])}
                 for j in range(old_edge.shape[1])
                 if (not np.isnan(old_edge[i, j]))]
                for i in range(old_edge.shape[0])]
        if isinstance(kws.get('faces', None), np.ndarray):
            old_face = kws['faces']
            assert(old_face.shape[1] >= 3)
            kws['faces'] = [
                [{'vertex_index': np.int32(old_face[i, j])}
                 for j in range(old_face.shape[1])
                 if (not np.isnan(old_face[i, j]))]
                for i in range(old_face.shape[0])]
        if isinstance(in_dict.get('face_texcoords', None), np.ndarray):
            old_texc = in_dict['face_texcoords']
            assert(old_texc.shape[0] == len(kws.get('faces', [])))
            for i in range(old_texc.shape[0]):
                for j in range(old_texc.shape[1]):
                    if not np.isnan(old_texc[i, j]):
                        kws['faces'][i][j]['texcoord_index'] = np.int32(
                            old_texc[i, j])
        if isinstance(in_dict.get('face_normals', None), np.ndarray):
            old_norm = in_dict['face_normals']
            assert(old_norm.shape[0] == len(kws.get('faces', [])))
            for i in range(old_norm.shape[0]):
                for j in range(old_norm.shape[1]):
                    if not np.isnan(old_norm[i, j]):
                        kws['faces'][i][j]['normal_index'] = np.int32(
                            old_norm[i, j])
        if isinstance(kws.get('points', None), np.ndarray):
            old_pnts = kws['points']
            kws['points'] = [
                [np.int32(old_pnts[i, j]) for j in range(old_pnts.shape[1])
                 if (not np.isnan(old_pnts[i, j]))]
                for i in range(old_pnts.shape[0])]
        if isinstance(kws.get('curves', None), np.ndarray):
            old_curv = kws['curves']
            kws['curves'] = [
                {'vertex_indices': [
                    np.int32(old_curv[i, j]) for j in range(old_curv.shape[1])
                    if (not np.isnan(old_curv[i, j]))]}
                for i in range(old_curv.shape[0])]
            assert('curve_params' in in_dict)
            if isinstance(in_dict['curve_params'], np.ndarray):
                old_parm = in_dict['curve_params']
                assert(old_parm.shape == (len(kws['curves']), 2))
                for i in range(old_parm.shape[0]):
                    kws['curves'][i]['starting_param'] = old_parm[i, 0]
                    kws['curves'][i]['ending_param'] = old_parm[i, 1]
        if isinstance(kws.get('curve2Ds', None), np.ndarray):
            old_curv = kws['curve2Ds']
            kws['curve2Ds'] = [
                [np.int32(old_curv[i, j]) for j in range(old_curv.shape[1])
                 if (not np.isnan(old_curv[i, j]))]
                for i in range(old_curv.shape[0])]
        if isinstance(kws.get('surfaces', None), np.ndarray):
            old_surf = kws['surfaces']
            kws['surfaces'] = [
                {'vertex_indices': [
                    {'vertex_index': np.int32(old_surf[i, j])}
                    for j in range(old_surf.shape[1])
                    if (not np.isnan(old_surf[i, j]))]}
                for i in range(old_surf.shape[0])]
            assert('surface_params' in in_dict)
            if isinstance(in_dict['surface_params'], np.ndarray):
                old_parm = in_dict['surface_params']
                assert(old_parm.shape == (len(kws['surfaces']), 4))
                for i in range(old_parm.shape[0]):
                    kws['surfaces'][i]['starting_param_u'] = old_parm[i, 0]
                    kws['surfaces'][i]['ending_param_u'] = old_parm[i, 1]
                    kws['surfaces'][i]['starting_param_v'] = old_parm[i, 2]
                    kws['surfaces'][i]['ending_param_v'] = old_parm[i, 3]
        if isinstance(in_dict.get('surface_texcoords', None), np.ndarray):
            old_texc = in_dict['surface_texcoords']
            assert(old_texc.shape[0] == len(kws['surfaces']))
            for i in range(old_texc.shape[0]):
                for j in range(old_texc.shape[1]):
                    if not np.isnan(old_texc[i, j]):
                        kws['surfaces'][i]['vertex_indices'][j][
                            'texcoord_index'] = np.int32(old_texc[i, j])
        if isinstance(in_dict.get('surface_normals', None), np.ndarray):
            old_norm = in_dict['surface_normals']
            assert(old_norm.shape[0] == len(kws['surfaces']))
            for i in range(old_norm.shape[0]):
                for j in range(old_norm.shape[1]):
                    if not np.isnan(old_norm[i, j]):
                        kws['surfaces'][i]['vertex_indices'][j][
                            'normal_index'] = np.int32(old_norm[i, j])
        return cls.from_dict(kws)
        
    def as_array_dict(self):
        r"""Get a version of the object as a dictionary of arrays."""
        out = {}
        if self.get('material', None):
            out['material'] = self['material']
        if self.get('vertices', None):
            out['vertices'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'xyzw']
                 for v in self['vertices']])
            out['vertex_colors'] = np.asarray(
                [[v.get(k, np.NaN) for k in ['red', 'green', 'blue']]
                 for v in self['vertices']])
            if np.all(np.isnan(out['vertices'][:, 3])):
                out['vertices'] = out['vertices'][:, :3]
            if np.all(np.isnan(out['vertex_colors'])):
                out.pop('vertex_colors')
        if self.get('params', None):
            out['params'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'uvw']
                 for v in self['params']])
            if np.all(np.isnan(out['params'][:, 2])):
                out['params'] = out['params'][:, :2]
        if self.get('normals', None):
            out['normals'] = np.asarray(
                [[v[k] for k in 'ijk'] for v in self['normals']])
        if self.get('texcoords', None):
            out['texcoords'] = np.asarray(
                [[v.get(k, np.NaN) for k in 'uvw']
                 for v in self['texcoords']])
            if np.all(np.isnan(out['texcoords'][:, 1:])):
                out['texcoords'] = out['texcoords'][:, :1]
            elif np.all(np.isnan(out['texcoords'][:, 2])):
                out['texcoords'] = out['texcoords'][:, :2]
        if self.get('lines', None):
            out['lines'] = np.NaN * np.ones(
                (len(self['lines']), len(max(self['lines'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['lines']):
                for j, v in enumerate(vlist):
                    out['lines'][i, j] = v['vertex_index']
        if self.get('faces', None):
            face_shp = (len(self['faces']), len(max(self['faces'], key=len)))
            out['faces'] = np.NaN * np.ones(face_shp, dtype='int32')
            out['face_texcoords'] = np.NaN * np.ones(face_shp, dtype='int32')
            out['face_normals'] = np.NaN * np.ones(face_shp, dtype='int32')
            for i, vlist in enumerate(self['faces']):
                for j, v in enumerate(vlist):
                    out['faces'][i, j] = v['vertex_index']
                    out['face_texcoords'][i, j] = v.get(
                        'texcoord_index', np.NaN)
                    out['face_normals'][i, j] = v.get('normal_index', np.NaN)
            if np.all(np.isnan(out['face_texcoords'])):
                out.pop('face_texcoords')
            if np.all(np.isnan(out['face_normals'])):
                out.pop('face_normals')
        if self.get('points', None):
            out['points'] = np.NaN * np.ones(
                (len(self['points']), len(max(self['points'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['points']):
                out['points'][i, :len(vlist)] = vlist
        if self.get('curves', None):
            def fkey(x):
                return len(x['vertex_indices'])
            out['curves'] = np.NaN * np.ones(
                (len(self['curves']), len(max(self['curves'], key=fkey))),
                dtype='int32')
            out['curve_params'] = np.zeros((out['curves'].shape[0], 2))
            for i, curv in enumerate(self['curves']):
                out['curve_params'][i, :] = [curv['starting_param'],
                                             curv['ending_param']]
                out['curves'][i, :fkey(curv)] = curv['vertex_indices']
        if self.get('curve2Ds', None):
            out['curve2Ds'] = np.NaN * np.ones(
                (len(self['curve2Ds']), len(max(self['curve2Ds'], key=len))),
                dtype='int32')
            for i, vlist in enumerate(self['curve2Ds']):
                out['curve2Ds'][i, :len(vlist)] = vlist
        if self.get('surfaces', None):
            def fkey(x):
                return len(x['vertex_indices'])
            surf_shp = (len(self['surfaces']), len(max(self['surfaces'], key=fkey)))
            out['surfaces'] = np.NaN * np.ones(surf_shp, dtype='int32')
            out['surface_params'] = np.zeros((surf_shp[0], 4))
            out['surface_texcoords'] = np.NaN * np.ones(surf_shp, dtype='int32')
            out['surface_normals'] = np.NaN * np.ones(surf_shp, dtype='int32')
            for i, surf in enumerate(self['surfaces']):
                out['surface_params'][i, :] = [surf['starting_param_u'],
                                               surf['ending_param_u'],
                                               surf['starting_param_v'],
                                               surf['ending_param_v']]
                for j, v in enumerate(surf['vertex_indices']):
                    out['surfaces'][i, j] = v['vertex_index']
                    out['surface_texcoords'][i, j] = v.get(
                        'texcoord_index', np.NaN)
                    out['surface_normals'][i, j] = v.get(
                        'normal_index', np.NaN)
            if np.all(np.isnan(out['surface_texcoords'])):
                out.pop('surface_texcoords')
            if np.all(np.isnan(out['surface_normals'])):
                out.pop('surface_normals')
        return out
    
    @classmethod
    def from_trimesh(cls, in_mesh):
        r"""Get a version of the object from a trimesh class."""
        kws = dict(vertices=in_mesh.vertices,
                   vertex_colors=in_mesh.visual.vertex_colors,
                   faces=in_mesh.faces.astype('int32'))
        weights = (kws['vertex_colors'][:, 3].astype('float32') + 1.0) / 256
        weights[weights == 1.0] = np.NaN
        kws['vertex_colors'] = kws['vertex_colors'][:, :3]
        kws['vertices'] = np.hstack([kws['vertices'], weights[..., None]])
        return cls.from_array_dict(kws)

    def as_trimesh(self, **kwargs):
        r"""Get a version of the object as a trimesh class."""
        kws0 = self.as_array_dict()
        kws = {'vertices': kws0.get('vertices', None),
               'vertex_colors': kws0.get('vertex_colors', None),
               'faces': kws0.get('faces', None)}
        if (kws['vertices'] is not None) and (kws['vertices'].shape[1] == 4):
            weights = kws['vertices'][:, 3] * 256 - 1.0
            weights[np.isnan(weights)] = 255
            kws['vertices'] = kws['vertices'][:, :3]
            if kws['vertex_colors'] is not None:
                kws['vertex_colors'] = np.hstack(
                    [kws['vertex_colors'], weights[..., None]])
        kws.update(kwargs, process=False)
        return trimesh.base.Trimesh(**kws)
    
    @property
    def mesh(self):
        r"""list: Vertices for each face in the structure."""
        mesh = []
        for f in self['faces']:
            imesh = []
            for v in f:
                imesh.append([self['vertices'][v['vertex_index']][k]
                              for k in ['x', 'y', 'z']])
            mesh.append(imesh)
        return mesh

    @property
    def vertex_normals(self):
        mesh = None
        if 'normals' in self:
            mesh = []
            for f in self['faces']:
                imesh = []
                for v in f:
                    imesh.append([self['normals'][v['normal_index']][k]
                                  for k in ['i', 'j', 'k']])
                mesh.append(imesh)
        return mesh

    @classmethod
    def from_shape(cls, shape, d, conversion=1.0):  # pragma: lpy
        r"""Create a ply dictionary from a PlantGL shape and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer): Descritizer.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        iobj = super(ObjDict, cls).from_shape(shape, d, conversion=conversion,
                                              _as_obj=True)
        if iobj is not None:
            # Texcoords
            if d.result.texCoordList:
                iobj.setdefault('texcoords', [])
                for t in d.result.texCoordList:
                    # TODO: Should the coords be scaled?
                    iobj['texcoords'].append({'u': t.x, 'v': t.y})
                if d.result.texCoordIndexList:
                    for i, t in enumerate(d.result.texCoordIndexList):
                        if t[0] < len(iobj['texcoords']):
                            for j in range(3):
                                iobj['faces'][i][j]['texcoord_index'] = t[j]
            # Normals
            if d.result.normalList:
                iobj.setdefault('normals', [])
                for n in d.result.normalList:
                    iobj['normals'].append({'i': n.x, 'j': n.y, 'k': n.z})
                if d.result.normalIndexList:
                    for i, n in enumerate(d.result.normalIndexList):
                        if n[0] < len(iobj['normals']):
                            for j in range(3):
                                iobj['faces'][i][j]['normal_index'] = n[j]
        return iobj

    def to_geom_args(self, conversion=1.0, name=None):  # pragma: lpy
        r"""Get arguments for creating a PlantGL geometry.

        Args:
            conversion (float, optional): Conversion factor that should be
                applied to the vertices. Defaults to 1.0.
            name (str, optional): Name that should be given to the created
                PlantGL symbol. Defaults to None and is ignored.

        Returns:
            tuple: Class, arguments and keyword arguments for PlantGL geometry.

        """
        import openalea.plantgl.all as pgl
        smb_class, args, kwargs = super(ObjDict, self).to_geom_args(
            conversion=conversion, name=name, _as_obj=True)
        index_class = pgl.Index
        array_class = pgl.IndexArray
        # Texture coords
        if self.get('texcoords', []):
            obj_texcoords = []
            for t in self['texcoords']:
                obj_texcoords.append(pgl.Vector2(np.float64(t['u']),
                                                 np.float64(t.get('v', 0.0))))
            kwargs['texCoordList'] = pgl.Point2Array(obj_texcoords)
            obj_ftexcoords = []
            for i, f in enumerate(self['faces']):
                entry = []
                for _f in f:
                    if 'texcoord_index' not in _f:
                        if i > 0:  # pragma: debug
                            warnings.warn(("'texcoord_index' missing from face"
                                           + "%d, texcoord indices will be "
                                           + "ignored.") % i)
                        obj_ftexcoords = []
                        entry = []
                        break
                    entry.append(int(_f['texcoord_index']))
                if not entry:
                    break
                obj_ftexcoords.append(index_class(*entry))
            if obj_ftexcoords:
                kwargs['texCoordIndexList'] = array_class(obj_ftexcoords)
        # Normals
        if self.get('normals', []):
            obj_normals = []
            for n in self['normals']:
                obj_normals.append(pgl.Vector3(np.float64(n['i']),
                                               np.float64(n['j']),
                                               np.float64(n['k'])))
            kwargs['normalList'] = pgl.Point3Array(obj_normals)
            obj_fnormals = []
            for i, f in enumerate(self['faces']):
                entry = []
                for _f in f:
                    if 'normal_index' not in _f:
                        if i > 0:  # pragma: debug
                            warnings.warn(("'normal_index' missing from face"
                                           + "%d, normal indices will be "
                                           + "ignored.") % i)
                        obj_fnormals = []
                        entry = []
                        break
                    entry.append(int(_f['normal_index']))
                if not entry:
                    break
                obj_fnormals.append(index_class(*entry))
            if obj_fnormals:
                kwargs['normalIndexList'] = array_class(obj_fnormals)
        return smb_class, args, kwargs

    def append(self, solf):
        r"""Append new ply information to this dictionary.

        Args:
            solf (ObjDict): Another ply to append to this one.

        """
        exist_map = {'vertex_index': len(self.get('vertices', [])),
                     'texcoord_index': len(self.get('texcoords', [])),
                     'normal_index': len(self.get('normals', [])),
                     'param_index': len(self.get('params', []))}
        exist_map.update(points=exist_map['vertex_index'],
                         curve2Ds=exist_map['param_index'])
        # Vertex fields
        for k in ['vertices', 'texcoords', 'normals', 'params']:
            if k in solf:
                if k not in self:
                    self[k] = []
                self[k] += solf[k]
        # Points/2D curves
        for k in ['points', 'curve2Ds']:
            if k in solf:
                if k not in self:
                    self[k] = []
                for x in solf[k]:
                    self[k].append([v + exist_map[k] for v in x])
        # Face/line fields
        for k in ['lines', 'faces']:
            if k in solf:
                if k not in self:
                    self[k] = []
                for x in solf[k]:
                    iele = [{ik: v[ik] + exist_map[ik] for ik in v.keys()} for v in x]
                    self[k].append(iele)
        # Curves
        k = 'curves'
        if k in solf:
            if k not in self:
                self[k] = []
            for x in solf[k]:
                iele = copy.deepcopy(x)
                iele['vertex_indices'] = [v + exist_map['vertex_index']
                                          for v in x['vertex_indices']]
        # Surfaces
        k = 'surfaces'
        if k in solf:
            if k not in self:
                self[k] = []
            for x in solf[k]:
                iele = copy.deepcopy(x)
                iele['vertex_indices'] = [{ik: v[ik] + exist_map[ik] for ik in v.keys()}
                                          for v in x['vertex_indices']]
        # Merge material using first in list
        material = None
        for x in [self, solf]:
            if x.get('material', None) is not None:
                material = x['material']
                break
        if material is not None:
            self['material'] = material
        return self

    def apply_scalar_map(self, *args, **kwargs):
        r"""Set the color of faces in a 3D object based on a scalar map.
        This creates a copy unless no_copy is True.

        Args:
            scalar_arr (arr): Scalar values that should be mapped to colors
                for each face.
            color_map (str, optional): The name of the color map that should
                be used. Defaults to 'plasma'.
            vmin (float, optional): Value that should map to the minimum of the
                colormap. Defaults to min(scalar_arr).
            vmax (float, optional): Value that should map to the maximum of the
                colormap. Defaults to max(scalar_arr).
            scaling (str, optional): Scaling that should be used to map the scalar
                array onto the colormap. Defaults to 'linear'.
            scale_by_area (bool, optional): If True, the elements of the scalar
                array will be multiplied by the area of the corresponding face.
                If True, vmin and vmax should be in terms of the scaled array.
                Defaults to False.
            no_copy (bool, optional): If True, the returned object will not be a
                copy. Defaults to False.

        Returns:
            dict: Obj with updated vertex colors.

        """
        kwargs['_as_obj'] = True
        return super(ObjDict, self).apply_scalar_map(*args, **kwargs)
    

class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    _seritype = 'obj'
    _schema_subtype_description = ('Serialize 3D structures using Obj format.')
    default_datatype = {'type': 'obj'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes: Serialized message.

        """
        return self.datatype.encode_data(args, self.typedef).encode("utf-8")

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return ObjDict(self.datatype.decode_data(msg, self.typedef))

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(ObjSerialize, cls).get_testing_options()
        obj = ObjDict({'vertices': [{'x': float(0), 'y': float(0), 'z': float(0)},
                                    {'x': float(0), 'y': float(0), 'z': float(1)},
                                    {'x': float(0), 'y': float(1), 'z': float(1)}],
                       'faces': [[{'vertex_index': int(0)},
                                  {'vertex_index': int(1)},
                                  {'vertex_index': int(2)}]]})
        out['objects'] = [obj, obj]
        out['contents'] = (b'# Author ygg_auto\n'
                           + b'# Generated by yggdrasil\n\n'
                           + b'v 0.0000 0.0000 0.0000\n'
                           + b'v 0.0000 0.0000 1.0000\n'
                           + b'v 0.0000 1.0000 1.0000\n'
                           + b'v 0.0000 0.0000 0.0000\n'
                           + b'v 0.0000 0.0000 1.0000\n'
                           + b'v 0.0000 1.0000 1.0000\n'
                           + b'f 1// 2// 3//\n'
                           + b'f 4// 5// 6//\n')
        return out
