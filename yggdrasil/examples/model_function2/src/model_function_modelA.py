from yggdrasil import units


def model_function(x):
    y = x + units.add_units(1.0, 'g')
    print("Model A: %s -> %s" % (x, y))
    return y
