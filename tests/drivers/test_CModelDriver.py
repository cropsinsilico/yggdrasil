from yggdrasil.drivers.CModelDriver import LDLinker


def test_LDLinker_tool_version():
    r"""Test the tool_version method of the LDLinker class."""
    if LDLinker.is_installed():
        LDLinker.tool_version()
        LDLinker.get_search_path()
        LDLinker.get_env_flags()
