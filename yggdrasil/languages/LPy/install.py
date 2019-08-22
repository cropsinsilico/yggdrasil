

def install(args=None):
    r"""Check if LPy language will be supported based on if the lpy package
    can be imported from openalea.

    Args:
        args (argparse.Namespace, optional): Arguments parsed from the
            command line. Default to None and is created from sys.argv.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    try:
        from openalea import lpy
        del lpy
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    out = install()
    if out:
        print("LPy interface installed.")
    else:
        raise Exception("Failed to install LPy interface.")
