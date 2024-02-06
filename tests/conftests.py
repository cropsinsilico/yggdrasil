import os
pytest_plugins = 'pytest-yggdrasil'
_test_directory = os.path.abspath(os.path.dirname(__file__))


def pytest_addoption(parser):
    parser.addoption("--yggdrasil-tests-rootdir", type=str,
                     help="Directory containing the yggdrasil tests",
                     default=_test_directory)
