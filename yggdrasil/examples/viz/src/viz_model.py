# Import classes for input/output channels
from yggdrasil.interface.YggInterface import YggInput

# Initialize input/output channels
in_channel = YggInput('input_viz')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, x = in_channel.recv()
    if not flag:
        print("Model B: No more input.")
        # Things that should be done at the end can go here
        break

    # Print received message
    print('Viz model received %f' % x)

    # Any actions that should be taken when a new value is
    # received should go here
