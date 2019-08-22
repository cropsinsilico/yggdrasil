r"""IO and Model drivers."""
from yggdrasil.components import import_component


_non_component_modules = ['lpy_model.py']


def create_driver(driver=None, name=None, args=None, **kwargs):
    r"""Dynamically create a driver based on a string and other driver
    properties.

    Args:
        driver (str): Name of the driver that should be created.
        name (str): Name to give the driver.
        args (object, optional): Second argument for drivers which take a
            minimum of two arguments. If None, the driver is assumed to take a
            minimum of one argument. Defaults to None.
        **kwargs: Additional keyword arguments are passed to the driver
            class.

    Returns:
        object: Instance of the requested driver.

    """
    class_ = import_component('model', driver, without_schema=True)
    if args is None:
        instance = class_(name, **kwargs)
    else:
        instance = class_(name, args, **kwargs)
    return instance


__all__ = ['create_driver', 'Driver',
           'ModelDriver', 'PythonModelDriver', 'RModelDriver',
           'CModelDriver', 'CPPModelDriver',
           'MakeModelDriver', 'MatlabModelDriver', 'LPyModelDriver',
           'ConnectionDriver', 'InputDriver', 'OutputDriver',
           'FileInputDriver', 'FileOutputDriver',
           'ClientDriver', 'ServerDriver',
           'RMQInputDriver', 'RMQOutputDriver',
           'RMQClientDriver', 'RMQServerDriver']
