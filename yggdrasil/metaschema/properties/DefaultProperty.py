from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class DefaultMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'default' property."""

    name = 'default'
    _replaces_existing = True
    _validate = False
