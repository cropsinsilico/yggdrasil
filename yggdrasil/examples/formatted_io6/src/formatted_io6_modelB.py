import pprint
# Import classes for input/output channels
from yggdrasil.interface.YggInterface import (
    YggObjInput, YggObjOutput)

# Initialize input/output channels
in_channel = YggObjInput('inputB')
out_channel = YggObjOutput('outputB')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, obj = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        break

    # Print received message
    print('Model B: (%d verts, %d faces)' % (obj.nvert, obj.nface))
    pprint.pprint(obj)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(obj)
    if not flag:
        raise RuntimeError("Model B: Error sending output.")
