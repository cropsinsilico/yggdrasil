#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "CisInterface.h"

#define BSIZE 8192 // the max


int main(int argc,char *argv[]){
  int ret;
  int error_code = 0;

  // Input & output to an ASCII file line by line
  cisAsciiFileInput_t FileInput = cisAsciiFileInput("inputC_file");
  cisAsciiFileOutput_t FileOutput = cisAsciiFileOutput("outputC_file");
  // Input & output from a table row by row
  cisAsciiTableInput_t TableInput = cisAsciiTableInput("inputC_table");
  cisAsciiTableOutput_t TableOutput = cisAsciiTableOutput("outputC_table",
							  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");
  // Input & output from a table as an array
  cisAsciiArrayInput_t ArrayInput = cisAsciiArrayInput("inputC_array");
  cisAsciiArrayOutput_t ArrayOutput = cisAsciiArrayOutput("outputC_array",
							  "%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n");

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("ascii_io(C): Receiving/sending ASCII file.\n");
  char *line = (char*)malloc(LINE_SIZE_MAX);
  ret = 0;
  while (ret >= 0) {
    // Receive a single line
    ret = cisRecv(FileInput, &line);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      ret = cisSend(FileOutput, line);
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
  long number;
  double value;
  double comp_real, comp_imag;
  ret = 0;
  while (ret >= 0) {
    // Receive a single row with values stored in scalars declared locally
    ret = cisRecv(TableInput, &name, &number, &value, &comp_real, &comp_imag);
		      
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %.5s, %ld, %3.1f, %g%+gj\n",
	     name, number, value, comp_real, comp_imag);
      ret = cisSend(TableOutput, name, number, value, comp_real, comp_imag);
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
  char *name_arr = NULL;
  long *number_arr = NULL;
  double *value_arr = NULL;
  double *comp_real_arr = NULL;
  double *comp_imag_arr = NULL;
  ret = 0;
  while (ret >= 0) {
    ret = cisRecv(ArrayInput, &name_arr, &number_arr, &value_arr,
		  &comp_real_arr, &comp_imag_arr);
    if (ret >= 0) {
      printf("Array: (%d rows)\n", ret);
      // Print each line in the array
      int i;
      for (i = 0; i < ret; i++)
	printf("%.5s, %ld, %3.1f, %3.1lf%+3.1lfj\n", &name_arr[5*i], number_arr[i],
	       value_arr[i], comp_real_arr[i], comp_imag_arr[i]);
      // Send the columns in the array to output. Formatting is handled on the
      // output driver side.
      ret = cisSend(ArrayOutput, ret, name_arr, number_arr, value_arr,
		    comp_real_arr, comp_imag_arr);
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
  if (comp_real_arr) free(comp_real_arr);
  if (comp_imag_arr) free(comp_imag_arr);
  
  return error_code;
}
