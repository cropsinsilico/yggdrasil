import subprocess


def test_update_config():
    r"""Test the yggconfig entry point."""
    subprocess.check_call(['yggconfig', '-h'])
