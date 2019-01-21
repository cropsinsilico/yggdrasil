# Normalizer adapated from the jsonschema validator
import copy
import contextlib
import jsonschema
from yggdrasil.metaschema.datatypes import get_type_class


class UndefinedProperty(object):
    r"""Class to be used as a flag for undefined properties."""
    pass


class UninitializedNormalized(object):
    r"""Class to be used as a flag for uninitialized normalized value."""
    pass


def create(*args, **kwargs):
    normalizers = kwargs.pop('normalizers', ())
    no_defaults = kwargs.pop('no_defaults', ())
    validator_class = jsonschema.validators.create(*args, **kwargs)

    class Normalizer(validator_class):
        NORMALIZERS = dict(normalizers)
        NO_DEFAULTS = no_defaults

        def __init__(self, *args, **kwargs):
            super(Normalizer, self).__init__(*args, **kwargs)
            self._normalized = UninitializedNormalized()
            self._normalizing = False
            self._old_settings = {}
            self._path_stack = []
            self._schema_path_stack = []
            self._normalized_stack = []

        def iter_errors(self, instance, _schema=None):
            if _schema is None:
                _schema = self.schema

            if self._normalizing:

                if isinstance(self._normalized, UninitializedNormalized):
                    self._normalized = copy.deepcopy(instance)
                instance = self._normalized

            if self._normalizing and (u"$ref" not in _schema):

                # Path based normalization
                try:
                    # print(self.current_schema_path, instance, type(instance), _schema)
                    if self.current_schema_path in self.NORMALIZERS:
                        normalizers = self.NORMALIZERS[self.current_schema_path]
                        for n in normalizers:
                            instance = n(self, None, instance, _schema)
                except BaseException as e:
                    error = jsonschema.ValidationError(str(e))
                    # set details if not already set by the called fn
                    error._set(
                        validator=n,
                        validator_value=None,
                        instance=instance,
                        schema=_schema)
                    yield error
                self._normalized = instance

                # Do defaults for required fields
                if (((isinstance(_schema.get('required', None), list)
                      and isinstance(_schema.get('properties', None), dict)
                      and self.is_type(self._normalized, "object")))):
                    for k in _schema['required']:
                        if (((k not in _schema['properties'])
                             or (k in self._normalized))):
                            continue
                        default = _schema['properties'][k].get('default', None)
                        self._normalized[k] = default
                    instance = self._normalized

                # Do default and type first so normalization can be validated
                for k in ['default', 'type']:
                    if (((k != 'default')
                         and isinstance(instance, UndefinedProperty))):
                        return
                    if k not in _schema:
                        continue
                    v = _schema[k]
                    validator = self.VALIDATORS.get(k)
                    if validator is None:
                        continue
                    errors = validator(self, v, instance, _schema) or ()
                    for error in errors:
                        # set details if not already set by the called fn
                        error._set(
                            validator=k,
                            validator_value=v,
                            instance=instance,
                            schema=_schema,
                        )
                        if k != u"$ref":
                            error.schema_path.appendleft(k)
                        yield error

                    instance = self._normalized

                self._normalized = instance

            for e in super(Normalizer, self).iter_errors(instance, _schema=_schema):
                yield e

        @property
        def current_path(self):
            return tuple(self._path_stack)

        @property
        def current_schema_path(self):
            return tuple(self._schema_path_stack)

        @contextlib.contextmanager
        def normalizing(self, **kwargs):
            for k, v in kwargs.items():
                if k == 'normalizers':
                    for ik, iv in self.NORMALIZERS.items():
                        if ik not in v:
                            v[ik] = iv
                elif k == 'validators':
                    for ik, iv in self.VALIDATORS.items():
                        if ik not in v:
                            v[ik] = iv
                if hasattr(self, k.upper()):
                    ksub = k.upper()
                else:
                    ksub = k
                self._old_settings[ksub] = getattr(self, ksub, None)
                setattr(self, ksub, v)
            self._normalizing = True
            try:
                yield
            finally:
                for k, v in self._old_settings.items():
                    if v is None:
                        delattr(self, k)
                    else:
                        setattr(self, k, v)
                self._old_settings = {}
                self._normalizing = False

        def descend(self, instance, schema, path=None, schema_path=None):
            if self._normalizing:
                if path is not None:
                    self._normalized_stack.append(self._normalized)
                    self._normalized = UninitializedNormalized()
                else:
                    self._normalized_stack.append(self._normalized)
                    self._normalized = copy.deepcopy(self._normalized)
            if path is not None:
                self._path_stack.append(path)
            if schema_path is not None:
                self._schema_path_stack.append(schema_path)
            failed = False
            try:
                for error in super(Normalizer, self).descend(instance, schema,
                                                             path=path,
                                                             schema_path=schema_path):
                    failed = True
                    yield error
            finally:
                if self._normalizing:
                    old_normalized = self._normalized_stack.pop()
                    if not (failed or isinstance(self._normalized, UndefinedProperty)):
                        if path is not None:
                            old_normalized[path] = self._normalized
                        else:
                            old_normalized = self._normalized
                    self._normalized = old_normalized
                if path is not None:
                    self._path_stack.pop()
                if schema_path is not None:
                    self._schema_path_stack.pop()

        def validate(self, instance, _schema=None, normalize=False, **kwargs):
            if normalize:
                with self.normalizing(**kwargs):
                    super(Normalizer, self).validate(instance, _schema=_schema)
                out = self._normalized
                return out
            else:
                super(Normalizer, self).validate(instance, _schema=_schema)

        def normalize(self, instance, _schema=None, **kwargs):
            with self.normalizing(**kwargs):
                errors = list(self.iter_errors(instance, _schema=_schema))
                # for e in errors[::-1]:
                #     print(80 * '-')
                #     print(e)
                # print(80 * '-')
            if errors:
                # raise jsonschema.ValidationError('error')
                return instance
            else:
                return self._normalized

        def is_type(self, instance, type):
            out = super(Normalizer, self).is_type(instance, type)
            if out:
                out = get_type_class(type).validate(instance)
            return out

    return Normalizer
