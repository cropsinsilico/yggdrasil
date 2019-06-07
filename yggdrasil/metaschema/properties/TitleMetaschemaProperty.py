from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class TitleMetaschemaProperty(MetaschemaProperty):
    r"""Title property with validation of new properties."""

    name = 'title'
    _replaces_existing = True
    _validate = False
