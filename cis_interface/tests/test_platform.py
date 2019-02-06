r"""Tests for platform compatiblity."""
from cis_interface.tests import assert_equal
from cis_interface import platform


def test_os():
    r"""Test that only one OS selected."""
    res = platform._is_mac + platform._is_linux + platform._is_win
    assert_equal(res, 1)
