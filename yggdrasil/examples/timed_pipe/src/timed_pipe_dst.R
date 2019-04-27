library(yggdrasil)


run <- function() {
  print('Hello from R pipe_dst')

  # Ins/outs matching with the the model yaml
  inq <- YggInterface('YggInput', 'input_pipe')
  outf <- YggInterface('YggOutput', 'output_file')
  print("pipe_dst(R): Created I/O channels")

  # Continue receiving input from the queue
  count <- 0
  while (TRUE) {
    c(ret, buf) %<-% inq$recv()
    if (!ret) {
      print("pipe_dst(R): Input channel closed")
      break
    }
    ret <- outf$send(buf)
    if (!ret) {
      stop(sprintf("pipe_dst(R): SEND ERROR ON MSG %d", count))
    }
    count <- count + 1
  }

  fprintf('Goodbye from R destination. Received %d messages.', count)
}


run()
