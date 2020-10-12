from yggdrasil.demos.tests import DemoTstBase
import unittest
try:
    import trimesh
except ImportError:  # pragma: debug
    trimesh = None


@unittest.skipIf(trimesh is None, "Trimesh is not installed")
class TestFSPM2020Demo(DemoTstBase):

    demo_name = 'fspm2020'
    runs = {'plant_v0': ('yamls/plant_v0.yml', ),
            'plant_v1': ('yamls/plant_v1.yml', 'yamls/light.yml'),
            'plant_v1_cpp': ('yamls/plant_v1.yml', 'yamls/light_cpp.yml'),
            'plant_v1_R': ('yamls/plant_v1.yml', 'yamls/light_R.yml'),
            'plant_v1_f90': ('yamls/plant_v1.yml',
                             'yamls/light_fortran.yml'),
            'plant_v2': ('yamls/plant_v2.yml', 'yamls/light.yml',
                         'yamls/roots.yml'),
            'call_split': ('yamls/plant_v2_split.yml', 'yamls/light.yml',
                           'yamls/roots.yml'),
            'simple_io': ('yamls/plant_output_mesh.yml',
                          'yamls/plant_io_mesh.yml')}
