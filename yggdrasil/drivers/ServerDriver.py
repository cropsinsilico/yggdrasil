from yggdrasil.drivers.ServerRequestDriver import ServerRequestDriver


class ServerDriver(ServerRequestDriver):
    r"""Alias for ServerRequestDriver."""

    _connection_type = 'server'
    _schema_subtype_description = ('Connection between a server request comm '
                                   'and a model acting as a server.')
