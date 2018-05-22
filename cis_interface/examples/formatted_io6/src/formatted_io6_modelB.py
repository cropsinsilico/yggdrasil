import pprint
# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisObjInput, CisObjOutput)

# Initialize input/output channels
in_channel = CisObjInput('inputB')
out_channel = CisObjOutput('outputB')

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
        print("Model B: Error sending output.")
        break
