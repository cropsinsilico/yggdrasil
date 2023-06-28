import numpy as np


def model_function(a, b, c):
    d = (not a)
    e = c["c1"]
    f = np.zeros(3, 'float64')
    for i in range(3):
        if a:
            f[i] = b * (i ** c["c1"])
        else:
            f[i] = b * (i ** c["c2"])
    return d, e, f
