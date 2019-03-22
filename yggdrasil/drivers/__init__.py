r"""IO and Model drivers."""
import os
import glob
import importlib


def import_driver(driver=None):
    r"""Dynamically import a driver based on a string.

    Args:
        driver (str): Name of the driver that should be imported.

    Returns:
        class: Driver class for the specified language.

    """
    if driver is None:
        driver = 'Driver'
    drv = importlib.import_module('yggdrasil.drivers.%s' % driver)
    class_ = getattr(drv, driver)
    return class_


def import_language_driver(language):
    r"""Dynamically import a model driver based on the specified language.

    Args:
        language (str): Language of driver that should be imported.

    Returns:
        class: Model driver class for the specified language.

    """
    from yggdrasil import schema
    s = schema.get_schema()
    drv_name = s['model'].subtype2class.get(language, None)
    if drv_name is None:
        raise ValueError("No driver registered for language '%s'" % language)
    return import_driver(drv_name)
                    

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
    class_ = import_driver(driver)
    if args is None:
        instance = class_(name, **kwargs)
    else:
        instance = class_(name, args, **kwargs)
    return instance


def import_all_drivers():
    r"""Import all drivers to ensure they are registered."""
    for x in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
        xbase = os.path.basename(x)
        if (not xbase.startswith('__')) and (xbase != 'lpy_model.py'):
            import_driver(xbase[:-3])


__all__ = ['import_driver', 'create_driver', 'Driver',
           'ModelDriver', 'PythonModelDriver',
           'CModelDriver', 'CPPModelDriver',
           'MakeModelDriver', 'MatlabModelDriver', 'LPyModelDriver',
           'ConnectionDriver', 'InputDriver', 'OutputDriver',
           'FileInputDriver', 'FileOutputDriver',
           'ClientDriver', 'ServerDriver',
           'RMQInputDriver', 'RMQOutputDriver',
           'RMQClientDriver', 'RMQServerDriver']
