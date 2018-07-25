import os
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


def test_locate_file():
    r"""Test file location method."""
    # Normal search
    os.environ['PATH'] = os.pathsep.join([os.path.dirname(config.__file__),
                                          os.environ.get('PATH')])
    nt.assert_equal(config.locate_file(os.path.basename(__file__)), __file__)
    # Missing file
    assert(not config.locate_file('missing_file.fake'))
    # File that exists in multiple locations
    assert(len(config.locate_file('__init__.py')) > 1)
    

def test_find_all():
    r"""Test find_all."""
    test_fil = os.path.basename(__file__)
    test_dir = os.path.dirname(config.__file__)
    test_ans = __file__
    nt.assert_equal(config.find_all(test_fil, test_dir), [test_ans])
    assert(not config.find_all(test_fil, 'invalid'))
