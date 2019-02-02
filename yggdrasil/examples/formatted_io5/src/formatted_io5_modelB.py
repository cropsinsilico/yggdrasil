import pprint
# Import classes for input/output channels
from yggdrasil.interface.YggInterface import (
    YggPlyInput, YggPlyOutput)

# Initialize input/output channels
in_channel = YggPlyInput('inputB')
out_channel = YggPlyOutput('outputB')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, ply = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        break

    # Print received message
    print('Model B: (%d verts, %d faces)' % (ply.nvert, ply.nface))
    pprint.pprint(ply)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(ply)
    if not flag:
        raise RuntimeError("Model B: Error sending output.")
