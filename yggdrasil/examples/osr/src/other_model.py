import sys
from yggdrasil import units
from yggdrasil.interface.YggInterface import (
    YggTimesync, YggOutput)


def timestep_calc(t):
    r"""Updates the state based on the time where x is a sine wave
    with period of 10 days and y is a cosine wave with a period of 5 days.

    Args:
        t (float): Current time.

    Returns:
        dict: Map of state parameters.

    """
    state = {"carbonAllocation2Roots": units.add_units(10.0, 'g'),
             "saturatedConductivity": units.add_units(10.0, 'cm/day')}
    return state


def main(t_step, t_units):
    r"""Function to execute integration.

    Args:
        t_step (float): The time step that should be used.
        t_units (str): Units of the time step.

    """
    print('Hello from Python other_model: timestep = %s %s' % (t_step, t_units))
    t_step = units.add_units(t_step, t_units)
    t_start = units.add_units(0.0, t_units)
    t_end = units.add_units(1.0, 'day')
    state = timestep_calc(t_start)

    # Set up connections matching yaml
    # Timestep synchonization connection will default to 'timesync'
    timesync = YggTimesync('timesync')
    out = YggOutput('output')

    # Initialize state and synchronize with other models
    t = t_start
    ret, state = timesync.call(t, state)
    if not ret:
        raise RuntimeError("other_model(Python): Initial sync failed.")
    print('other_model(Python): t = % 8s' % t, end='')
    for k, v in state.items():
        print(', %s = %+ 5.2f' % (k, v), end='')
    print('')

    # Send initial state to output
    flag = out.send(dict(state, time=t))
    if not flag:
        raise RuntimeError("other_model(Python): Failed to send "
                           "initial output for t=%s." % t)
    
    # Iterate until end
    while t < t_end:

        # Perform calculations to update the state
        t = t + t_step
        state = timestep_calc(t)

        # Synchronize the state
        ret, state = timesync.call(t, state)
        if not ret:
            raise RuntimeError("other_model(Python): sync for t=%f failed." % t)
        print('other_model(Python): t = % 8s' % t, end='')
        for k, v in state.items():
            print(', %s = %+ 5.2f' % (k, v), end='')
        print('')

        # Send output
        flag = out.send(dict(state, time=t))
        if not flag:
            raise RuntimeError("other_model(Python): Failed to send output for t=%s." % t)

    print('Goodbye from Python other_model')


if __name__ == '__main__':
    # Take time step from the first argument
    main(float(sys.argv[1]), sys.argv[2])
