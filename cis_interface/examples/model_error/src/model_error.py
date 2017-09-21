import sys


def runerror():
    # Raise exception or return non-zero value to indicate an error
    raise Exception("Test error")
    sys.exit(-1)

    
if __name__ == '__main__':
    runerror()
