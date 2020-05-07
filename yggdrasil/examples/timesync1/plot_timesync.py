import sys
import numpy as np
from matplotlib import pyplot as plt
from yggdrasil import units
from yggdrasil.communication.AsciiTableComm import AsciiTableComm


def main(fileA, fileB, example_name):
    r"""Method to plot comparison of two results."""
    dataA = AsciiTableComm('test', address=fileA, direction='recv',
                           as_array=True).recv()[1]
    dataB = AsciiTableComm('test', address=fileB, direction='recv',
                           as_array=True).recv()[1]
    xtrue = np.sin(2.0 * np.pi * dataA[0] / units.add_units(10, 'day'))
    ytrue = np.cos(2.0 * np.pi * dataA[0] / units.add_units(5, 'day'))
    if example_name == 'timesync2':
        ytrue *= 2.0
        dataB[1] *= 2.0
    plt.plot(dataA[0], xtrue, 'k')
    plt.plot(dataA[0], ytrue, 'k')
    plt.plot(dataA[0], dataA[1], 'b-', label='x (model A)')
    plt.plot(dataA[0], dataA[2], 'r-', label='y (model A)')
    plt.plot(dataB[0].to(dataA[0].units), dataB[1], 'b--',
             label='x (model B)')
    plt.plot(dataB[0].to(dataA[0].units), dataB[2], 'r--',
             label='y (model B)')
    plt.xlabel('Time (%s)' % dataA[0].units)
    plt.ylabel('State Value')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    # Take time step from the first argument
    if len(sys.argv) >= 4:
        example_name = sys.argv[3]
    else:
        example_name = 'timesync1'
    main(sys.argv[1], sys.argv[2], example_name)
