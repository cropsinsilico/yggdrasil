# import MPI test fixtures
from tests.communication.conftest import *  # noqa: F401, F403
from yggdrasil.examples import get_example_languages


def pytest_generate_tests(metafunc):
    if metafunc.cls is not None:
        pairs = []
        for example_name in metafunc.cls.examples:
            if getattr(metafunc.cls, 'languages', None):
                languages = metafunc.cls.languages
            else:
                languages = get_example_languages(example_name)
            for language in languages:
                pairs.append((example_name, language))
            
        metafunc.parametrize("example_name, language", pairs,
                             indirect=True, scope="class")
