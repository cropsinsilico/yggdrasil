#include <stdio.h>
#include <stdlib.h>
// Include interface methods
#include "PsiInterface.hpp"


int main(int argc,char *argv[]){
  const uint BSIZE = 8192; // the max
  int ret;

  // Input & output to an ASCII file line by line
  PsiAsciiFileInput FileInput("inputCPP_file");
  PsiAsciiFileOutput FileOutput("outputCPP_file");
  // Input & output from a table row by row
  PsiAsciiTableInput TableInput("inputCPP_table");
  PsiAsciiTableOutput TableOutput("outputCPP_table", "%5s\t%ld\t%3.1f\n");
  // Input & output from a table as an array
  PsiAsciiTableInput ArrayInput("inputCPP_array");
  PsiAsciiTableOutput ArrayOutput("outputCPP_array", "%5s\t%ld\t%3.1f\n");

  // Read lines from ASCII text file until end of file is reached.
  // As each line is received, it is then sent to the output ASCII file.
  printf("ascii_io(CPP): Receiving/sending ASCII file.\n");
  char line[LINE_SIZE_MAX];
  ret = 0;
  while (ret >= 0) {
    // Receive a single line
    ret = FileInput.recv_line(line, LINE_SIZE_MAX);
    if (ret >= 0) {
      // If the receive was succesful, send the line to output
      printf("File: %s", line);
      ret = FileOutput.send_line(line);
      if (ret != 0) {
	printf("ascii_io(CPP): ERROR SENDING LINE\n");
	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of file input (CPP)\n");
      FileOutput.send_eof();
    }
  }

  // Read rows from ASCII table until end of file is reached.
  // As each row is received, it is then sent to the output ASCII table
  printf("ascii_io(CPP): Receiving/sending ASCII table.\n");
  char name[BSIZE];
  int number;
  float value;
  ret = 0;
  while (ret >= 0) {
    // Receive a single row with values stored in scalars declared locally
    ret = TableInput.recv_row(3, &name, &number, &value);
    if (ret >= 0) {
      // If the receive was succesful, send the values to output. Formatting
      // is taken care of on the output driver side.
      printf("Table: %s, %d, %f\n", name, number, value);
      ret = TableOutput.send_row(3, name, number, value);
      if (ret != 0) {
	printf("ascii_io(CPP): ERROR SENDING ROW\n");
	break;
      }
    } else {
      // If the receive was not succesful, send the end-of-file message to
      // close the output file.
      printf("End of table input (CPP)\n");
      TableOutput.send_eof();
    }
  }

  // Read entire array from ASCII table into columns that are dynamically
  // allocated. The returned values tells us the number of elements in the
  // columns.
  printf("Receiving/sending ASCII table as array.\n");
  char *name_arr;
  long *number_arr;
  double *value_arr;
  ret = ArrayInput.recv_array(3, &name_arr, &number_arr, &value_arr);
  if (ret < 0) {
    printf("ascii_io(CPP): ERROR RECVING ARRAY\n");
    free(name_arr);
    free(number_arr);
    free(value_arr);
    return -1;
  }
  printf("Array: (%d rows)\n", ret);
  // Print each line in the array
  for (int i = 0; i < ret; i++)
    printf("%5s, %d, %f\n", &name_arr[5*i], number_arr[i], value_arr[i]);
  // Send the columns in the array to output. Formatting is handled on the
  // output driver side.
  ret = ArrayOutput.send_array(3, ret, name_arr, number_arr, value_arr);
  if (ret != 0)
    printf("ascii_io(CPP): ERROR SENDING ARRAY\n");
  
  // Free dynamically allocated columns
  free(name_arr);
  free(number_arr);
  free(value_arr);

  return 0;
}
