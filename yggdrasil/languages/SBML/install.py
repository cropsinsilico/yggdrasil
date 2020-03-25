

def install(args=None):
    r"""Check if SBML language will be supported based on if the roadrunner package
    can be imported from openalea.

    Args:
        args (argparse.Namespace, optional): Arguments parsed from the
            command line. Default to None and is created from sys.argv.

    Returns:
        bool: True if install succeded, False otherwise.

    """
    try:
        import roadrunner
        del roadrunner
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    out = install()
    if out:
        print("SBML interface installed.")
    else:
        raise Exception("Failed to install SBML interface.")
