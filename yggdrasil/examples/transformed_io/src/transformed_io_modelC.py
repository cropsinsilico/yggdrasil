from yggdrasil import units


def modelC_function(in_val):
    out_val = 2 * in_val
    print("modelC_function(%s) = %s" % (in_val, out_val))
    return in_val, out_val


def transform_function(in_val):
    return (in_val / units.add_units(10, 'cm**2'))
