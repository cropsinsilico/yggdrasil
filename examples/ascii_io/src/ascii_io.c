// Author Venkatraman Srinivasan
#include <stdio.h>
#include <stdlib.h>

#include "PsiInterface.h"

PsiAsciiFileInput get_input_file(int type) {
  const char *name;
  if (type == 0)
    name = "Input/inputC_file.txt";
  else
    name = "inputC_file";
  PsiAsciiFileInput out = psi_ascii_file_input(name, type);
  printf("%s\n", name);
  return out;
}

PsiAsciiFileOutput get_output_file(int type) {
  const char *name;
  if (type == 0)
    name = "Output/outputC_file.txt";
  else
    name = "outputC_file";
  PsiAsciiFileOutput out = psi_ascii_file_output(name, type);
  return out;
}

PsiAsciiTableInput get_input_table(int type) {
  const char *name;
  if (type == 0)
    name = "Input/inputC_table.txt";
  else
    name = "inputC_table";
  PsiAsciiTableInput out = psi_ascii_table_input(name, type);
  return out;
}

PsiAsciiTableOutput get_output_table(int type) {
  const char *name;
  if (type == 0)
    name = "Output/outputC_table.txt";
  else
    name = "outputC_table";
  PsiAsciiTableOutput out = psi_ascii_table_output(name, type, "%5s\t%ld\t%f\n");
  return out;
}

PsiAsciiTableInput get_input_array(int type) {
  const char *name;
  if (type == 0)
    name = "Input/inputC_array.txt";
  else
    name = "inputC_array";
  PsiAsciiTableInput out = psi_ascii_table_input(name, type);
  return out;
}

PsiAsciiTableOutput get_output_array(int type) {
  const char *name;
  if (type == 0)
    name = "Output/outputC_array.txt";
  else
    name = "outputC_array";
  PsiAsciiTableOutput out = psi_ascii_table_output(name, type, "%5s\t%ld\t%f\n");
  return out;
}

int main(int argc,char *argv[]){
  char line[LINE_SIZE_MAX];
  const uint BSIZE = 8192; // the max
  char name[BSIZE];
  int number;
  double value;
  int ret;
  char *name_arr;
  long *number_arr;
  double *value_arr;

  PsiAsciiFileInput FileInput = get_input_file(1);
  PsiAsciiFileOutput FileOutput = get_output_file(1);
  PsiAsciiTableInput TableInput = get_input_table(1);
  PsiAsciiTableOutput TableOutput = get_output_table(1);
  PsiAsciiTableInput ArrayInput = get_input_array(1);
  PsiAsciiTableOutput ArrayOutput = get_output_array(1);

  // Do generic text file
  ret = 0;
  while (ret >= 0) {
    ret = recv_line(FileInput, line, LINE_SIZE_MAX);
    if (ret >= 0) {
      printf("File: %s", line);
      send_line(FileOutput, line);
    } else {
      printf("End of file input (C)\n");
      af_send_eof(FileOutput);
    }
  }

  // Do table
  ret = 0;
  while (ret >= 0) {
    ret = recv_row(TableInput, &name, &number, &value);
    if (ret >= 0) {
      printf("Table: %s, %d, %f\n", name, number, value);
      send_row(TableOutput, name, number, value);
    } else {
      printf("End of table input (C)\n");
      at_send_eof(TableOutput);
    }
  }

  // Do array
  ret = recv_array(ArrayInput, &name_arr, &number_arr, &value_arr);
  printf("Array: (%d rows)\n", ret);
  for (int i = 0; i < ret; i++) {
    /* printf("%d, %f\n", number_arr[i], value_arr[i]); */
    printf("%5s, %d, %f\n", &name_arr[5*i], number_arr[i], value_arr[i]);
  }
  send_array(ArrayOutput, ret, name_arr, number_arr, value_arr);
  free(name_arr);
  free(number_arr);
  free(value_arr);

  cleanup_pafi(&FileInput);
  cleanup_pafo(&FileOutput);
  cleanup_pati(&TableInput);
  cleanup_pato(&TableOutput);
  cleanup_pati(&ArrayInput);
  cleanup_pato(&ArrayOutput);
  
  return 0;
}
