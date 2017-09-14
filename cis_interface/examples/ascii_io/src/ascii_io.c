#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "PsiInterface.h"


int main(int argc,char *argv[]){
  const uint BSIZE = 8192; // the max
  int ret;

  // Input & output to an ASCII file line by line
  psiAsciiFileInput_t FileInput = psiAsciiFileInput("inputC_file", 1);
  psiAsciiFileOutput_t FileOutput = psiAsciiFileOutput("outputC_file", 1);
  // Input & output from a table row by row
  psiAsciiTableInput_t TableInput = psiAsciiTableInput("inputC_table", 1);
  psiAsciiTableOutput_t TableOutput = psiAsciiTableOutput("outputC_table",
							  "%5s\t%ld\t%3.1f\n", 1);
  // Input & output from a table as an array
  psiAsciiTableInput_t ArrayInput = psiAsciiTableInput("inputC_array", 1);
  psiAsciiTableOutput_t ArrayOutput = psiAsciiTableOutput("outputC_array",
							  "%5s\t%ld\t%3.1f\n", 1);

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("ascii_io(C): Receiving/sending ASCII file.\n");
  char line[LINE_SIZE_MAX];
  ret = 0;
  while (ret >= 0) {
    // Receive a single line
    ret = af_recv_line(FileInput, line, LINE_SIZE_MAX);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      ret = af_send_line(FileOutput, line);
      if (ret != 0) {
	printf("ascii_io(C): ERROR SENDING LINE\n");
	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of file input (C)\n");
      af_send_eof(FileOutput);
    }
  }

  // Read rows from ASCII table until end of file is reached.
  // As each row is received, it is then sent to the output ASCII table
  printf("ascii_io(C): Receiving/sending ASCII table.\n");
  char name[BSIZE];
  long number;
  double value;
  ret = 0;
  while (ret >= 0) {
    // Receive a single row with values stored in scalars declared locally
    ret = at_recv_row(TableInput, &name, &number, &value);
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %s, %ld, %3.1f\n", name, number, value);
      ret = at_send_row(TableOutput, name, number, value);
      if (ret != 0) {
	printf("ascii_io(C): ERROR SENDING ROW\n");
	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of table input (C)\n");
      at_send_eof(TableOutput);
    }
  }

  // Read entire array from ASCII table into columns that are dynamically
  // allocated. The returned values tells us the number of elements in the
  // columns.
  printf("Receiving/sending ASCII table as array.\n");
  char *name_arr;
  long *number_arr;
  double *value_arr;
  ret = at_recv_array(ArrayInput, &name_arr, &number_arr, &value_arr);
  if (ret < 0) {
    printf("ascii_io(C): ERROR RECVING ARRAY\n");
    free(name_arr);
    free(number_arr);
    free(value_arr);
    return -1;
  }
  printf("Array: (%d rows)\n", ret);
  // Print each line in the array
  int i;
  for (i = 0; i < ret; i++)
    printf("%5s, %ld, %f\n", &name_arr[5*i], number_arr[i], value_arr[i]);
  // Send the columns in the array to output. Formatting is handled on the
  // output driver side.
  ret = at_send_array(ArrayOutput, ret, name_arr, number_arr, value_arr);
  if (ret != 0)
    printf("ascii_io(C): ERROR SENDING ARRAY\n");
  
  // Free dynamically allocated columns
  free(name_arr);
  free(number_arr);
  free(value_arr);

  // Clean up to deallocate things
  cleanup_pafi(&FileInput);
  cleanup_pafo(&FileOutput);
  cleanup_pati(&TableInput);
  cleanup_pato(&TableOutput);
  cleanup_pati(&ArrayInput);
  cleanup_pato(&ArrayOutput);
  
  return 0;
}
