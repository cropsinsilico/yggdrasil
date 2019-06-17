

def install():
    r"""Check if LPy language will be supported based on if the lpy package
    can be imported from openalea."""
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
