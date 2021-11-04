import sys
import numpy as np
from matplotlib import pyplot as plt
from yggdrasil import units
from yggdrasil.communication.AsciiTableComm import AsciiTableComm


def main(fileA, fileB, example_name):
    r"""Method to plot comparison of two results."""
    if example_name == 'timesync2':
        figsize = (10.8, 4.8)
        fig = plt.figure(figsize=figsize)
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2, sharey=ax1)
        ax3 = fig.add_subplot(2, 2, 3, sharex=ax1)
        axs = [ax1, ax2, ax3]
    else:
        figsize = None
        fig = plt.figure(figsize=figsize)
        ax1 = fig.add_subplot(1, 1, 1)
        axs = [ax1]
    dataA = AsciiTableComm('test', address=fileA, direction='recv',
                           as_array=True).recv_dict()[1]
    dataB = AsciiTableComm('test', address=fileB, direction='recv',
                           as_array=True).recv_dict()[1]
    xtrue = np.sin(2.0 * np.pi * dataA['time'] / units.add_units(10, 'day'))
    ytrue = np.cos(2.0 * np.pi * dataA['time'] / units.add_units(5, 'day'))
    ztrue = -np.cos(2.0 * np.pi * dataA['time'] / units.add_units(20, 'day'))
    atrue = np.sin(2.0 * np.pi * dataA['time'] / units.add_units(2.5, 'day'))
    btrue = np.cos(2.0 * np.pi * dataA['time'] / units.add_units(2.5, 'day'))
    if example_name == 'timesync2':
        ytrue *= 2.0
        dataB['x'] = 2.0 * dataB['xvar']
        dataB['y'] = dataB['yvar']
    ax1.plot(dataA['time'], xtrue, 'k')
    ax1.plot(dataA['time'], ytrue, 'k')
    ax1.plot(dataA['time'], dataA['x'], 'b-', label='x (model A)')
    ax1.plot(dataA['time'], dataA['y'], 'r-', label='y (model A)')
    ax1.plot(dataB['time'].to(dataA['time'].units), dataB['x'],
             'b--', label='x (model B)')
    ax1.plot(dataB['time'].to(dataA['time'].units), dataB['y'],
             'r--', label='y (model B)')
    ax1.set_xlabel('Time (%s)' % dataA['time'].units)
    ax1.set_ylabel('State Value')
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
    if example_name == 'timesync2':
        ax2.plot(dataA['time'], ztrue, 'k')
        ax2.plot(dataA['time'], dataA['z1'], 'o-', label='z1 (model A)')
        ax2.plot(dataA['time'], dataA['z2'], 'o-', label='z2 (model A)')
        ax2.plot(dataB['time'].to(dataA['time'].units), dataB['z'],
                 'o--', label='z (model B)')
        ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
        ax3.plot(dataA['time'], atrue, 'k')
        ax3.plot(dataA['time'], btrue, 'k')
        ax3.plot(dataA['time'], dataA['a'], 'c-', label='a (model A)')
        ax3.plot(dataA['time'], dataA['b'], 'm-', label='b (model A)')
        ax3.plot(dataB['time'].to(dataA['time'].units), dataB['a'],
                 'c--', label='a (model B)')
        ax3.plot(dataB['time'].to(dataA['time'].units), dataB['b'],
                 'm--', label='b (model B)')
        ax3.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
        plt.subplots_adjust(left=0.075, right=0.95, wspace=0.1, hspace=0.45)
    return fig, axs


if __name__ == '__main__':
    # Take time step from the first argument
    if len(sys.argv) >= 4:
        example_name = sys.argv[3]
    else:
        example_name = 'timesync1'
    fig, axs = main(sys.argv[1], sys.argv[2], example_name)
    plt.show()
