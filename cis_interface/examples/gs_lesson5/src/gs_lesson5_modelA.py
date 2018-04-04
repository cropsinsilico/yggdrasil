# Import classes for input/output channels
from cis_interface.interface.CisInterface import CisInput, CisOutput

# Initialize input/output channels
in_channel = CisInput('inputA')
out_channel = CisOutput('outputA')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, msg = in_channel.recv()
    if not flag:
        print("Model A: No more input.")
        break

    # Print received message
    print('Model A: %s' % msg)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(msg)
    if not flag:
        print("Model A: Error sending output.")
        break
