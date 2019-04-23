# Import library for input/output
library(reticulate)
library(zeallot)
ygg <- import('yggdrasil.interface.YggInterface')

# Initialize input/output channels
in_channel <- ygg$YggInput('input')
out_channel <- ygg$YggOutput('output')

# Loop until there is no longer input or the queues are closed
while(TRUE) {

  # Receive input from input channel
  # If there is an error, the flag will be False
  c(flag, msg) %<-% in_channel$recv()
  if (!flag) {
    print('No more input.')
    break
  }

  # Print received message
  print(msg)

  # Send output to output channel
  # If there is an error, the flag will be False
  flag = out_channel$send(msg)
  if (!flag) {
    print('Error sending output.')
    break
  }

}
