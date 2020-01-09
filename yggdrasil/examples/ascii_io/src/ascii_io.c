#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "YggInterface.h"

#define BSIZE 8192 // the max



int main(int argc,char *argv[]){
  int ret;
  int error_code = 0;

  // Input & output to an ASCII file line by line
  yggAsciiFileInput_t FileInput = yggAsciiFileInput("inputC_file");
  yggAsciiFileOutput_t FileOutput = yggAsciiFileOutput("outputC_file");
  // Input & output from a table row by row
  yggAsciiTableInput_t TableInput = yggAsciiTableInput("inputC_table");
  yggAsciiTableOutput_t TableOutput = yggAsciiTableOutput("outputC_table",
							  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");
  // Input & output from a table as an array
  yggAsciiArrayInput_t ArrayInput = yggAsciiArrayInput("inputC_array");
  yggAsciiArrayOutput_t ArrayOutput = yggAsciiArrayOutput("outputC_array",
							  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("ascii_io(C): Receiving/sending ASCII file.\n");
  size_t line_size = LINE_SIZE_MAX;
  char *line = (char*)malloc(line_size);
  ret = 0;
  while (ret >= 0) {
    line_size = LINE_SIZE_MAX; // Reset to size of buffer

    // Receive a single line
    ret = yggRecvRealloc(FileInput, &line, &line_size);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      ret = yggSend(FileOutput, line, line_size);
      if (ret < 0) {
  	printf("ascii_io(C): ERROR SENDING LINE\n");
  	error_code = -1;
  	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of file input (C)\n");
    }
  }
  if (line) free(line);

  // Read rows from ASCII table until end of file is reached.
  // As each row is received, it is then sent to the output ASCII table
  printf("ascii_io(C): Receiving/sending ASCII table.\n");
  char name[BSIZE];
  size_t name_siz = BSIZE;
  long number;
  double value;
  complex_double comp;
  ret = 0;
  while (ret >= 0) {
    name_siz = BSIZE; // Reset to size of the buffer

    // Receive a single row with values stored in scalars declared locally
    ret = yggRecv(TableInput, &name, &name_siz, &number, &value, &comp);
		      
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %.5s, %ld, %3.1f, %g%+gj\n",
  	     name, number, value, creal(comp), cimag(comp));
      ret = yggSend(TableOutput, name, name_siz, number, value, comp);
      if (ret < 0) {
  	printf("ascii_io(C): ERROR SENDING ROW\n");
  	error_code = -1;
  	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of table input (C)\n");
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
  complex_double *comp_arr = NULL;
  ret = 0;
  while (ret >= 0) {
    ret = yggRecvRealloc(ArrayInput, &nrows, &name_arr, &number_arr, &value_arr, &comp_arr);
    if (ret >= 0) {
      printf("Array: (%lu rows)\n", nrows);
      // Print each line in the array
      int i;
      for (i = 0; i < nrows; i++)
	printf("%.5s, %ld, %3.1f, %3.1lf%+3.1lfj\n", &name_arr[5*i], number_arr[i],
	       value_arr[i], creal(comp_arr[i]), cimag(comp_arr[i]));
      // Send the columns in the array to output. Formatting is handled on the
      // output driver side.
      ret = yggSend(ArrayOutput, nrows, name_arr, number_arr, value_arr, comp_arr);
      if (ret < 0) {
	printf("ascii_io(C): ERROR SENDING ARRAY\n");
	error_code = -1;
	break;
      }
    } else {
      printf("End of array input (C)\n");
    }
  }
    
  // Free dynamically allocated columns
  if (name_arr) free(name_arr);
  if (number_arr) free(number_arr);
  if (value_arr) free(value_arr);
  if (comp_arr) free(comp_arr);
  
  return error_code;
}
