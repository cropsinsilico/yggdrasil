from yggdrasil.examples import yamls
from yggdrasil.examples.tests import _test_registry


# Test discovery
for k in yamls.keys():
    if k not in _test_registry:
        print('no test for example', k)
