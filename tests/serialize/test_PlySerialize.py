import pytest
import numpy as np
from tests.serialize import TestSerializeBase as base_class


class TestPlySerialize(base_class):
    r"""Test class for TestPlySerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "ply"

    def test_apply_scalar_map(self, class_name, testing_options):
        r"""Test applying a scalar colormap."""
        for x in testing_options['objects']:
            scalar_arr = np.arange(x.count_elements('faces')).astype(
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
