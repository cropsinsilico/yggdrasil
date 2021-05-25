# Import library for input/output channels
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggPandasInput", "inputA")
out_channel = Yggdrasil.YggInterface("YggPandasOutput", "outputA")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, frame = in_channel.recv()
    if (!flag)
        println("Model A: No more input.")
	break
    end

    # Print received message
    # nrows = len(frame.index)
    # @printf("Model A: (%d rows)\n", nrows)
    println(frame)

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send(frame)
    if (!flag)
        error("Model A: Error sending output.")
    end

end  # while