# Import classes for input/output channels
from yggdrasil.interface.YggInterface import (
    YggAsciiTableInput, YggAsciiTableOutput)

# Initialize input/output channels
in_channel = YggAsciiTableInput('inputA')
out_channel = YggAsciiTableOutput('outputA', '%6s\t%d\t%f\n')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, msg = in_channel.recv()
    if not flag:
        print("Model A: No more input.")
        break
    name, count, size = msg

    # Print received message
    print('Model A: %s, %d, %f' % (name, count, size))

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(name, count, size)
    if not flag:
        raise RuntimeError("Model A: Error sending output.")
