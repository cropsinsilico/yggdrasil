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


def timestep_calc(t, xname, yname):
    r"""Updates the state based on the time where x is a sine wave
    with period of 10 days and y is a cosine wave with a period of 5 days.

    Args:
        t (float): Current time.
        xname (str): Name of x state variable.
        yname (str): Name of y state variable.

    Returns:
        dict: Map of state parameters.

    """
    state = {
        xname: np.sin(2.0 * np.pi * t / units.add_units(10, 'day')),
        yname: np.cos(2.0 * np.pi * t / units.add_units(5, 'day'))}
    if xname == 'xvar':
        state[xname] = x2xvar(state[xname])
    return state


def main(t_step, t_units, xname, yname):
    r"""Function to execute integration.

    Args:
        t_step (float): The time step that should be used.
        t_units (str): Units of the time step.
        xname (str): Name of x state variable.
        yname (str): Name of y state variable.

    """
    print('Hello from Python timesync: timestep = %s %s' % (t_step, t_units))
    t_step = units.add_units(t_step, t_units)
    t_start = units.add_units(0.0, t_units)
    t_end = units.add_units(5.0, 'day')
    state = timestep_calc(t_start, xname, yname)

    # Set up connections matching yaml
    # Timestep synchronization connection will be 'statesync'
    timesync = YggTimesync("statesync")
    out = YggOutput('output')

    # Initialize state and synchronize with other models
    t = t_start
    ret, result = timesync.call(t, state)
    if not ret:
        raise RuntimeError("timesync(Python): Initial sync failed.")
    state = result[0]
    print('timesync(Python): t = % 8s, %s = %+ 5.2f, %s = %+ 5.2f' % (
        t, xname, state[xname], yname, state[yname]))

    # Send initial state to output
    flag = out.send(dict(state, time=t))
    if not flag:
        raise RuntimeError("timesync(Python): Failed to send "
                           "initial output for t=%s." % t)
    
    # Iterate until end
    while t < t_end:

        # Perform calculations to update the state
        t = t + t_step
        state = timestep_calc(t, xname, yname)

        # Synchronize the state
        ret, result = timesync.call(t, state)
        if not ret:
            raise RuntimeError("timesync(Python): sync for t=%f failed." % t)
        state = result[0]
        print('timesync(Python): t = % 8s, %s = %+ 5.2f, %s = %+ 5.2f' % (
            t, xname, state[xname], yname, state[yname]))

        # Send output
        flag = out.send(dict(state, time=t))
        if not flag:
            raise RuntimeError("timesync(Python): Failed to send output for t=%s." % t)

    print('Goodbye from Python timesync')


if __name__ == '__main__':
    # Take time step from the first argument
    main(float(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
