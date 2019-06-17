# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggAsciiArrayInput', 'inputB')
out_channel <- YggInterface('YggAsciiArrayOutput', 'outputB', '%6s\t%d\t%f\n')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, arr) %<-% in_channel$recv_array()
  if (!flag) {
    print('Model B: No more input.')
    break
  }

  # Print received message
  nr = length(arr);
  fprintf('Model B: (%d rows)', nr)
  for (i in 1:nr) {
    fprintf('   %s, %d, %f', arr[[i]][[1]], arr[[i]][[2]], arr[[i]][[3]])
  }

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send_array(arr)
  if (!flag) {
    stop('Model B: Error sending output.')
  }

}
