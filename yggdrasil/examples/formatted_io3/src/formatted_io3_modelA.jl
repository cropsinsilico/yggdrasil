# Import library for input/output channels
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggAsciiArrayInput", "inputA")
out_channel = Yggdrasil.YggInterface("YggAsciiArrayOutput", "outputA",
                                     "%6s\t%d\t%f\n")

# Loop until there is no longer input or the queues are closed
while true

    # Receive input from input channel
    # If there is an error, the flag will be false
    flag, arr = in_channel.recv_array()
    if (!flag)
        println("Model A: No more input.")
	break
    end

    # Print received message
    println(arr)
    # @printf("Model A: (%d rows)\n", size(arr, 1))
    # for i = 1:size(arr,1)
    #     println(arr[i])
    #     # @printf("   %s, %d, %f", arr[i])
    # end

    # Send output to output channel
    # If there is an error, the flag will be false
    flag = out_channel.send_array(arr)
    if (!flag)
        error("Model A: Error sending output.")
    end

end  # while