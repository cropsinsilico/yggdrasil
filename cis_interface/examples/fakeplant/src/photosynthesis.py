import sys
from cis_interface.interface import CisInput, CisOutput


def calc_photosynthesis_rate(T, CO2, light):
    r"""Calculate the rate of photosynthesis from environment properties.

    Args:
        T (float): Temperature.
        CO2 (float): CO2 concentration.
        light (float): Light intensity.

    Returns:
        float: Photosynthesis rate.

    """
    return light * CO2 / T


if __name__ == '__main__':
    in_temp = CisInput('temperature')
    in_co2 = CisInput('co2')
    in_light = CisInput('light_intensity')
    out_photo = CisOutput('photosynthesis_rate', '%lf\n')
    
    # Receive temperature & CO2 concentration of environment
    flag, msg = in_temp.recv()
    if not flag:
        print("photosynthesis: Failed to receive temperature.")
        sys.exit(-1)
    T = msg[0]
    print("photosynthesis: T = %f" % T)
    flag, msg = in_co2.recv()
    if not flag:
        print("photosynthesis: Failed to receive CO2 concentration.")
        sys.exit(-1)
    CO2 = msg[0]
    print("photosynthesis: CO2 = %f" % CO2)

    # Loop over light intensities
    while True:
        flag, msg = in_light.recv()
        if not flag:
            print("photosynthesis: No more input.")
            break
        LI = msg[0]
        PR = calc_photosynthesis_rate(T, CO2, LI)
        print("photosynthesis: light intensity = %f " % LI +
              "--> photosynthesis rate = %f" % PR)
        flag = out_photo.send(PR)
        if not flag:
            print("photosynthesis: Failed to send output.")
            sys.exit(-1)

    sys.exit(0)
