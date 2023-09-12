# Import library for input/output
using Yggdrasil
using Printf

# Initialize input/output channels
in_channel = Yggdrasil.YggInterface("YggInput", "input")
out_channel = Yggdrasil.YggInterface("YggOutput", "output")

# Loop until there is no longer input or the queues are closed
while(true)

  # Receive input from input channel
  # If there is an error, the flag will be False
  flag, obj = in_channel.recv()
  if (!flag)
    println("Julia Model: No more input.")
    break
  end

  # Print received message
  @printf("Julia Model: %s\n", obj)

  # Print keys
  @printf("Julia Model: keys = %s\n", keys(obj))

  # Get floating point element
  co2 = obj["CO2"]
  @printf("Julia Model: CO2 = %f\n", co2)

  # Get array element
  amaxtb = obj["AMAXTB"]
  println("Julia Model: AMAXTB = ")
  for i = 1:length(amaxtb[1])
    @printf("\t%s\t%s\n", amaxtb[1][i], amaxtb[2][i])
  end

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel.send(obj)
  if (!flag)
    error("Julia Model: Error sending output.")
  end

end
