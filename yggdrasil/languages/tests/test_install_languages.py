import unittest
from yggdrasil.languages import install_languages


class TestInstallLanguages(unittest.TestCase):

    def test_update_argparser(self):
        r"""Test update_argparser."""
        install_languages.update_argparser(arglist=['all'])
        install_languages.update_argparser(arglist=['python'])
        install_languages.update_argparser(language='python',
                                           arglist=['python'])
        with self.assertRaises(SystemExit):
            install_languages.update_argparser(arglist=['-h'])
            unittest.main(exit=False)

    def test_install_language(self):
        r"""Test install_language."""
        install_languages.install_language('PYTHON', arglist=[])

    def test_install_all_languages(self):
        r"""Test install_all_languages."""
        install_languages.install_all_languages()
        install_languages.install_all_languages(from_setup=True)
