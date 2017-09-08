import nose.tools as nt
from cis_interface import config


def test_CisConfigParser():
    r"""Ensure that get returns proper defaults etc."""
    x = config.CisConfigParser()
    x.add_section('test_section')
    x.set('test_section', 'test_option', 'test_value')
    nt.assert_equal(x.get('test_section', 'test_option'), 'test_value')
    nt.assert_equal(x.get('test_section', 'fake_option'), None)
    nt.assert_equal(x.get('test_section', 'fake_option', 5), 5)
    nt.assert_equal(x.get('fake_section', 'fake_option'), None)
    nt.assert_equal(x.get('fake_section', 'fake_option', 5), 5)
