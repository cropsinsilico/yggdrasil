# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggInput', 'input')
out_channel <- YggInterface('YggOutput', 'output')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, obj) %<-% in_channel$recv()
  if (!flag) {
    print('R Model: No more input.')
    break
  }

  # Print received message
  print('R Model:')
  print(obj)

  # Print keys
  print('R Model: keys = ')
  print(names(obj))

  # Get floating point element
  co2 = obj[["CO2"]]
  print(sprintf('R Model: CO2 = %f', co2))

  # Get array element
  amaxtb = obj[["AMAXTB"]]
  print('R Model: AMAXTB = ')
  for (i in 1:length(amaxtb[[1]])) {
    print(sprintf('\t%f\t%f', amaxtb[[1]][[i]], amaxtb[[2]][[i]]))
  }

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(obj)
  if (!flag) {
    stop('R Model: Error sending output.')
  }

}
