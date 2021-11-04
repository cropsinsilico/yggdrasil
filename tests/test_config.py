import pytest
import os
import shutil
from yggdrasil import config, tools, platform


def test_YggConfigParser():
    r"""Ensure that get returns proper defaults etc."""
    x = config.YggConfigParser()
    x.add_section('test_section')
    x.set('test_section', 'test_option', 'test_value')
    with pytest.raises(RuntimeError):
        x.update_file()
    assert(x.file_to_update is None)
    assert(x.get('test_section', 'test_option') == 'test_value')
    assert(x.get('test_section', 'fake_option') is None)
    assert(x.get('test_section', 'fake_option', 5) == 5)
    assert(x.get('fake_section', 'fake_option') is None)
    assert(x.get('fake_section', 'fake_option', 5) == 5)


def test_update_language_config():
    r"""Test updating configuration for installed languages."""
    languages = tools.get_supported_lang()
    cfg_orig = config.ygg_cfg_usr.file_to_update
    cfg_copy = '_copy'.join(os.path.splitext(cfg_orig))
    shutil.copy2(cfg_orig, cfg_copy)
    try:
        if config.ygg_cfg_usr.has_option('c', 'vcpkg_dir'):
            config.update_language_config(
                'c', lang_kwargs={'c': {
                    'vcpkg_dir': config.ygg_cfg_usr.get(
                        'c', 'vcpkg_dir')}})
        if platform._is_mac:
            config.update_language_config(
                'c', lang_kwargs={'c': {'compiler': shutil.which('clang')}})
        config.update_language_config(overwrite=True, verbose=True,
                                      allow_multiple_omp=True)
        if len(languages) > 0:
            config.ygg_cfg_usr.remove_section(languages[0])
            config.update_language_config(
                languages[0], disable_languages=[languages[0]])
            config.update_language_config(
                languages[0], disable_languages=[languages[0]],
                enable_languages=[languages[0]])
            config.update_language_config(
                languages[0], enable_languages=[languages[0]])
        if len(languages) > 1:
            config.ygg_cfg_usr.remove_section(languages[1])
            config.update_language_config(
                languages[1], enable_languages=[languages[1]])
    finally:
        shutil.move(cfg_copy, cfg_orig)
        config.ygg_cfg_usr.reload()
        config.ygg_cfg.reload()


def test_cfg_logging():
    r"""Test cfg_logging."""
    lvl = config.get_ygg_loglevel()
    config.set_ygg_loglevel(lvl)
    os.environ['YGG_SUBPROCESS'] = 'True'
    lvl = config.get_ygg_loglevel()
    config.set_ygg_loglevel(lvl)
    config.cfg_logging()
    del os.environ['YGG_SUBPROCESS']


def test_parser_config():
    r"""Test parser_config."""
    config.get_config_parser(description="test", skip_sections=['testing'])
    parser = config.get_config_parser(description="test")
    with pytest.raises(ValueError):
        config.resolve_config_parser(
            parser.parse_args(['--production-run', '--debug']))
    args1 = config.resolve_config_parser(
        parser.parse_args(['--production-run']))
    args2 = config.resolve_config_parser(
        parser.parse_args(['--debug']))
    args3 = config.resolve_config_parser(
        parser.parse_args(['--validate-messages=True']))
    assert(args3.validate_messages is True)
    old_var = {k: os.environ.get(k, None) for k in
               ['YGG_VALIDATE_COMPONENTS', 'YGG_VALIDATE_MESSAGES',
                'YGG_DEBUG', 'YGG_CLIENT_DEBUG']}
    args2.validate_messages = 'True'
    for k, v in old_var.items():
        assert(os.environ.get(k, None) == v)
    with config.parser_config(args1):
        assert(os.environ.get('YGG_VALIDATE_COMPONENTS', '') == 'false')
        assert(os.environ.get('YGG_VALIDATE_MESSAGES', '') == 'false')
    with config.parser_config(args2):
        assert(os.environ.get('YGG_DEBUG', '') == 'DEBUG')
        assert(os.environ.get('YGG_CLIENT_DEBUG', '') == 'DEBUG')
        assert(os.environ.get('YGG_VALIDATE_COMPONENTS', '') == 'true')
        assert(os.environ.get('YGG_VALIDATE_MESSAGES', '') == 'true')
    for k, v in old_var.items():
        assert(os.environ.get(k, None) == v)
    with pytest.raises(ValueError):
        config.acquire_env(dict(production_run=True, debug=True))
    with config.temp_config(production_run=True):
        assert(os.environ.get('YGG_VALIDATE_COMPONENTS', '') == 'false')
        assert(os.environ.get('YGG_VALIDATE_MESSAGES', '') == 'false')
    with config.temp_config(debug=True):
        assert(os.environ.get('YGG_DEBUG', '') == 'DEBUG')
        assert(os.environ.get('YGG_CLIENT_DEBUG', '') == 'DEBUG')
        assert(os.environ.get('YGG_VALIDATE_COMPONENTS', '') == 'true')
        assert(os.environ.get('YGG_VALIDATE_MESSAGES', '') == 'true')
    with config.temp_config(validate_messages='True'):
        assert(os.environ.get('YGG_VALIDATE_MESSAGES', '') == 'true')
