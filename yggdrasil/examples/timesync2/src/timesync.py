import sys
import numpy as np
from yggdrasil import units
from yggdrasil.interface.YggInterface import (
    YggTimesync, YggOutput)


def xvar2x(xvar):
    r"""Convert xvar to x."""
    x = 2 * xvar
    return x


def x2xvar(x):
    r"""Convert x to xvar."""
    xvar = x / 2
    return xvar


def xagg(series):
    r"""Aggregate x variables."""
    return max(series, key=abs)


def merge_z(z1, z2):
    r"""Merge the z1 and z2 variables."""
    return z1 + z2


def split_z(z):
    r"""Split z into z1 and z2 variables."""
    return (z / 2.0, z / 2.0)


def timestep_calc(t, model):
    r"""Updates the state based on the time where x is a sine wave
    with period of 10 days and y is a cosine wave with a period of 5 days.
    If model is 'A', the forth state variable will be 'a', a sine
    with a period of 2.5 days. If model is 'B', the forth state
    variable will be 'b', a cosine with a period of 2.5 days.

    Args:
        t (float): Current time.
        model (str): Identifier for the model (A or B).

    Returns:
        dict: Map of state parameters.

    """
    if model == 'A':
        state = {
            'x': np.sin(2.0 * np.pi * t / units.add_units(10, 'day')),
            'y': np.cos(2.0 * np.pi * t / units.add_units(5, 'day')),
            'z1': -np.cos(2.0 * np.pi * t / units.add_units(20, 'day')),
            'z2': -np.cos(2.0 * np.pi * t / units.add_units(20, 'day')),
            'a': np.sin(2.0 * np.pi * t / units.add_units(2.5, 'day'))}
    else:
        state = {
            'xvar': x2xvar(np.sin(2.0 * np.pi * t / units.add_units(10, 'day'))),
            'yvar': np.cos(2.0 * np.pi * t / units.add_units(5, 'day')),
            'z': -2.0 * np.cos(2.0 * np.pi * t / units.add_units(20, 'day')),
            'b': np.cos(2.0 * np.pi * t / units.add_units(2.5, 'day'))}
    return state


def main(t_step, t_units, model):
    r"""Function to execute integration.

    Args:
        t_step (float): The time step that should be used.
        t_units (str): Units of the time step.
        model (str): Identifier for the model (A or B).

    """
    print('Hello from Python timesync: timestep = %s %s' % (t_step, t_units))
    t_step = units.add_units(t_step, t_units)
    t_start = units.add_units(0.0, t_units)
    t_end = units.add_units(5.0, 'day')
    state = timestep_calc(t_start, model)

    # Set up connections matching yaml
    # Timestep synchronization connection will be 'statesync'
    timesync = YggTimesync("statesync")
    out = YggOutput('output')

    # Initialize state and synchronize with other models
    t = t_start
    ret, state = timesync.call(t, state)
    if not ret:
        raise RuntimeError("timesync(Python): Initial sync failed.")
    print('timesync(Python): t = % 8s' % t, end='')
    for k, v in state.items():
        print(', %s = %+ 5.2f' % (k, v), end='')
    print('')

    # Send initial state to output
    flag = out.send(dict(state, time=t))
    if not flag:
        raise RuntimeError("timesync(Python): Failed to send "
                           "initial output for t=%s." % t)
    
    # Iterate until end
    while t < t_end:

        # Perform calculations to update the state
        t = t + t_step
        state = timestep_calc(t, model)

        # Synchronize the state
        ret, state = timesync.call(t, state)
        if not ret:
            raise RuntimeError("timesync(Python): sync for t=%f failed." % t)
        print('timesync(Python): t = % 8s' % t, end='')
        for k, v in state.items():
            print(', %s = %+ 5.2f' % (k, v), end='')
        print('')

        # Send output
        flag = out.send(dict(state, time=t))
        if not flag:
            raise RuntimeError("timesync(Python): Failed to send output for t=%s." % t)

    print('Goodbye from Python timesync')


if __name__ == '__main__':
    # Take time step from the first argument
    main(float(sys.argv[1]), sys.argv[2], sys.argv[3])
