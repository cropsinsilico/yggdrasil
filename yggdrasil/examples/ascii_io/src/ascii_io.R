library(yggdrasil)

# Input & output to an ASCII file line by line
in_file <- YggInterface('YggAsciiFileInput', 'inputR_file')
out_file <- YggInterface('YggAsciiFileOutput', 'outputR_file')
# Input & output from a table row by row
in_table <- YggInterface('YggAsciiTableInput', 'inputR_table')
out_table <- YggInterface('YggAsciiTableOutput', 'outputR_table',
                          '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n')
# Input & output from a table as an array
in_array <- YggInterface('YggAsciiArrayInput', 'inputR_array')
out_array <- YggInterface('YggAsciiArrayOutput', 'outputR_array',
                          '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n')

# Read lines from ASCII text file until end of file is reached.
# As each line is received, it is then sent to the output ASCII file.
print('ascii_io(R): Receiving/sending ASCII file.')
ret = TRUE
while (ret) {
  # Receive a single line
  c(ret, line) %<-% in_file$recv()
  if (ret) {
    # If the receive was succesful, send the line to output
    fprintf('File: %s', line)
    ret <- out_file$send(line)
    if (!ret) {
      stop("ascii_io(R): ERROR SENDING LINE")
    }
  } else {
    # If the receive was not succesful, send the end-of-file message to
    # close the output file.
    print("End of file input (R)")
    out_file$send_eof()
  }
}

# Read rows from ASCII table until end of file is reached.
# As each row is received, it is then sent to the output ASCII table
print('ascii_io(R): Receiving/sending ASCII table.')
ret <- TRUE
while (ret) {
  # Receive a single row
  c(ret, line) %<-% in_table$recv()
  if (ret) {
    # If the receive was succesful, send the values to output.
    # Formatting is taken care of on the output driver side.
    fprintf("Table: %s, %d, %3.1f, %s", line[[1]], line[[2]], line[[3]], line[[4]])
    ret <- out_table$send(line[[1]], line[[2]], line[[3]], line[[4]])
    if (!ret) {
      stop("ascii_io(R): ERROR SENDING ROW")
    }
  } else {
    # If the receive was not succesful, send the end-of-file message to
    # close the output file.
    print("End of table input (R)")
    out_table$send_eof()
  }
}

# Read entire array from ASCII table into numpy array
ret <- TRUE
while (ret) {
  c(ret, arr) %<-% in_array$recv_array()
  if (ret) {
    fprintf("Array: (%d rows)", length(arr))
    # Print each line in the array
    for (i in 1:length(arr)) {
      fprintf("%5s, %d, %3.1f, %s",
              arr[[i]][[1]], arr[[i]][[2]], arr[[i]][[3]], arr[[i]][[4]])
    }
    # Send the array to output. Formatting is handled on the output driver side.
    ret <- out_array$send_array(arr)
    if (!ret) {
      stop("ascii_io(R): ERROR SENDING ARRAY")
    }
  } else {
    print("ascii_io(R): End of array input (R)")
  }
}
