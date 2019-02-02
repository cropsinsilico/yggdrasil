from yggdrasil.interface import YggInput, YggOutput


def calculate_growth(photosynthesis_rate):
    r"""Calculate the plant growth rate from the photosynthesis rate.

    Args:
        photosynthesis_rate (float): Rate of photosynthesis.

    Returns:
        float: Growth rate.

    """
    return 0.5 * photosynthesis_rate


if __name__ == '__main__':
    input = YggInput('photosynthesis_rate')
    output = YggOutput('growth_rate', '%f\n')
    
    while True:
        flag, prate = input.recv()
        if not flag:
            print('growth: No more input.')
            break
        grate = calculate_growth(*prate)
        print('growth: photosynthesis rate = %f ---> growth rate = %f' % (
            prate[0], grate))
        flag = output.send(grate)
        if not flag:
            raise RuntimeError('growth: Error sending growth rate.')
