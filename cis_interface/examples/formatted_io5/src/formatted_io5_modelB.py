import pprint
# Import classes for input/output channels
from cis_interface.interface.CisInterface import (
    CisPlyInput, CisPlyOutput)

# Initialize input/output channels
in_channel = CisPlyInput('inputB')
out_channel = CisPlyOutput('outputB')

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
        print("Model B: Error sending output.")
        break
