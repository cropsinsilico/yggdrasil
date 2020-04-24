import sys
from matplotlib import pyplot as plt
from yggdrasil.communication.AsciiTableComm import AsciiTableComm


def main(fileA, fileB):
    r"""Method to plot comparison of two results."""
    dataA = AsciiTableComm('test', address=fileA, direction='recv',
                           as_array=True).recv()[1]
    dataB = AsciiTableComm('test', address=fileB, direction='recv',
                           as_array=True).recv()[1]
    plt.plot(dataA[0], dataA[1], 'b-')
    plt.plot(dataA[0], dataA[2], 'r-')
    plt.plot(dataB[0].to(dataA[0].units), dataB[1], 'b--')
    plt.plot(dataB[0].to(dataA[0].units), dataB[2], 'r--')
    plt.show()


if __name__ == '__main__':
    # Take time step from the first argument
    main(sys.argv[1], sys.argv[2])
