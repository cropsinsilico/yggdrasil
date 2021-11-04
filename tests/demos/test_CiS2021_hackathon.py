import pytest
try:
    import trimesh
except ImportError:  # pragma: debug
    trimesh = None
from tests.demos import DemoTstBase as base_class


@pytest.mark.skipif(trimesh is None, reason="Trimesh is not installed")
class TestCiS2021HackathonDemo(base_class):

    @pytest.fixture(scope="class")
    def demo_name(self):
        r"""str: Name of demo being tested."""
        return 'CiS2021-hackathon'

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
