#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "PsiInterface.h"


int main(int argc,char *argv[]){
  const uint BSIZE = 8192; // the max
  int ret;

  // Input & output to an ASCII file line by line
  PsiAsciiFileInput FileInput = psi_ascii_file_input("inputC_file", 1);
  PsiAsciiFileOutput FileOutput = psi_ascii_file_output("outputC_file", 1);
  // Input & output from a table row by row
  PsiAsciiTableInput TableInput = psi_ascii_table_input("inputC_table", 1);
  PsiAsciiTableOutput TableOutput = psi_ascii_table_output("outputC_table", 1,
							   "%5s\t%ld\t%3.1f\n");
  // Input & output from a table as an array
  PsiAsciiTableInput ArrayInput = psi_ascii_table_input("inputC_array", 1);
  PsiAsciiTableOutput ArrayOutput = psi_ascii_table_output("outputC_array", 1,
							   "%5s\t%ld\t%3.1f\n");

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("Receiving/sending ASCII file.\n");
  char line[LINE_SIZE_MAX];
  ret = 0;
  while (ret >= 0) {
    // Receive a single line
    ret = recv_line(FileInput, line, LINE_SIZE_MAX);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      send_line(FileOutput, line);
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of file input (C)\n");
      af_send_eof(FileOutput);
    }
  }

  // Read rows from ASCII table until end of file is reached.
  // As each row is received, it is then sent to the output ASCII table
  printf("Receiving/sending ASCII table.\n");
  char name[BSIZE];
  int number;
  double value;
  ret = 0;
  while (ret >= 0) {
    // Receive a single row with values stored in scalars declared locally
    ret = recv_row(TableInput, &name, &number, &value);
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %s, %d, %f\n", name, number, value);
      send_row(TableOutput, name, number, value);
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
  ret = recv_array(ArrayInput, &name_arr, &number_arr, &value_arr);
  printf("Array: (%d rows)\n", ret);
  // Print each line in the array
  for (int i = 0; i < ret; i++)
    printf("%5s, %d, %f\n", &name_arr[5*i], number_arr[i], value_arr[i]);
  // Send the columns in the array to output. Formatting is handled on the
  // output driver side.
  send_array(ArrayOutput, ret, name_arr, number_arr, value_arr);
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
