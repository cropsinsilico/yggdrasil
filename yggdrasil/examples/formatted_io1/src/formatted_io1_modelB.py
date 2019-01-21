# Import classes for input/output channels
from yggdrasil.interface.YggInterface import YggInput, YggOutput

# Initialize input/output channels
in_channel = YggInput('inputB')
out_channel = YggOutput('outputB')

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
        raise RuntimeError("Model B: Error sending output.")
