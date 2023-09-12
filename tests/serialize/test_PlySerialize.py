import pytest
import numpy as np
from tests.serialize import TestSerializeBase as base_class


class TestPlyDict:
    r"""Test class for PlyDict class."""

    @pytest.fixture(scope="class")
    def geom_cls(self):
        from yggdrasil.serialize.PlySerialize import PlyDict
        return PlyDict


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
            for scalar_arr in [
                    10 * np.arange(x.count_elements('faces')),
                    np.zeros(x.count_elements('faces'))]:
                scalar_arr = scalar_arr.astype('float')
                odict = x.as_dict()
                for scale in ['linear', 'log']:
                    ox = type(x)(odict)
                    o2 = type(x)(odict)
                    o1 = ox.apply_scalar_map(scalar_arr, scaling=scale,
                                             scale_by_area=True)
                    o2.apply_scalar_map(scalar_arr, scaling=scale,
                                        scale_by_area=True, no_copy=True)
                    assert o1 == o2
                    assert o1 != ox
