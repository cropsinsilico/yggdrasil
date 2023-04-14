# Import library for input/output channels
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggAsciiTableInput", "inputA")
out_channel = Yggdrasil.YggInterface("YggAsciiTableOutput", "outputA",
                                     "%6s\t%d\t%f\n")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, msg = in_channel.recv()
    if (!flag)
        println("Model A: No more input.")
	break
    end
    name, count, size = msg

    # Print received message
    @printf("Model A: %s, %d, %f\n", name, count, size)

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send(name, count, size)
    if (!flag)
        error("Model A: Error sending output.")
    end

end  # while