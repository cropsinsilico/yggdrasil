import copy
import numpy as np
import matplotlib as mpl
import matplotlib.cm as cm
from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PlyDict(dict):
    r"""Class for storing ply information.

    Args:
        vertices (list, optional): 3D positions of vertices comprising the
            3D object. Defaults to [].
        faces (list, optional): Indices of 3 or more vertices making up faces.
            Defaults to [].
        vertex_colors (list, optional): RGB values for each of the vertices.
            If not provided, all vertices will be black. Defaults to [].

    """
    def __init__(self, **kwargs):
        list_keys = ['vertices', 'faces', 'vertex_colors']
        for k in list_keys:
            if kwargs.get(k, None) is None:
                kwargs.setdefault(k, [])
        super(PlyDict, self).__init__(**kwargs)

    @property
    def nvert(self):
        r"""int: Number of vertices."""
        return len(self['vertices'])

    @property
    def nface(self):
        r"""int: Number of faces."""
        return len(self['faces'])

    @property
    def bounds(self):
        r"""tuple: Minimums and maximums of vertices."""
        mins = 1e6 * np.ones(3, 'float')
        maxs = -1e6 * np.ones(3, 'float')
        for v in self['vertices']:
            mins = np.minimum(mins, np.array(v))
            maxs = np.maximum(maxs, np.array(v))
        return mins, maxs

    @property
    def mesh(self):
        r"""list: Vertices for each face in the structure."""
        mesh = []
        for f in self['faces']:
            imesh = []
            for i in range(3):
                imesh += self['vertices'][f[i]]
            mesh.append(imesh)
        return mesh

    @classmethod
    def from_shape(cls, shape, d, conversion=1.0):
        r"""Create a ply dictionary from a PlantGL shape and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer): Descritizer.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.

        """
        iply = None
        d.process(shape)
        if d.result is not None:
            iply = cls()
            # Vertices
            for p in d.result.pointList:
                iply['vertices'].append([conversion * p.x,
                                         conversion * p.y,
                                         conversion * p.z])
            # Colors
            if d.result.colorPerVertex and d.result.colorList:
                if d.result.isColorIndexListToDefault():
                    for c in d.result.colorList:
                        iply['vertex_colors'].append([c.red,
                                                      c.green,
                                                      c.blue])
                else:  # pragma: debug
                    raise Exception("Indexed vertex colors not supported.")
            # elif not shape.appearance.isAmbientToDefault():
            #     c = shape.appearance.ambient
            #     icolor = [c.red, c.green, c.blue]
            #     iply['vertex_colors'] += [icolor for p in d.result.pointList]
            # Material
            if (shape.appearance.name != shape.appearance.DEFAULT_MATERIAL.name):
                iply['material'] = shape.appearance.name
            # Faces
            for i3 in d.result.indexList:
                iply['faces'].append([i3[0], i3[1], i3[2]])
        return iply

    @classmethod
    def from_scene(cls, scene, d=None, conversion=1.0, default_rgb=None):
        r"""Create a ply dictionary from a PlantGL scene and descritizer.

        Args:
            scene (openalea.plantgl.scene): Scene that should be descritized.
            d (openalea.plantgl.descritizer, optional): Descritizer. Defaults
                to openalea.plantgl.all.Tesselator.
            conversion (float, optional): Conversion factor that should be
                applied to the vertex positions. Defaults to 1.0.
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].

        """
        if d is None:
            from openalea.plantgl.all import Tesselator
            d = Tesselator()
        out = cls()
        for k, shapes in scene.todict().items():
            for shape in shapes:
                d.clear()
                iply = cls.from_shape(shape, d, conversion=conversion)
                if iply is not None:
                    out.append(iply, default_rgb=default_rgb)
                d.clear()
        return out

    def to_scene(self, conversion=1.0, name=None):
        r"""Create a PlantGL scene from a Ply dictionary.

        Args:
            conversion (float, optional): Conversion factor that should be
                applied to the vertices. Defaults to 1.0.
            name (str, optional): Name that should be given to the created
                PlantGL symbol. Defaults to None and is ignored.

        Returns:
        

        """
        import openalea.plantgl.all as pgl
        smb_class, args, kwargs = self.to_geom_args(conversion=conversion,
                                                    name=name)
        smb = smb_class(*args, **kwargs)
        if name is not None:
            smb.setName(name)
        if self.get('material', None) is not None:
            mat = pgl.Material(self['material'])
            shp = pgl.Shape(smb, mat)
        else:
            shp = pgl.Shape(smb)
        if name is not None:
            shp.setName(name)
        scn = pgl.Scene([shp])
        return scn

    def to_geom_args(self, conversion=1.0, name=None):
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
        kwargs = dict()
        # Add vertices
        obj_points = []
        for v in self['vertices']:
            xarr = conversion * np.array(v)
            obj_points.append(pgl.Vector3(xarr[0], xarr[1], xarr[2]))
        points = pgl.Point3Array(obj_points)
        # Add indices
        obj_indices = []
        nind = None
        index_class = pgl.Index3
        array_class = pgl.Index3Array
        smb_class = pgl.TriangleSet
        for f in self['faces']:
            if nind is None:
                nind = len(f)
                if nind == 3:
                    pass
                else:
                    raise ValueError("No PlantGL class for faces with %d vertices."
                                     % nind)
            else:
                if len(f) != nind:
                    raise ValueError("Faces do not all contain %d vertices." % nind)
            f_int = [int(_f) for _f in f]
            obj_indices.append(index_class(*f_int))
        indices = array_class(obj_indices)
        # Add colors
        if self['vertex_colors']:
            obj_colors = []
            for c in self['vertex_colors']:
                assert(len(c) == 3)
                obj_colors.append(pgl.Color4(c[0], c[1], c[2], 1))
            colors = pgl.Color4Array(obj_colors)
            kwargs['colorList'] = colors
            kwargs['colorPerVertex'] = True
        args = (points, indices)
        return smb_class, args, kwargs

    def set_vertex_colors(self, default_rgb=None):
        r"""Set the vertex colors to a default if they are not yet set.

        Args:
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].

        """
        if len(self['vertex_colors']) == self.nvert:
            return
        if default_rgb is None:
            default_rgb = [0, 0, 0]
        self['vertex_colors'] = [default_rgb for _ in range(self.nvert)]

    def append(self, solf, default_rgb=None):
        r"""Append new ply information to this dictionary.

        Args:
            solf (PlyDict): Another ply to append to this one.
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].

        """
        do_colors = False
        if self['vertex_colors'] or solf['vertex_colors']:
            self.set_vertex_colors(default_rgb=default_rgb)
            solf.set_vertex_colors(default_rgb=default_rgb)
            do_colors = True
        # Vertex fields
        nvert = self.nvert
        self['vertices'] += solf['vertices']
        if do_colors:
            self['vertex_colors'] += solf['vertex_colors']
        # Face fields
        for f in solf['faces']:
            self['faces'].append([v + nvert for v in f])

    def merge(self, ply_list, no_copy=False, default_rgb=None):
        r"""Merge a list of ply dictionaries.

        Args:
            ply_list (list): Ply dictionaries.
            no_copy (bool, optional): If True, the current dictionary will be
                updated, otherwise a copy will be returned with the update.
                Defaults to False.
            default_rgb (list, optional): Default color in RGB that should be
                used for missing colors. Defaults to [0, 0, 0].

        Returns:
            dict: Merged ply dictionary.

        """
        if not isinstance(ply_list, list):
            ply_list = [ply_list]
        # Merge fields
        if no_copy:
            out = self
        else:
            out = copy.deepcopy(self)
        for x in ply_list:
            out.append(x, default_rgb=default_rgb)
        return out

    def apply_scalar_map(self, scalar_arr, color_map=None,
                         vmin=None, vmax=None, scaling='linear',
                         scale_by_area=False, no_copy=False):
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
            dict: Ply with updated vertex colors.

        """
        # Scale by area
        if scale_by_area:
            scalar_arr = copy.deepcopy(scalar_arr)
            for i in range(len(self['faces'])):
                f = self['faces'][i]
                v0 = np.array(self['vertices'][f[0]])
                v1 = np.array(self['vertices'][f[1]])
                v2 = np.array(self['vertices'][f[2]])
                a = np.sqrt(np.sum((v0 - v1)**2))
                b = np.sqrt(np.sum((v1 - v2)**2))
                c = np.sqrt(np.sum((v2 - v0)**2))
                s = (a + b + c) / 2.0
                area = np.sqrt(s * (s - a) * (s - b) * (s - c))
                scalar_arr[i] = area * scalar_arr[i]
        # Map vertices onto faces
        vertex_scalar = [[] for x in self['vertices']]
        for i in range(len(self['faces'])):
            for v in self['faces'][i]:
                vertex_scalar[v].append(scalar_arr[i])
        for i in range(len(vertex_scalar)):
            vertex_scalar[i] = np.mean(vertex_scalar[i])
        vertex_scalar = np.array(vertex_scalar)
        if scaling == 'log':
            vertex_scalar = np.ma.MaskedArray(vertex_scalar, vertex_scalar <= 0)
        # Get color scaling
        if color_map is None:
            # color_map = 'summer'
            color_map = 'plasma'
        if vmin is None:
            vmin = vertex_scalar.min()
        if vmax is None:
            vmax = vertex_scalar.max()
        # print(vmin, vmax)
        cmap = cm.get_cmap(color_map)
        if scaling == 'log':
            norm = mpl.colors.LogNorm(vmin=vmin, vmax=vmax)
        elif scaling == 'linear':
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        else:  # pragma: debug
            raise Exception("Scaling must be 'linear' or 'log'.")
        m = cm.ScalarMappable(norm=norm, cmap=cmap)
        # Scale colors
        vertex_colors = (255 * m.to_rgba(vertex_scalar)).astype('int')[:, :3].tolist()
        if no_copy:
            out = self
        else:
            out = copy.deepcopy(self)
        out['vertex_colors'] = vertex_colors
        return out


class PlySerialize(DefaultSerialize):
    r"""Class for serializing/deserializing .ply file formats.

    Args:
        write_header (bool, optional): If True, headers will be added to
            serialized output. Defaults to True.
        newline (str, optional): String that should be used for new lines.
            Defaults to '\n'.

    Attributes:
        write_header (bool): If True, headers will be added to serialized
            output.
        newline (str): String that should be used for new lines.
        default_rgb (list): Default color in RGB that should be used for
            missing colors.

    """
    
    def __init__(self, *args, **kwargs):
        self.write_header = kwargs.pop('write_header', True)
        self.newline = backwards.bytes2unicode(kwargs.pop('newline', '\n'))
        self.default_rgb = [0, 0, 0]
        super(PlySerialize, self).__init__(*args, **kwargs)

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 8
        
    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return backwards.unicode2bytes('')
            
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (PlyDict): Dictionary of ply information.

        Returns:
            bytes, str: Serialized message.

        """
        lines = []
        if isinstance(args, dict):
            args = PlyDict(**args)
        nvert = args.nvert
        nface = args.nface
        # Header
        if self.write_header:
            lines += ['ply',
                      'format ascii 1.0',
                      'comment author cis_auto',
                      'comment File generated by cis_interface',
                      'element vertex %d' % nvert,
                      'property float x',
                      'property float y',
                      'property float z']
            if args.get('vertex_colors', []):
                lines += ['property uchar diffuse_red',
                          'property uchar diffuse_green',
                          'property uchar diffuse_blue']
            lines += ['element face %d' % nface,
                      'property list uchar int vertex_indices',
                      'end_header']
        # 3D objects
        if args.get('vertex_colors', []):
            for i in range(args.nvert):
                v = args['vertices'][i]
                c = args['vertex_colors'][i]
                entry = tuple(list(v) + list(c))
                lines.append('%6.4f %6.4f %6.4f %d %d %d' % entry)
        else:
            for i in range(args.nvert):
                v = args['vertices'][i]
                entry = tuple(list(v))
                lines.append('%6.4f %6.4f %6.4f' % entry)
        for f in args.get('faces', []):
            nv = len(f)
            iline = '%d' % nv
            for v in f:
                iline += ' %d' % v
            lines.append(iline)
        out = self.newline.join(lines) + self.newline
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg, nvert=None, nface=None,
                         do_vertex_colors=False):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.
            nvert (int, optional): Number of vertices expected if the ply
                header is not in the message. Defaults to None.
            nface (int, optional): Number of faces expected if the ply
                header is not in the message. Defaults to None.
            do_vertex_colors (bool, optional): If True the vertex color
                will be contained in the vertex information if the ply
                header is not in the message. Defaults to False.

        Returns:
            dict: Deserialized .ply information.

        """
        if len(msg) == 0:
            out = self.empty_msg
        else:
            lines = backwards.bytes2unicode(msg).split(self.newline)
            # Split header and body
            headline = 0
            for i in range(len(lines)):
                if 'end_header' in lines[i]:
                    headline = i + 1
                    break
            if headline > 0:
                element = None
                for i in range(headline):
                    if lines[i].startswith('element'):
                        parts = lines[i].split()
                        element = parts[1]
                        if element == 'vertex':
                            nvert = int(parts[2])
                        elif element == 'face':
                            nface = int(parts[2])
                    elif element == 'vertex':
                        if 'green' in lines[i]:
                            do_vertex_colors = True
            if (nvert is None) or (nface is None):  # pragma: debug
                raise RuntimeError("Could not locate element definitions.")
            # Get 3D info
            out = PlyDict()
            i = headline
            while out.nvert < nvert:
                values = lines[i].split()
                if len(values) > 0:
                    out['vertices'].append([x for x in map(float, values[:3])])
                    if do_vertex_colors:
                        iclr = self.default_rgb
                        if len(values) >= 6:
                            iclr = [x for x in map(int, values[3:])]
                        out['vertex_colors'].append(iclr)
                i += 1
            while out.nface < nface:
                values = lines[i].split()
                if len(values) > 0:
                    nv = int(values[0])
                    out['faces'].append([x for x in map(int, values[1:(nv + 1)])])
                    for x in out['faces'][-1]:
                        assert(x < out.nvert)
                i += 1
        return out
