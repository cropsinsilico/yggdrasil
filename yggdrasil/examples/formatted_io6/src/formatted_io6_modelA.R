# Import library for input/output
library(yggdrasil)

# Initialize input/output channels
in_channel <- YggInterface('YggObjInput', 'inputA')
out_channel <- YggInterface('YggObjOutput', 'outputA')

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
  fprintf('Model A: (%d verts, %d faces)',
          length(obj[['vertices']]), length(obj[['faces']]))

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(obj)
  if (!flag) {
    stop('Model A: Error sending output.')
  }

}
