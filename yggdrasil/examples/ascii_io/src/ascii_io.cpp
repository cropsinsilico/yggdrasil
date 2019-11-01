#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "YggInterface.hpp"

#define BSIZE 8192 // the max


int main(int argc,char *argv[]){
  int ret;
  int error_code = 0;

  // Input & output to an ASCII file line by line
  YggAsciiFileInput FileInput("inputCPP_file");
  YggAsciiFileOutput FileOutput("outputCPP_file");
  // Input & output from a table row by row
  YggAsciiTableInput TableInput("inputCPP_table");
  YggAsciiTableOutput TableOutput("outputCPP_table",
                                  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");
  // Input & output from a table as an array
  YggAsciiArrayInput ArrayInput("inputCPP_array");
  YggAsciiArrayOutput ArrayOutput("outputCPP_array",
				  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("ascii_io(CPP): Receiving/sending ASCII file.\n");
  char *line = (char*)malloc(LINE_SIZE_MAX);
  // char line[LINE_SIZE_MAX];
  ret = 0;
  while (ret >= 0) {
    // Receive a single line
    ret = FileInput.recv_line(line, LINE_SIZE_MAX);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      ret = FileOutput.send_line(line);
      if (ret < 0) {
	printf("ascii_io(CPP): ERROR SENDING LINE\n");
	error_code = -1;
	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of file input (CPP)\n");
      // FileOutput.send_eof();
    }
  }
  free(line);

  // Read rows from ASCII table until end of file is reached.
  // As each row is received, it is then sent to the output ASCII table
  printf("ascii_io(CPP): Receiving/sending ASCII table.\n");
  size_t name_siz = BSIZE;
  size_t * const p_name_siz = &name_siz; // Required in C++ to get name size
  char name[BSIZE];
  int number;
  double value;
  std::complex<double> comp;
  ret = 0;
  while (ret >= 0) {
    name_siz = BSIZE;  // Reset to buffer size

    // Receive a single row with values stored in scalars declared locally
    ret = TableInput.recv(5, &name, &name_siz, &number, &value, &comp);
    name_siz = strlen(name);
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %.5s, %d, %3.1f, %3.1lf%+3.1lfj\n", name, number, value,
  	     std::real(comp), std::imag(comp));
      ret = TableOutput.send(5, name, name_siz, number, value, comp);
      if (ret < 0) {
      	printf("ascii_io(CPP): ERROR SENDING ROW\n");
      	error_code = -1;
      	break;
      }
      name_siz = BSIZE;
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of table input (CPP)\n");
    }
  }

  // Read entire array from ASCII table into columns that are dynamically
  // allocated. The returned values tells us the number of elements in the
  // columns.
  printf("Receiving/sending ASCII table as array.\n");
  size_t nrows;
  char *name_arr = NULL;
  long *number_arr = NULL;
  double *value_arr = NULL;
  std::complex<double> *comp_arr = NULL;
  ret = 0;
  while (ret >= 0) {
    ret = ArrayInput.recvRealloc(5, &nrows, &name_arr, &number_arr, &value_arr, &comp_arr);
    if (ret >= 0) {
      printf("Array: (%lu rows)\n", nrows);
      // Print each line in the array
      for (size_t i = 0; i < nrows; i++)
  	printf("%.5s, %ld, %3.1f, %3.1lf%+3.1lfj\n", &name_arr[5*i], number_arr[i],
  	       value_arr[i], std::real(comp_arr[i]), std::imag(comp_arr[i]));
      // Send the columns in the array to output. Formatting is handled on the
      // output driver side.
      ret = ArrayOutput.send(5, nrows, name_arr, number_arr, value_arr, comp_arr);
      if (ret < 0) {
  	printf("ascii_io(CPP): ERROR SENDING ARRAY\n");
  	error_code = -1;
  	break;
      }
    } else {
      printf("End of array input (C++)\n"); 
    }
  }
  
  // Free dynamically allocated columns
  if (name_arr) free(name_arr);
  if (number_arr) free(number_arr);
  if (value_arr) free(value_arr);
  if (comp_arr) free(comp_arr);

  return error_code;
}
