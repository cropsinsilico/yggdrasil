# Import classes for input/output channels
from cis_interface.interface.CisInterface import CisInput, CisOutput

# Initialize input/output channels
in_channel = CisInput('inputB')
out_channel = CisOutput('outputB')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, msg = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        break

    # Print received message
    print('Model B: %s' % msg)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(msg)
    if not flag:
        print("Model B: Error sending output.")
        break
