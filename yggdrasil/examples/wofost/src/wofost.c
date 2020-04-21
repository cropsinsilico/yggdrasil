#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggInput_t in_channel = yggGenericInput("input");
  yggOutput_t out_channel = yggGenericOutput("output");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  generic_t obj = init_generic();
  double* amaxtb_x = NULL;
  double* amaxtb_y = NULL;
  char** keys = NULL;
  size_t nkeys, i;
  double co2;
  generic_t amaxtb;
  size_t n_amaxtb;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = yggRecv(in_channel, &obj);
    if (flag < 0) {
      printf("C Model: No more input.\n");
      break;
    }

    // Print received message
    printf("C Model:\n");
    display_generic(obj);

    // Print keys
    nkeys = generic_map_get_keys(obj, &keys);
    printf("C Model: keys = ");
    for (i = 0; i < nkeys; i++) {
      printf("%s ", keys[i]);
    }
    printf("\n");

    // Get double precision floating point element
    co2 = generic_map_get_double(obj, "CO2");
    printf("C Model: CO2 = %lf\n", co2);

    // Get array element
    amaxtb = generic_map_get_array(obj, "AMAXTB");
    n_amaxtb = generic_array_get_1darray_double(amaxtb, 0, &amaxtb_x);
    generic_array_get_1darray_double(amaxtb, 1, &amaxtb_y);
    printf("C Model: AMAXTB = \n");
    for (i = 0; i < n_amaxtb; i++) {
      printf("\t%lf\t%lf\n", amaxtb_x[i], amaxtb_y[i]);
    }

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = yggSend(out_channel, obj);
    if (flag < 0) {
      printf("C Model: Error sending output.\n");
      break;
    }

    // Free dynamically allocated variables for this loop
    free_generic(&amaxtb);

  }

  // Free dynamically allocated obj structure
  free_generic(&obj);
  free(amaxtb_x);
  free(amaxtb_y);
  free(keys);
  
  return 0;
}

