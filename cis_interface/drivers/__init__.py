r"""IO and Model drivers."""
import importlib


def import_driver(driver=None):
    r"""Dynamically import a driver based on a string.

    Args:
        driver (str): Name of the driver that should be imported.

    """
    if driver is None:
        driver = 'Driver'
    drv = importlib.import_module('cis_interface.drivers.%s' % driver)
    class_ = getattr(drv, driver)
    return class_
                    

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


def get_model_driver(lang=None):
    r"""Get the name of the model driver that should be used for a model
    written in the specified programming language. If there is not a
    corresponding driver, 'ModelDriver' will be returned.

    Args:
        lang (str, optional): Language that the model is written in. Defaults
            to None.

    Returns:
        str: The name of the model driver that should be used to run a model
            in the specified language.

    """
    if isinstance(lang, str):
        lang = lang.lower()
    if lang == 'python':
        out = 'PythonModelDriver'
    elif lang == 'matlab':
        out = 'MatlabModelDriver'
    elif lang in ['c', 'c++', 'cpp']:
        out = 'GCCModelDriver'
    elif lang == 'make':
        out = 'MakeModelDriver'
    else:
        out = 'ModelDriver'
    return out


__all__ = ['import_driver', 'create_driver', 'get_model_driver', 'Driver',
           'ModelDriver', 'PythonModelDriver', 'GCCModelDriver',
           'MakeModelDriver', 'MatlabModelDriver',
           'InputDriver', 'OutputDriver',
           'IODriver', 'FileInputDriver', 'FileOutputDriver',
           'AsciiFileInputDriver', 'AsciiFileOutputDriver',
           'AsciiTableInputDriver', 'AsciiTableOutputDriver',
           'RPCDriver', 'RMQDriver', 'RMQInputDriver', 'RMQOutputDriver',
           'RMQClientDriver', 'RMQServerDriver']
