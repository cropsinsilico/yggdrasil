import test_Driver as parent


class TestModelParam(parent.TestParam):
    r"""Test parameters for basic ModelDriver class.

    Attributes (in addition to parent class's):
        -

    """
    
    def __init__(self):
        super(TestModelParam, self).__init__()
        self.driver = 'ModelDriver'
        self.args = ['sleep', '0.1']
        self.attr_list += ['args', 'process', 'env']
        

class TestModelDriverNoStart(TestModelParam, parent.TestDriverNoStart):
    r"""Test runner for basic ModelDriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestModelDriver(TestModelParam, parent.TestDriver):
    r"""Test runner for basic ModelDriver class.

    Attributes (in addition to parent class's):
        -

    """
    
    def run_before_stop(self):
        r"""Commands to run while the instance is running."""
        self.instance.wait()
