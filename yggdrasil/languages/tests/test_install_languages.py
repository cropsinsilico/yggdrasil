from yggdrasil.languages import install_languages


def test_install_all_languages():
    r"""Test install_all_languages."""
    install_languages.install_all_languages()
    install_languages.install_all_languages(from_setup=True)
