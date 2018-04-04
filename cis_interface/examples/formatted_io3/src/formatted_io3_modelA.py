# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisAsciiArrayInput, CisAsciiArrayOutput)

# Initialize input/output channels
in_channel = CisAsciiArrayInput('inputA')
out_channel = CisAsciiArrayOutput('outputA', '%6s\t%d\t%f\n')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, arr = in_channel.recv()
    if not flag:
        print("Model A: No more input.")
        break

    # Print received message
    print('Model A: (%d rows)' % len(arr))
    for i in range(len(arr)):
        print('   %s, %d, %f' % tuple(arr[i]))

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(arr)
    if not flag:
        print("Model A: Error sending output.")
        break
