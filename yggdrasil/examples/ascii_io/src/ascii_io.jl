# Import library for input/output channels
using Yggdrasil
using Printf

# Input & output to an ASCII file line by line
in_file = Yggdrasil.YggInterface("YggAsciiFileInput", "inputJulia_file")
out_file = Yggdrasil.YggInterface("YggAsciiFileOutput", "outputJulia_file")
# Input & output from a table row by row
in_table = Yggdrasil.YggInterface("YggAsciiTableInput", "inputJulia_table")
out_table = Yggdrasil.YggInterface("YggAsciiTableOutput", "outputJulia_table",
     	                           "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n")
# Input & output from a table as an array
in_array = Yggdrasil.YggInterface("YggAsciiArrayInput", "inputJulia_array")
out_array = Yggdrasil.YggInterface("YggAsciiArrayOutput", "outputJulia_array",
	                           "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n")

# Read lines from ASCII text file until end of file is reached.
# As each line is received, it is then sent to the output ASCII file.
println("ascii_io(Julia): Receiving/sending ASCII file.")
ret = true
while (ret)
  # Receive a single line
  global ret, line = in_file.recv()
  if (ret)
    # If the receive was succesful, send the line to output
    @printf("File: %s\n", line)
    global ret = out_file.send(line)
    if (!ret)
      error("ascii_io(Julia): ERROR SENDING LINE")
    end
  else
    # If the receive was not succesful, send the end-of-file message to
    # close the output file.
    println("End of file input (Julia)")
    out_file.send_eof()
  end
end

# Read rows from ASCII table until end of file is reached.
# As each row is received, it is then sent to the output ASCII table
println("ascii_io(Julia): Receiving/sending ASCII table.")
ret = true
while (ret)
  # Receive a single row
  global ret, line = in_table.recv()
  if (ret)
    # If the receive was succesful, send the values to output.
    # Formatting is taken care of on the output driver side.
    println(line)
    println(typeof(line))
    @printf("Table: %s, %d, %3.1f, %s\n", line[1], line[2], line[3], line[4])
    global ret = out_table.send(line[1], line[2], line[3], line[4])
    if (!ret)
      error("ascii_io(Julia): ERROR SENDING ROW")
    end
  else
    # If the receive was not succesful, send the end-of-file message to
    # close the output file.
    println("End of table input (Julia)")
    out_table.send_eof()
  end
end

# Read entire array from ASCII table into numpy array
ret = true
while (ret)
  global ret, arr = in_array.recv_array()
  if (ret)
    @printf("Array: (%d rows)\n", length(arr))
    # Print each line in the array
    for i = 1:length(arr)
      @printf("%5s, %d, %3.1f, %s\n",
              arr[i][1], arr[i][2], arr[i][3], arr[i][4])
    end
    # Send the array to output. Formatting is handled on the output driver side.
    global ret = out_array.send_array(arr)
    if (!ret)
      error("ascii_io(Julia): ERROR SENDING ARRAY")
    end
  else
    print("ascii_io(Julia): End of array input (Julia)")
  end
end
