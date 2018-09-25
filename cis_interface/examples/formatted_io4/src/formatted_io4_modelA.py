# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisPandasInput, CisPandasOutput)

# Initialize input/output channels
in_channel = CisPandasInput('inputA')
out_channel = CisPandasOutput('outputA')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, frame = in_channel.recv()
    if not flag:
        print("Model A: No more input.")
        break

    # Print received message
    nrows = len(frame.index)
    print('Model A: (%d rows)' % len(frame.index))
    print(frame)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(frame)
    if not flag:
        print("Model A: Error sending output.")
        break
