from yggdrasil.tools import ProxyObject


class TestBase(object):

    @property
    def a(self):
        return 1


class TestProxy(ProxyObject):

    __slots__ = ['b']

    def __init__(self, *args, **kwargs):
        self.b = 3
        super(TestProxy, self).__init__(*args, **kwargs)

    @property
    def a(self):
        return 2


x = TestBase()
xp = TestProxy(x)

# Check properties & variables
assert(x.a == 1)
assert(xp.a == 2)
assert(xp._wrapped.a == 1)
assert(xp.b == 3)

# Check classes
assert(isinstance(xp, TestBase))
assert(isinstance(xp, TestProxy))
assert(isinstance(xp, ProxyObject))
