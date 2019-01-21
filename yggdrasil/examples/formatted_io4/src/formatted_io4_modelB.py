# Import classes for input/output channels
from yggdrasil.interface.YggInterface import (
    YggPandasInput, YggPandasOutput)

# Initialize input/output channels
in_channel = YggPandasInput('inputB')
out_channel = YggPandasOutput('outputB')

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
        raise RuntimeError("Model B: Error sending output.")
