import os
from yggdrasil.tests import assert_equal, assert_raises
from yggdrasil import config, tools


def test_YggConfigParser():
    r"""Ensure that get returns proper defaults etc."""
    x = config.YggConfigParser()
    x.add_section('test_section')
    x.set('test_section', 'test_option', 'test_value')
    assert_raises(RuntimeError, x.update_file)
    assert_equal(x.file_to_update, None)
    assert_equal(x.get('test_section', 'test_option'), 'test_value')
    assert_equal(x.get('test_section', 'fake_option'), None)
    assert_equal(x.get('test_section', 'fake_option', 5), 5)
    assert_equal(x.get('fake_section', 'fake_option'), None)
    assert_equal(x.get('fake_section', 'fake_option', 5), 5)


def test_update_language_config():
    r"""Test updating configuration for installed languages."""
    languages = tools.get_supported_lang()
    config.update_language_config(overwrite=True, verbose=True)
    try:
        config.update_language_config(
            languages[0], disable_languages=[languages[0]])
        config.update_language_config(
            languages[0], disable_languages=[languages[0]],
            enable_languages=[languages[0]])
    finally:
        config.update_language_config(
            languages[0], enable_languages=[languages[0]])


def test_cfg_logging():
    r"""Test cfg_logging."""
    lvl = config.get_ygg_loglevel()
    config.set_ygg_loglevel(lvl)
    os.environ['YGG_SUBPROCESS'] = 'True'
    lvl = config.get_ygg_loglevel()
    config.set_ygg_loglevel(lvl)
    config.cfg_logging()
    del os.environ['YGG_SUBPROCESS']
