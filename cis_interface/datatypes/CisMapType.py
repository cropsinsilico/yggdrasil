from cis_interface.datatypes import register_type
from cis_interface.datatypes.CisContainerBase import CisContainerBase


@register_type
class CisMapType(CisContainerBase):
    r"""Type associated with a map."""

    name = 'map'
    description = 'A container mapping between keys and values.'
    properties = {'contents': {
                  'description': 'Map between keys and type of each value.',
                  'type': 'object',  # TODO: expansion 'cistype' type
                  'minProperties': 1}
                  }
    _python_types = (dict, )
    _container_type = dict

    @classmethod
    def _iterate(cls, container):
        r"""Iterate over the contents of the container. Each element returned
        should be a tuple including an index and a value.

        Args:
            container (obj): Object to be iterated over.

        Returns:
            iterator: Iterator over elements in the container.

        """
        for k, v in container.items():
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
        container[index] = value

    @classmethod
    def _has_element(cls, container, index):
        r"""Check to see if an index is in the container.

        Args:
            container (obj): Object that should be checked for index.
            index (obj): Index that should be checked for.

        Returns:
            bool: True if the index is in the container.

        """
        return (index in container)
