import test_Driver as parent


class TestModelDriver(parent.TestDriver):
    r"""Test runner for basic ModelDriver class."""
    
    def __init__(self):
        super(TestModelDriver, self).__init__()
        self.driver = 'ModelDriver'
        self.args = 'ls' # TODO: ['sleep', '1']
        self.attr_list += ['args', 'process', 'env']

    def run_before_stop(self):
        r"""Commands to run while the instance is running."""
        self.instance.wait()
