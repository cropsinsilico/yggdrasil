from yggdrasil import units


def model_function(x):
    y = x + units.add_units(2.0, 'g')
    print("Model B: %s -> %s" % (x, y))
    return y
