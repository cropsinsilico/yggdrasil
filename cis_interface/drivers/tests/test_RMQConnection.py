import test_IODriver as parent


class TestRMQConnection(parent.TestIODriver):
    r"""Test class for RMQConnection class."""

    def __init__(self):
        super(TestRMQConnection, self).__init__()
        self.driver = 'RMQConnection'
        self.args = '_TEST'
        self.attr_list += ['args', 'connection', 'user', 'server', 'passwd',
                           'queue', 'channel', '_closing']
        
