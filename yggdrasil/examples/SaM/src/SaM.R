library(yggdrasil)


# Get input and output channels matching yaml
in1 <- YggInterface('YggInput', 'input1_R')
in2 <- YggInterface('YggInput', 'static_R')
out1 <- YggInterface('YggOutput', 'output_R')
print('SaM(R): Set up I/O channels')

# Get input from input1 channel
c(ret, adata) %<-% in1$recv()
if (!ret) {
  stop('SaM(R): ERROR RECV from input1')
}
a <- strtoi(adata)
fprintf('SaM(R): Received %d from input1', a)

# Get input from static channel
c(ret, bdata) %<-% in2$recv()
if (!ret) {
  stop('SaM(R): ERROR RECV from static')
}
b <- strtoi(bdata)
fprintf('SaM(R): Received %d from static', b)

# Compute sum and send message to output channel
sum <- a + b
outdata = sprintf('%d', sum)
ret <- out1$send(outdata)
if (!ret) {
  stop('SaM(R): ERROR SEND to output')
}
print('SaM(R): Sent to output')
