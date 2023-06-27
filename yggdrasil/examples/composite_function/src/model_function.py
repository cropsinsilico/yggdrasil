import numpy as np


def model_function(a, b, c):
    out = np.zeros(3, 'float64')
    for i in range(3):
        if a:
            out[i] = b * (i ** c["c1"])
        else:
            out[i] = b * (i ** c["c2"])
    return out
