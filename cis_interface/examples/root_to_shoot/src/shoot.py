import time


def calc_shoot_mass(r_s, dt, S_t, R_t, R_tp1):
    r"""Calculate the shoot mass.

    Args:
        r_s (float): Relative shoot growth rate.
        dt (float): The time step.
        S_t (float): Previous shoot mass.
        R_t (float): Previous root mass.
        R_tp1 (float): Root mass at the next timestep.

    Returns:
        float: Shoot mass at the next timestep.

    """
    time.sleep(0.1)  # To simulate a longer calculation
    return (S_t * r_s * dt) + S_t - (R_tp1 - R_t)
