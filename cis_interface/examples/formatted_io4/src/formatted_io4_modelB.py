# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisPandasInput, CisPandasOutput)

# Initialize input/output channels
in_channel = CisPandasInput('inputB')
out_channel = CisPandasOutput('outputB')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, frame = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        break

    # Print received message
    nrows = len(frame.index)
    print('Model B: (%d rows)' % nrows)
    print(frame)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(frame)
    if not flag:
        print("Model B: Error sending output.")
        break
