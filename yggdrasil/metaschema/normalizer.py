# Normalizer adapated from the jsonschema validator
import pprint
import copy
import contextlib
import jsonschema
import logging
from collections import OrderedDict


logger = logging.getLogger(__name__)


class UndefinedProperty(object):
    r"""Class to be used as a flag for undefined properties."""
    pass


class UninitializedNormalized(object):
    r"""Class to be used as a flag for uninitialized normalized value."""
    pass


def create(*args, **kwargs):
    r"""Dynamically create a validation/normalization class that subclasses
    the jsonschema validation class.

    Args:
        normalizers (dict, optional): Keys are tuples representing paths that
            exist within the schema at which the normalization functions stored
            in lists as their value counterparts should be executed. Defaults to
            empty dictionary.
        no_defaults (bool, optional): If True, defaults will not be set during
            normalization. Defaults to False.
        required_defaults (bool, optional): If True, defaults will be set for
            required properties, even if no_defaults is True. Defaults to False.
        *args: Additional arguments are passed to jsonschema.validators.create.
        **kwargs: Additional keyword arguments are passed to
            jsonschema.validators.create.
        
    """
    normalizers = kwargs.pop('normalizers', ())
    no_defaults = kwargs.pop('no_defaults', ())
    required_defaults = kwargs.pop('required_defaults', ())
    validator_class = jsonschema.validators.create(*args, **kwargs)

    class Normalizer(validator_class):
        r"""Class that can be used to normalize (or validate) objects against
        JSON schemas.

        Args:
            *args: Additional arguments are passed to the base validator class.
            **kwargs: Additional keyword arguments are passed to the base
                validator class.

        Attributes:
            NORMALIZERS (dict): Keys are tuples representing paths that exist
                within the schema at which the normalization functions stored in
                lists as their value counterparts should be executed.
            NO_DEFAULTS (bool): If True, defaults will not be set during
                normalization.
            REQUIRED_DEFAULTS (bool): If True, defaults will be set for required
                properties, even if NO_DEFAULTS is True.

        """
        NORMALIZER_VALIDATORS = OrderedDict([('default', None),
                                             ('type', None)])
        NORMALIZERS = dict(normalizers)
        NO_DEFAULTS = no_defaults
        REQUIRED_DEFAULTS = required_defaults
        VERBOSE = False

        def __init__(self, *args, **kwargs):
            super(Normalizer, self).__init__(*args, **kwargs)
            self._normalized = UninitializedNormalized()
            self._normalizing = False
            self._old_settings = {}
            self._path_stack = []
            self._schema_path_stack = []
            self._normalized_stack = []

        @classmethod
        def normalize_schema(cls, schema, **kwargs):
            r"""Normalize a schema against the metaschema.

            Args:
                schema (dict): Schema that should be normalized.
                **kwargs: Additional keyword arguments are passed to the
                    normalize method.

            Returns:
                dict: Normalized schema.

            """
            return cls(cls.META_SCHEMA).normalize(schema, **kwargs)

        @property
        def current_path(self):
            r"""tuple: Current path from the top of the instance to the current
            instance being validated/normalized."""
            return tuple(self._path_stack)

        @property
        def current_schema_path(self):
            r"""tuple: Current path from the top of the schema to the current
            schema being used for validation/normalization."""
            return tuple(self._schema_path_stack)

        @contextlib.contextmanager
        def normalizing(self, **kwargs):
            r"""Context for normalization that records normalizers before
            context is initialized so that they can be restored once the context
            exist.

            Args:
                **kwargs: Keyword arguments are treated as attributes that
                    should be added to the class in the context. If the class
                    already has an attribute of the same name, it is stored
                    for restoration after the context exits.

            Yields:
                ValidationError: Errors encountered during validation.

            """
            kwargs.update(iter_errors=self.iter_errors_normalize,
                          descend=self.descend_normalize,
                          _normalizing=True)
            for k, v in kwargs.items():
                if k == 'normalizers':
                    if self.NORMALIZERS:  # pragma: debug
                        raise Exception("Uncomment lines below to allow "
                                        + "addition of default normalizers.")
                    # for ik, iv in self.NORMALIZERS.items():
                    #     v.setdefault(ik, iv)
                elif k == 'validators':
                    for ik, iv in self.VALIDATORS.items():
                        v.setdefault(ik, iv)
                elif k == 'normalizer_validators':
                    for ik, iv in self.NORMALIZER_VALIDATORS.items():
                        v.setdefault(ik, iv)
                if hasattr(self, k.upper()):
                    ksub = k.upper()
                else:
                    ksub = k
                self._old_settings[ksub] = getattr(self, ksub, None)
                setattr(self, ksub, v)
            # Separate out validators that need to be run in a specific order
            # during normalization
            _migrated_validators = []
            for k in self.NORMALIZER_VALIDATORS.keys():
                if self.NORMALIZER_VALIDATORS[k] is None:
                    _migrated_validators.append(k)
                    self.NORMALIZER_VALIDATORS[k] = self.VALIDATORS.get(k, None)
                    self.VALIDATORS[k] = None
            # Perform context and then cleanup
            try:
                yield
            finally:
                # Restore validators with special order
                for k in _migrated_validators:
                    self.VALIDATORS[k] = self.NORMALIZER_VALIDATORS[k]
                    self.NORMALIZER_VALIDATORS[k] = None
                # Restore old attributes
                for k, v in self._old_settings.items():
                    if v is None:
                        delattr(self, k)
                    else:
                        setattr(self, k, v)
                self._old_settings = {}

        def iter_errors_normalize(self, instance, _schema=None):
            r"""Iterate through all of the errors encountered during validation
            of an instance at the current level or lower against properties in a
            schema.

            Args:
                instance (object): Instance that will be validated.
                _schema (dict, optional): Schema that the instance will be
                    validated against. Defaults to the schema used to initialize
                    the class.

            Yields:
                ValidationError: Errors encountered during validation of the
                    instance.

            """
            if _schema is None:
                _schema = self.schema

            if isinstance(self._normalized, UninitializedNormalized):
                self._normalized = copy.deepcopy(instance)

            if isinstance(_schema, dict) and (u"$ref" not in _schema):
                # Path based normalization
                try:
                    # logger.info("schema_path=%s, type=%s, instance=%s, schema=%s"
                    #             % (self.current_schema_path,
                    #                type(self._normalized), self._normalized,
                    #                _schema))
                    if self.current_schema_path in self.NORMALIZERS:
                        normalizers = self.NORMALIZERS[self.current_schema_path]
                        for n in normalizers:
                            self._normalized = n(self, None, self._normalized, _schema)
                except BaseException as e:
                    error = jsonschema.ValidationError(str(e))
                    # set details if not already set by the called fn
                    error._set(
                        validator=n,
                        validator_value=None,
                        instance=self._normalized,
                        schema=_schema)
                    # if self.VERBOSE:  # pragma: debug
                    #     logger.info('Error in normalization: %s' % e)
                    yield error

                # Do defaults for required fields
                if (((((not self.NO_DEFAULTS) or self.REQUIRED_DEFAULTS)
                      and isinstance(_schema.get('required', None), list)
                      and isinstance(_schema.get('properties', None), dict)
                      and self.is_type(self._normalized, "object")))):
                    for k in _schema['required']:
                        if (((k not in _schema['properties'])
                             or (k in self._normalized))):
                            continue
                        default = _schema['properties'][k].get('default', None)
                        self._normalized[k] = copy.deepcopy(default)

                # Perform normalization for properties that will change the
                # outcome of validation
                for k, validator in self.NORMALIZER_VALIDATORS.items():
                    if (((k != 'default')
                         and isinstance(self._normalized, UndefinedProperty))):
                        return
                    if (validator is None) or (k not in _schema):
                        continue
                    v = _schema[k]
                    errors = validator(self, v, self._normalized, _schema) or ()
                    for error in errors:
                        # set details if not already set by the called fn
                        error._set(
                            validator=k,
                            validator_value=v,
                            instance=self._normalized,
                            schema=_schema,
                        )
                        if k != u"$ref":
                            error.schema_path.appendleft(k)
                        # if self.VERBOSE:  # pragma: debug
                        #     logger.info('Error in early %s validation: %s'
                        #                 % (k, error))
                        yield error

            for e in self._old_settings['iter_errors'](self._normalized,
                                                       _schema=_schema):
                # if self.VERBOSE:  # pragma: debug
                #     logger.info('Error in base iter_errors: %s' % e)
                yield e

        def descend_normalize(self, instance, schema, path=None, schema_path=None):
            r"""Descend along a path in the schema/instance, recording
            information about the normalization state so that it can be replaced
            with the original value if there is a validation error along the
            descent path.

            Args:
                instance (object): Current instance being validated against the
                    schema.
                schema (dict): Current schema that the instance is being
                    validated against.
                path (str, int, optional): Path that resulted in the current
                    instance. Defaults to None.
                schema_path (str, int, optional): Path that resulted in the
                    current schema. Defaults to None.

            Yields:
                ValidationError: Errors raised during validation of the instance.

            """
            old_normalized = self._normalized
            if path is not None:
                # self._normalized_stack.append(self._normalized)
                self._normalized = UninitializedNormalized()
            else:
                # self._normalized_stack.append(self._normalized)
                self._normalized = copy.deepcopy(self._normalized)
            if path is not None:
                self._path_stack.append(path)
            if schema_path is not None:
                self._schema_path_stack.append(schema_path)
            failed = False
            try:
                for error in self._old_settings['descend'](instance, schema,
                                                           path=path,
                                                           schema_path=schema_path):
                    failed = True
                    # if self.VERBOSE:
                    #     logger.info("Error in descent (path=%s, schema_path=%s): %s"
                    #                 % (path, schema_path, error))
                    yield error
            finally:
                # old_normalized = self._normalized_stack.pop()
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
            r"""Validate an instance against a schema.

            Args:
                instance (object): Object to be validated.
                _schema (dict, optional): Schema by which the instance should be
                    validated. Defaults to None and will be set to the schema
                    used to create the class.
                normalize (bool, optional): If True, the instance will also be
                    normalized as it is validated. Defaults to False.
                **kwargs: Additional keyword arguments are passed to the
                    'normalizing' context if normalize is True, otherwise they
                    are ignored.

            Returns:
                object: Normalized instance if normalize == True.

            """
            if normalize:
                with self.normalizing(**kwargs):
                    super(Normalizer, self).validate(instance, _schema=_schema)
                out = self._normalized
                return out
            else:
                super(Normalizer, self).validate(instance, _schema=_schema)

        def normalize(self, instance, _schema=None, show_errors=False, **kwargs):
            r"""Normalize an instance during validation, allowing for aliases,
            defaults, or simple type conversions.

            Args:
                instance (object): Object to be normalized and validated.
                _schema (dict, optional): Schema by which the instance should be
                    normalized and validated. Defaults to None and will be set
                    to the schema used to create the class.
                show_errors (bool, optional): If True, any errors during the
                    normalization are displayed. Defaults to False.
                **kwargs: Additional keyword arguments are passed to the
                    'normalizing' context.

            Returns:
                object: Normalized instance.

            """
            if show_errors:
                self.VERBOSE = True
            with self.normalizing(**kwargs):
                errors = list(self.iter_errors(instance, _schema=_schema))
                if show_errors:  # pragma: debug
                    for e in errors[::-1]:
                        if e:
                            logger.info(80 * '-')
                            logger.info(e)
                    if errors:
                        logger.info(80 * '-')
                        logger.info('Normalized:\n'
                                    + pprint.pformat(self._normalized))
            if errors:
                return instance
            else:
                return self._normalized

    return Normalizer
