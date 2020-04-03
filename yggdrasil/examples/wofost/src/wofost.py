# Import classes for input/output channels
from yggdrasil.interface.YggInterface import YggInput, YggOutput

# Initialize input/output channels
in_channel = YggInput('input')
out_channel = YggOutput('output')

# Loop until there is no longer input or the queues are closed
while True:

    # Receive input from input channel
    # If there is an error, the flag will be False
    flag, obj = in_channel.recv()
    if not flag:
        print("Python Model: No more input.")
        break

    # Print received message
    print('Python Model: %s' % str(obj))

    # Print keys
    print('Python Model: keys = %s' % str(obj.keys()))

    # Get floating point element
    co2 = obj['CO2']
    print('Python Model: CO2 = %f' % co2)

    # Get array element
    amaxtb = obj['AMAXTB']
    print('Python Model: AMAXTB = ')
    for x, y in zip(*amaxtb):
        print('\t%f\t%f' % (x, y))

    # Send output to output channel
    # If there is an error, the flag will be False
    flag = out_channel.send(obj)
    if not flag:
        raise RuntimeError("Python Model: Error sending output.")
