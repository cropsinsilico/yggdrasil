import sys
from cis_interface.interface import CisInput, CisOutput


def calc_shoot_mass(r_s, S_t, R_t, R_tp1):
    r"""Calculate the shoot mass.

    Args:
        r_s (float): Relative shoot growth rate.
        S_t (float): Previous shoot mass.
        R_t (float): Previous root mass.
        R_tp1 (float): Root mass at the next timestep.

    Returns:
        float: Shoot mass at the next timestep.

    """
    return (S_t * r_s) + S_t - (R_tp1 - R_t)


if __name__ == '__main__':

    ShootInput = CisInput('shoot_input')
    NextRootMass = CisInput('next_root_mass')
    NextShootMass = CisOutput('next_shoot_mass', '%lf\n')

    # Receive number of timesteps, shoot growth rate, and initial shoot mass
    flag, input = ShootInput.recv()
    if not flag:
        print('shoot: Error receiving shoot growth rate.')
        sys.exit(-1)
    nstep, r_s, S_t = input

    # Send initial shoot mass
    flag = NextShootMass.send(S_t);
    if not flag:
        print('shoot: Error sending initial shoot mass.')
        sys.exit(-1)

    # Receive inital root mass
    flag, input = NextRootMass.recv()
    if not flag:
        print('shoot: Error receiving initial root mass.')
        sys.exit(-1)
    R_t = input[0]

    # Loop over timesteps, outputing shoot masses
    for i in range(nstep):
        flag, input = NextRootMass.recv()
        if not flag:
            print('shoot: Error receiving root mass for timestep %d.' % (i + 1))
            sys.exit(-1)
        R_tp1 = input[0]

        S_tp1 = calc_shoot_mass(r_s, S_t, R_t, R_tp1)

        flag = NextShootMass.send(S_tp1)
        if not flag:
            print('shoot: Error sending shoot amss for timestep %d.' % (i + 1))
            sys.exit(-1)

        S_t = S_tp1
        R_t = R_tp1

    sys.exit(0)
