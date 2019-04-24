# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggInput', 'inputA')
out_channel <- YggInterface('YggOutput', 'outputA')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, msg) %<-% in_channel$recv()
  if (!flag) {
    print('Model A: No more input.')
    break
  }

  # Print received message
  fprintf('Model A: %s', msg)

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(msg)
  if (!flag) {
    stop('Model A: Error sending output.')
  }

}
