# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisAsciiArrayInput, CisAsciiArrayOutput)

# Initialize input/output channels
in_channel = CisAsciiArrayInput('inputB')
out_channel = CisAsciiArrayOutput('outputB', '%6s\t%d\t%f\n')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, arr = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        break

    # Print received message
    print('Model B: (%d rows)' % len(arr))
    for i in range(len(arr)):
        print('   %s, %d, %f' % tuple(arr[i]))

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(arr)
    if not flag:
        print("Model B: Error sending output.")
        break
