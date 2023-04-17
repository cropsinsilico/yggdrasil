# Import library for input/output channels
using Yggdrasil

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggInput", "input")
out_channel = Yggdrasil.YggInterface("YggOutput", "output")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, msg = in_channel.recv()
    if (!flag)
        println("No more input.")
	break
    end

    # Print received message
    println(msg)

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send(msg)
    if (!flag)
        println("Error sending output.")
        break
    end

end  # while