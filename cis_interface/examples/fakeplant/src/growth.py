from cis_interface.interface import CisInput, CisOutput


def calculate_growth(photosynthesis_rate):
    r"""Calculate the plant growth rate from the photosynthesis rate.

    Args:
        photosynthesis_rate (float): Rate of photosynthesis.

    Returns:
        float: Growth rate.

    """
    return 10 * photosynthesis_rate


if __name__ == '__main__':
    input = CisInput('photosynthesis_rate')
    output = CisOutput('growth_rate', '%f\n')
    
    while True:
        flag, prate = input.recv()
        if not flag:
            print('growth: No more input.')
            break
        grate = calculate_growth(*prate)
        flag = output.send(grate)
        if not flag:
            print('growth: Error sending growth rate.')
            break
