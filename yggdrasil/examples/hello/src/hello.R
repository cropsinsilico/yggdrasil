library(yggdrasil)

print('Hello from R')

# Ins/outs matching with the the model yaml
inf <- YggInterface('YggInput', 'inFile')
outf <- YggInterface('YggOutput', 'outFile')
inq <- YggInterface('YggInput', 'helloQueueIn')
outq <- YggInterface('YggOutput', 'helloQueueOut')
print("hello(R): Created I/O channels")

# Receive input from a local file
c(ret, buf) %<-% inf$recv()
if (!ret) {
  stop('hello(R): ERROR FILE RECV')
}
fprintf('hello(R): Received %d bytes from file: %s', length(buf), buf)

# Send output to the output queue
ret <- outq$send(buf)
if (!ret) {
  stop('hello(R): ERROR QUEUE SEND')
}
print('hello(R): Sent to outq')

# Receive input form the input queue
c(ret, buf) %<-% inq$recv()
if (!ret) {
  stop('hello(R): ERROR QUEUE RECV')
}
fprintf('hello(R): Received %d bytes from queue: %s', length(buf), buf)

# Send output to a local file
ret <- outf$send(buf)
if (!ret) {
  stop('hello(R): ERROR FILE SEND')
}
print('hello(R): Sent to outf')

print('Goodbye from R')
