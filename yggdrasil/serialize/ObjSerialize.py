import warnings
import numpy as np
from yggdrasil import rapidjson
from yggdrasil.serialize.PlySerialize import PlySerialize, GeometryBase


class ObjDict(GeometryBase, rapidjson.geometry.ObjWavefront):
    r"""Enhanced dictionary class for storing Obj information."""

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
    file_extensions = ['.obj']

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes: Serialized message.

        """
        assert isinstance(args, ObjDict)
        return str(args).strip().encode("utf-8")

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return ObjDict(msg.strip())

    def normalize(self, args):
        r"""Normalize a message to conform to the expected datatype.

        Args:
            args (object): Message arguments.

        Returns:
            object: Normalized message.

        """
        if isinstance(args, ObjDict):
            return args
        elif self.is_mesh(args):
            return ObjDict.from_mesh(
                args, prune_duplicates=self.prune_duplicates)
        return ObjDict(super(PlySerialize, self).normalize(args))
        
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(ObjSerialize, cls).get_testing_options()
        obj = ObjDict(
            {'vertices': [{'x': float(0), 'y': float(0), 'z': float(0)},
                          {'x': float(0), 'y': float(0), 'z': float(1)},
                          {'x': float(0), 'y': float(1), 'z': float(1)},
                          {'x': float(1), 'y': float(1), 'z': float(1)}],
             'faces': [
                 [{'vertex_index': int(0)},
                  {'vertex_index': int(1)},
                  {'vertex_index': int(2)}],
                 [{'vertex_index': int(1)},
                  {'vertex_index': int(2)},
                  {'vertex_index': int(3)}],
                 [{'vertex_index': int(0)},
                  {'vertex_index': int(1)},
                  {'vertex_index': int(2)},
                  {'vertex_index': int(3)}]],
             'comments': ["Author ygg_auto", "Generated by yggdrasil"]})
        out['objects'] = [obj, obj]
        out['contents'] = (b'# Author ygg_auto\n'
                           + b'# Generated by yggdrasil\n'
                           + b'v 0.0 0.0 0.0\n'
                           + b'v 0.0 0.0 1.0\n'
                           + b'v 0.0 1.0 1.0\n'
                           + b'v 1.0 1.0 1.0\n'
                           + b'f 1 2 3\n'
                           + b'f 2 3 4\n'
                           + b'f 1 2 3 4\n'
                           + b'# Author ygg_auto\n'
                           + b'# Generated by yggdrasil\n'
                           + b'v 0.0 0.0 0.0\n'
                           + b'v 0.0 0.0 1.0\n'
                           + b'v 0.0 1.0 1.0\n'
                           + b'v 1.0 1.0 1.0\n'
                           + b'f 5 6 7\n'
                           + b'f 6 7 8\n'
                           + b'f 5 6 7 8')
        return out
