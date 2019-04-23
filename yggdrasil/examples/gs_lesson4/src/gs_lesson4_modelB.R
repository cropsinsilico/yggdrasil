# Import library for input/output
library(reticulate)
library(zeallot)
ygg <- import('yggdrasil.interface.YggInterface')

# Initialize input/output channels
in_channel <- ygg$YggInput('inputB')
out_channel <- ygg$YggOutput('outputB')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, msg) %<-% in_channel$recv()
  if (!flag) {
    print('Model B: No more input.')
    break
  }

  # Print received message
  print(sprintf('Model B: %s', msg))

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(msg)
  if (!flag) {
    stop('Model B: Error sending output.')
  }

}
