# Import classes for input/output channels
from yggdrasil.interface.YggInterface import YggInput, YggOutput

# Initialize input/output channels
in_channel = YggInput('input')
out_channel = YggOutput('output')

# Loop until there is no longer input or the queues are closed
while True:
    
    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, msg = in_channel.recv()
    if not flag:
        print("No more input.")
        break

    # Print received message
    print(msg)

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(msg)
    if not flag:
        print("Error sending output.")
        break
