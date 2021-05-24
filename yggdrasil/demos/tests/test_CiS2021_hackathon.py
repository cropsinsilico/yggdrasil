import os
from yggdrasil.demos.tests import DemoTstBase, _demo_dir
import unittest
try:
    import trimesh
except ImportError:  # pragma: debug
    trimesh = None


@unittest.skipIf(trimesh is None, "Trimesh is not installed")
class TestCiS2021HackathonDemo(DemoTstBase):

    demo_name = 'CiS2021-hackathon'
    runs = {'light_v0': ('yamls/light_v0_python.yml', 'yamls/connections_v0.yml'),
            'shoot_v0': ('yamls/shoot_v0.yml', ),
            'shoot_v1': ('yamls/shoot_v1.yml', 'yamls/light_v0_python.yml',
                         'yamls/connections_v1.yml'),
            'shoot_v2': ('yamls/light_v1_python.yml', 'yamls/shoot_v2.yml'),
            'shoot_v2_split': ('yamls/light_v1_python.yml',
                               'yamls/shoot_v2_split.yml'),
            'shoot_v2_copies': ('yamls/light_v2_python.yml',
                                'yamls/shoot_v2_copies.yml'),
            'roots_v0': ('yamls/roots_v0.yml', ),
            'timesync': ('yamls/roots_v1.yml', 'yamls/shoot_v3.yml',
                         'yamls/timesync.yml', 'yamls/light_v1_python.yml')}

    def __init__(self, *args, **kwargs):
        super(TestCiS2021HackathonDemo, self).__init__(*args, **kwargs)
        out_dir = os.path.join(_demo_dir, self.demo_name, 'output')
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
