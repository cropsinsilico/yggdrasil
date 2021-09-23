import pytest
from yggdrasil.metaschema.datatypes.ContainerMetaschemaType import (
    ContainerMetaschemaType)


def test_container_errors():
    r"""Test implementation errors on bare container class."""
    with pytest.raises(NotImplementedError):
        ContainerMetaschemaType._iterate(None)
    with pytest.raises(NotImplementedError):
        ContainerMetaschemaType._assign(None, None, None)
    with pytest.raises(NotImplementedError):
        ContainerMetaschemaType._has_element(None, None)
