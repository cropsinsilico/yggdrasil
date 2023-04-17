# Import library for input/output channels
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggPlyInput", "inputA")
out_channel = Yggdrasil.YggInterface("YggPlyOutput", "outputA")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, ply = in_channel.recv()
    if (!flag)
        println("Model A: No more input.")
	break
    end

    # Print received message
    println(ply)
    # @printf("Model A: (%d verts, %d faces)\n",
    #         length(get(ply, "vertices")),
    #         length(get(ply, "faces")))

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send(ply)
    if (!flag)
        error("Model A: Error sending output.")
    end

end  # while