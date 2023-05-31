import pytest
import tempfile
import os
import numpy as np
from tests.serialize import TestSerializeBase as base_class


class TestPlyDict:
    r"""Test class for PlyDict class."""

    @pytest.fixture(scope="class")
    def geom_cls(self):
        from yggdrasil.serialize.PlySerialize import PlyDict
        return PlyDict

    def test_mesh(self, geom_cls, geom_dict):
        r"""Test construction from a mesh."""
        x = geom_cls(geom_dict)
        mesh = x.mesh
        y = geom_cls.from_mesh(mesh)
        assert x.mesh == y.mesh
        assert x.nvert != y.nvert
        assert x.nface == y.nface
        z = geom_cls.from_mesh(mesh, prune_duplicates=True)
        assert x.mesh == z.mesh
        assert x.nvert == z.nvert
        assert x.nface == z.nface

    def test_mesh_structured(self, geom_cls, geom_dict):
        r"""Test construction from a numpy structured array."""
        from numpy.lib.recfunctions import unstructured_to_structured
        x = geom_cls(geom_dict)
        field_names = ['x1', 'y1', 'z1',
                       'x2', 'y2', 'z2',
                       'x3', 'y3', 'z3']
        formats = ['f8' for _ in field_names]
        dtype = np.dtype(dict(names=field_names, formats=formats))
        mesh = unstructured_to_structured(np.array(x.mesh), dtype=dtype)
        y = geom_cls.from_mesh(mesh)
        assert x.mesh == y.mesh
        assert x.nvert != y.nvert
        assert x.nface == y.nface
        z = geom_cls.from_mesh(mesh, prune_duplicates=True)
        assert x.mesh == z.mesh
        assert x.nvert == z.nvert
        assert x.nface == z.nface

    def test_mesh_file(self, geom_cls, geom_dict):
        r"""Test construciton from a mesh file."""
        x = geom_cls(geom_dict)
        mesh = np.asarray(x.mesh)
        ftemp = tempfile.NamedTemporaryFile(delete=False)
        np.savetxt(ftemp, mesh)
        fname = ftemp.name
        ftemp.close()
        try:
            y = geom_cls.from_mesh(fname)
            assert x.mesh == y.mesh
            assert x.nvert != y.nvert
            assert x.nface == y.nface
            z = geom_cls.from_mesh(fname, prune_duplicates=True)
            assert x.mesh == z.mesh
            assert x.nvert == z.nvert
            assert x.nface == z.nface
        finally:
            if os.path.isfile(fname):
                os.remove(fname)


class TestPlySerialize(base_class):
    r"""Test class for TestPlySerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "ply"

    def test_serialize_mesh(self, geom_dict, instance, testing_options):
        r"""Test serialize/deserialize of mesh."""
        iobj = type(testing_options['objects'][0])(geom_dict)
        mesh = np.asarray(iobj.mesh)
        msg = instance.serialize(mesh)
        iout, ihead = instance.deserialize(msg)
        assert iobj.mesh == iout.mesh
        assert iobj.nvert == iout.nvert
        assert iobj.nface == iout.nface

    def test_apply_scalar_map(self, class_name, testing_options):
        r"""Test applying a scalar colormap."""
        for x in testing_options['objects']:
            scalar_arr = 10 * np.arange(x.count_elements('faces')).astype(
                'float')
            with pytest.raises(NotImplementedError):
                x.apply_scalar_map(scalar_arr, scale_by_area=True)
            new_faces = []
            if 'Obj' in class_name:
                for f in x['faces']:
                    if len(f) == 3:
                        new_faces.append(f)
            else:
                for f in x['faces']:
                    if len(f['vertex_index']) == 3:
                        new_faces.append(f)
            odict = x.as_dict()
            odict['face'] = new_faces
            for scale in ['linear', 'log']:
                ox = type(x)(odict)
                o2 = type(x)(odict)
                o1 = ox.apply_scalar_map(scalar_arr, scaling=scale,
                                         scale_by_area=True)
                o2.apply_scalar_map(scalar_arr, scaling=scale,
                                    scale_by_area=True, no_copy=True)
                assert o1 == o2
                assert o1 != ox
