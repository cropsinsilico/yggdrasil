from yggdrasil.drivers.ClientRequestDriver import ClientRequestDriver


class ClientDriver(ClientRequestDriver):
    r"""Alias for ClientRequestDriver."""

    _connection_type = 'client'
    _schema_subtype_description = ('Connection between a model acting as a '
                                   'client and a server request comm.')
