import pytest
import os
from yggdrasil import platform
from yggdrasil.drivers.CModelDriver import CModelDriver, LDLinker


def test_LDLinker_tool_version():
    r"""Test the tool_version method of the LDLinker class."""
    if LDLinker.is_installed():
        LDLinker.tool_version()
        LDLinker.get_search_path()
        LDLinker.get_env_flags()


@pytest.mark.skipif(not platform._is_linux, reason="OS is not Linux")
def test_update_ld_library_path():
    r"""Test update_ld_library_path method."""
    lang_dir = CModelDriver.get_language_dir()
    total = os.pathsep.join(['test', lang_dir])
    env = {'LD_LIBRARY_PATH': 'test'}
    env = CModelDriver.update_ld_library_path(env)
    assert(env['LD_LIBRARY_PATH'] == total)
    # Second time to ensure that path not added twice
    env = CModelDriver.update_ld_library_path(env)
    assert(env['LD_LIBRARY_PATH'] == total)
