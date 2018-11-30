from cis_interface.metaschema.datatypes import register_type, get_type_class
from cis_interface.metaschema.datatypes.MetaschemaType import MetaschemaType
from cis_interface.metaschema.datatypes.ContainerMetaschemaType import (
    ContainerMetaschemaType)


@register_type
class JSONArrayMetaschemaType(ContainerMetaschemaType):
    r"""Type associated with a set of subtypes."""

    name = 'array'
    description = 'A container of ordered values.'
    properties = ContainerMetaschemaType.properties + ['items']
    definition_properties = ContainerMetaschemaType.definition_properties
    metadata_properties = ContainerMetaschemaType.metadata_properties + ['items']
    python_types = (list, tuple)
    _replaces_existing = True

    _container_type = list
    _json_type = 'array'
    _json_property = 'items'

    @classmethod
    def _iterate(cls, container):
        r"""Iterate over the contents of the container. Each element returned
        should be a tuple including an index and a value.

        Args:
            container (obj): Object to be iterated over.

        Returns:
            iterator: Iterator over elements in the container.

        """
        for k, v in enumerate(container):
            yield (k, v)

    @classmethod
    def _assign(cls, container, index, value):
        r"""Assign an element in the container to the specified value.

        Args:
            container (obj): Object that element will be assigned to.
            index (obj): Index in the container object where element will be
                assigned.
            value (obj): Value that will be assigned to the element in the
                container object.

        """
        if len(container) > index:
            container[index] = value
        elif len(container) == index:
            container.append(value)
        else:
            raise RuntimeError("The container has %s elements and the index is %s"
                               % (len(container), index))

    @classmethod
    def _has_element(cls, container, index):
        r"""Check to see if an index is in the container.

        Args:
            container (obj): Object that should be checked for index.
            index (obj): Index that should be checked for.

        Returns:
            bool: True if the index is in the container.

        """
        return (len(container) > index)

    @classmethod
    def _get_element(cls, container, index, default):
        r"""Get an element from the container if it exists, otherwise return
        the default.

        Args:
            container (obj): Object that should be returned from.
            index (obj): Index of element that should be returned.
            default (obj): Default that should be returned if the index is not
                in the container.

        Returns:
            object: Container contents at specified element.

        """
        if isinstance(container, dict):
            assert('type' in container)
            return container
        return super(JSONArrayMetaschemaType, cls)._get_element(
            container, index, default)
        
    @classmethod
    def extract_typedef(cls, metadata):
        r"""Extract the minimum typedef required for this type from the provided
        metadata.

        Args:
            metadata (dict): Message metadata.

        Returns:
            dict: Encoded type definition with unncessary properties removed.

        """
        out = super(JSONArrayMetaschemaType, cls).extract_typedef(metadata)
        if (cls._json_property in out) and isinstance(out[cls._json_property], dict):
            if 'type' in out[cls._json_property]:
                vcls = get_type_class(out[cls._json_property]['type'])
                out[cls._json_property] = vcls.extract_typedef(out[cls._json_property])
        return out

    def update_typedef(self, **kwargs):
        r"""Update the current typedef with new values.

        Args:
            **kwargs: All keyword arguments are considered to be new type
                definitions. If they are a valid definition property, they
                will be copied to the typedef associated with the instance.

        Returns:
            dict: A dictionary of keyword arguments that were not added to the
                type definition.

        """
        map = kwargs.get(self._json_property, None)
        map_out = None
        if isinstance(map, dict) and ('type' in map):
            if isinstance(self._typecls, MetaschemaType):
                map_out = self._typecls.update_typedef(**map)
            elif len(self._typecls) == 0:
                self._typecls = get_type_class(map['type'])(**map)
            else:
                raise Exception("Cannot change from an array of types "
                                + "to a single type.")
        elif isinstance(self._typecls, MetaschemaType):
            raise Exception("Cannot change from a single type to an array.")
        out = super(JSONArrayMetaschemaType, self).update_typedef(**kwargs)
        if map_out:
            out[self._json_property] = map_out
        return out
