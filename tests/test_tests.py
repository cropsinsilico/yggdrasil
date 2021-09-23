from yggdrasil.tests import YggTestClass, assert_raises


class TestYggTest(YggTestClass):
    r"""Test errors for uninitialized YggTestClass."""

    def create_instance(self):
        r"""Dummy overload to prevent initialization."""
        return None

    def test_description(self):
        r"""Get uninitialized description."""
        self.description_prefix
        self.shortDescription()

    def test_import_cls(self):
        r"""Test import class with mod/cls unset."""
        assert_raises(Exception, getattr, self, 'import_cls')
        self._mod = 'drivers'
        assert_raises(Exception, getattr, self, 'import_cls')

    def test_post_teardown_ref(self):
        r"""Test errors on instance ref post teardown."""
        self.teardown()
        assert_raises(RuntimeError, getattr, self, 'instance')
