import pprint
# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisObjInput, CisObjOutput)

# Initialize input/output channels
in_channel = CisObjInput('inputA')
out_channel = CisObjOutput('outputA')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, obj = in_channel.recv()
    if not flag:
        print("Model A: No more input.")
        break

    # Print received message
    print('Model A: (%d verts, %d faces)' % (obj.nvert, obj.nface))
    pprint.pprint(obj)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(obj)
    if not flag:
        print("Model A: Error sending output.")
        break
