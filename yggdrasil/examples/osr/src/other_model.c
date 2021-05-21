#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.h"


int timestep_calc(double t, const char* t_units, generic_t state) {
  int ret = 0;
  if (ret >= 0) {
    ret = generic_map_set_double(state, "carbonAllocation2Roots", 10.0, "g");
  }
  if (ret >= 0) {
    ret = generic_map_set_double(state, "saturatedConductivity", 10.0, "cm/day");
  }
  return ret;
}


int main(int argc, char *argv[]) {

  double t_step = atof(argv[1]);
  char* t_units = argv[2];
  int exit_code = 0;
  printf("Hello from C other_model: timestep %f %s\n", t_step, t_units);
  double t_start = 0.0;
  double t_end = 1.0;
  size_t nkeys, ikey;
  char** keys = NULL;
  if (strcmp(t_units, "hr") == 0) {
    t_end = 24.0 * t_end;
  }
  int ret;
  generic_t state_send = init_generic_map();
  generic_t state_recv = init_generic_map();
  ret = timestep_calc(t_start, t_units, state_send);
  if (ret < 0) {
    printf("other_model(C): Error in initial timestep calculation.");
    return -1;
  }

  // Set up connections matching yaml
  // Timestep synchronization connection will be 'timesync'
  comm_t* timesync = yggTimesync("timesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  comm_t* out = yggOutputType("output", out_dtype);

  // Initialize state and synchronize with other models
  double t = t_start;
  ret = rpcCall(timesync, t, state_send, &state_recv);
  if (ret < 0) {
    printf("other_model(C): Initial sync failed.\n");
    return -1;
  }
  nkeys = generic_map_get_keys(state_recv, &keys);
  printf("other_model(C): t = %5.1f %-3s", t, t_units);
  for (ikey = 0; ikey < nkeys; ikey++) {
    printf(", %s = %+ 5.2f", keys[ikey],
	   generic_map_get_double(state_recv, keys[ikey]));
  }
  printf("\n");

  // Send initial state to output
  generic_t msg = copy_generic(state_recv);
  ret = generic_map_set_double(msg, "time", t, t_units);
  if (ret < 0) {
    printf("other_model(C): Failed to set time in initial output map.\n");
    return -1;
  }
  ret = yggSend(out, msg);
  if (ret < 0) {
    printf("other_model(C): Failed to send initial output for t=%f.\n", t);
    return -1;
  }
  destroy_generic(&msg);

  // Iterate until end
  while (t < t_end) {

    // Perform calculations to update the state
    t = t + t_step;
    ret = timestep_calc(t, t_units, state_send);
    if (ret < 0) {
      printf("other_model(C): Error in timestep calculation for t = %f.\n", t);
      return -1;
    }

    // Synchronize the state
    ret = rpcCall(timesync, t, state_send, &state_recv);
    if (ret < 0) {
      printf("other_model(C): sync for t=%f failed.\n", t);
      return -1;
    }
    nkeys = generic_map_get_keys(state_recv, &keys);
    printf("other_model(C): t = %5.1f %-3s", t, t_units);
    for (ikey = 0; ikey < nkeys; ikey++) {
      printf(", %s = %+ 5.2f", keys[ikey],
	     generic_map_get_double(state_recv, keys[ikey]));
    }
    printf("\n");

    // Send output
    generic_t msg = copy_generic(state_recv);
    ret = generic_map_set_double(msg, "time", t, t_units);
    if (ret < 0) {
      printf("other_model(C): Failed to set time in output map.\n");
      return -1;
    }
    ret = yggSend(out, msg);
    if (ret < 0) {
      printf("other_model(C): Failed to send output for t=%f.\n", t);
      return -1;
    }
    destroy_generic(&msg);
  }

  printf("Goodbye from C other_model\n");
  destroy_generic(&state_send);
  destroy_generic(&state_recv);
  return 0;
    
}
