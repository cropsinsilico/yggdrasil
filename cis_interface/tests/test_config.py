import os
import tempfile
from cis_interface.tests import assert_equal, assert_warns
from cis_interface import config, backwards, tools


def make_temp(fname_base, count=1):
    r"""Create temporary copies of same file with different extensions."""
    fname_base = fname_base.lower()
    tempdir = os.path.normcase(os.path.normpath(tempfile.gettempdir()))
    if (tempdir + os.pathsep) not in os.environ['PATH']:
        os.environ['PATH'] = os.pathsep.join([tempdir, os.environ.get('PATH')])
    fname_pattern = fname_base + '.*'
    fname = os.path.join(tempdir, fname_base)
    out = []
    for i in range(count):
        fname_i = '%s.%d' % (fname, i)
        out.append(fname_i)
        if not os.path.isfile(fname_i):
            with open(fname_i, 'w') as fd:
                fd.write('Test file %d' % i)
    return tempdir, fname_pattern, out


def make_temp_single():
    r"""Create single temporary file."""
    return make_temp('single_test_file')


def make_temp_multiple():
    r"""Create multiple temporary files."""
    return make_temp('multiple_test_file', count=2)


def test_CisConfigParser():
    r"""Ensure that get returns proper defaults etc."""
    x = config.CisConfigParser()
    x.add_section('test_section')
    x.set('test_section', 'test_option', 'test_value')
    assert_equal(x.get('test_section', 'test_option'), 'test_value')
    assert_equal(x.get('test_section', 'fake_option'), None)
    assert_equal(x.get('test_section', 'fake_option', 5), 5)
    assert_equal(x.get('fake_section', 'fake_option'), None)
    assert_equal(x.get('fake_section', 'fake_option', 5), 5)


def test_locate_file():
    r"""Test file location method."""
    # Missing file
    assert(not config.locate_file('missing_file.fake'))
    # Single file
    sdir, spat, sans = make_temp_single()
    sout = config.locate_file(spat)
    assert(isinstance(sout, backwards.string_types))
    assert_equal(sout, sans[0])
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    with assert_warns(RuntimeWarning):
        mout = config.locate_file(mpat)
        assert(isinstance(mout, backwards.string_types))
        assert_equal(mout, mans[0])
    

def test_find_all():
    r"""Test find_all."""
    # Missing file
    assert(not config.find_all('missing_file.fake', 'invalid'))
    # Single file
    sdir, spat, sans = make_temp_single()
    sout = config.find_all(spat, sdir)
    assert(isinstance(sout, list))
    assert_equal(sout, sans)
    # Multiple files
    mdir, mpat, mans = make_temp_multiple()
    mout = config.find_all(mpat, mdir)
    assert(isinstance(mout, list))
    assert_equal(mout, mans)


def test_update_config():
    r"""Test update_config."""
    test_cfg = os.path.join(tempfile.gettempdir(), 'test.cfg')
    assert(not os.path.isfile(test_cfg))
    if not tools.is_lang_installed('matlab'):  # pragma: no matlab
        assert_warns(RuntimeWarning, config.update_config, test_cfg)
    config.update_config(test_cfg)
    assert(os.path.isfile(test_cfg))
    os.remove(test_cfg)


def test_cfg_logging():
    r"""Test cfg_logging."""
    os.environ['CIS_SUBPROCESS'] = 'True'
    config.cfg_logging()
    del os.environ['CIS_SUBPROCESS']
