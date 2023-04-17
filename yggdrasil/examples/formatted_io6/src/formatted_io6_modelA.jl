# Import library for input/output channels
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggObjInput", "inputA")
out_channel = Yggdrasil.YggInterface("YggObjOutput", "outputA")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, obj = in_channel.recv()
    if (!flag)
        println("Model A: No more input.")
	break
    end

    # Print received message
    println(obj)
    # @printf("Model A: (%d verts, %d faces)\n",
    #         length(get(obj, "vertices")),
    #         length(get(obj, "faces")))

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send(obj)
    if (!flag)
        error("Model A: Error sending output.")
    end

end  # while