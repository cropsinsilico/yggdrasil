# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggInput', 'inputA')
out_channel <- YggInterface('YggOutput', 'outputA')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, obj) %<-% in_channel$recv()
  if (!flag) {
    print('Model A: No more input.')
    break
  }

  # Print received message
  print('Model A:')
  print(obj)

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(obj)
  if (!flag) {
    stop('Model A: Error sending output.')
  }

}
