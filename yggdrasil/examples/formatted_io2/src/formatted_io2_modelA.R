# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggAsciiTableInput', 'inputA')
out_channel <- YggInterface('YggAsciiTableOutput', 'outputA', '%6s\t%d\t%f\n')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, msg) %<-% in_channel$recv()
  if (!flag) {
    print('Model A: No more input.')
    break
  }
  c(name, count, size) %<-% msg

  # Print received message
  fprintf('Model A: %s, %d, %f', name, count, size)

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(name, count, size)
  if (!flag) {
    stop('Model A: Error sending output.')
  }

}
