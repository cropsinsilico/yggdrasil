# Normalizer adapated from the jsonschema validator
import numbers
import contextlib
from jsonschema.compat import str_types, int_types, iteritems
from jsonschema import RefResolver


class UndefinedProperty(object):
    r"""Class to be used as a flag for undefined properties."""
    pass


def _normalize_ref(normalizer, ref, instance, schema):
    scope, resolved = normalizer.resolver.resolve(ref)
    normalizer.resolver.push_scope(scope)
    try:
        instance = normalizer.descend(instance, resolved)
    finally:
        normalizer.resolver.pop_scope()
    return instance


def _normalize_allOf(normalizer, allOf, instance, schema):
    for index, subschema in enumerate(allOf):
        instance = normalizer.descend(instance, subschema, schema_path=index)
    return instance


def _normalize_oneOf(normalizer, oneOf, instance, schema):
    subschemas = enumerate(oneOf)
    for index, subschema in subschemas:
        instance = normalizer.descend(instance, subschema, schema_path=index)
    return instance


def _normalize_anyOf(normalizer, anyOf, instance, schema):
    for index, subschema in enumerate(anyOf):
        instance = normalizer.descend(instance, subschema, schema_path=index)
    return instance


def create(meta_schema, normalizers=(), version=None, default_types=None,
           no_defaults=False):  # noqa: C901, E501
    if default_types is None:
        default_types = {
            u"array": list, u"boolean": bool, u"integer": int_types,
            u"null": type(None), u"number": numbers.Number, u"object": dict,
            u"string": str_types,
        }

    class Normalizer(object):
        NORMALIZERS = dict(normalizers)
        META_SCHEMA = dict(meta_schema)
        DEFAULT_TYPES = dict(default_types)
        NODEFAULTS = no_defaults

        def __init__(self, schema, types=(), resolver=None):

            self._path_stack = []
            self._schema_path_stack = []
            self._types = dict(self.DEFAULT_TYPES)
            self._types.update(types)

            if resolver is None:
                resolver = RefResolver.from_schema(schema)

            self.resolver = resolver
            self.schema = schema

        def iter_instance(self, instance, _schema=None):
            if _schema is None:
                _schema = self.schema

            ref = _schema.get(u"$ref")
            if ref is not None:
                normalizers = [(u"$ref", ref)]
            else:

                # print(self.current_schema_path, instance)
                if self.current_schema_path in self.NORMALIZERS:
                    normalizers = self.NORMALIZERS[self.current_schema_path]
                    for n in normalizers:
                        instance = n(self, None, instance, _schema)

                normalizers = iteritems(_schema)
                if isinstance(instance, UndefinedProperty):
                    if (not self.NODEFAULTS) and ('default' in _schema):
                        instance = _schema['default']
                    else:
                        return instance

            for k, v in normalizers:
                normalizer = self.NORMALIZERS.get(k, None)
                if normalizer is None:
                    continue

                instance = normalizer(self, v, instance, _schema)
            return instance

        @property
        def current_path(self):
            return tuple(self._path_stack)

        @property
        def current_schema_path(self):
            return tuple(self._schema_path_stack)

        @contextlib.contextmanager
        def append_path(self, path, schema_path):
            if path is not None:
                self._path_stack.append(path)
            if schema_path is not None:
                self._schema_path_stack.append(schema_path)
            try:
                yield
            finally:
                if path is not None:
                    self._path_stack.pop()
                if schema_path is not None:
                    self._schema_path_stack.pop()

        def descend(self, instance, schema, path=None, schema_path=None):
            with self.append_path(path, schema_path):
                out = self.iter_instance(instance, schema)
            return out

        def normalize(self, *args, **kwargs):
            return self.iter_instance(*args, **kwargs)

    return Normalizer
