#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.h"


int timestep_calc(double t, const char* t_units, generic_t state,
		  const char* model) {
  double x_period = 10.0; // Days
  double y_period = 5.0;  // Days
  double z_period = 20.0; // Days
  double o_period = 2.5;  // Days
  int ret = 0;
  if (strcmp(t_units, "day") == 0) {
    // No conversion necessary
  } else if (strcmp(t_units, "hr") == 0) {
    x_period = x_period * 24.0;
    y_period = y_period * 24.0;
    z_period = z_period * 24.0;
    o_period = o_period * 24.0;
  } else {
    printf("timestep_calc: Unsupported unit '%s'\n", t_units);
    ret = -1;
  }
  if (ret >= 0) {
    if (strcmp(model, "A") == 0) {
      ret = generic_map_set_double(state, "x",
				   sin(2.0 * M_PI * t / x_period),
				   "");
      ret = generic_map_set_double(state, "y",
				   cos(2.0 * M_PI * t / y_period),
				   "");
      ret = generic_map_set_double(state, "z1",
				   -cos(2.0 * M_PI * t / z_period),
				   "");
      ret = generic_map_set_double(state, "z2",
				   -cos(2.0 * M_PI * t / z_period),
				   "");
      ret = generic_map_set_double(state, "a",
				   sin(2.0 * M_PI * t / o_period),
				   "");
    } else {
      ret = generic_map_set_double(state, "xvar",
				   sin(2.0 * M_PI * t / x_period) / 2.0,
				   "");
      ret = generic_map_set_double(state, "yvar",
				   cos(2.0 * M_PI * t / y_period),
				   "");
      ret = generic_map_set_double(state, "z",
				   -2.0 * cos(2.0 * M_PI * t / z_period),
				   "");
      ret = generic_map_set_double(state, "b",
				   cos(2.0 * M_PI * t / o_period),
				   "");
    }
  }
  return ret;
}


int main(int argc, char *argv[]) {

  double t_step = atof(argv[1]);
  char* t_units = argv[2];
  char* model = argv[3];
  int exit_code = 0;
  printf("Hello from C timesync: timestep %f %s\n", t_step, t_units);
  double t_start = 0.0;
  double t_end = 5.0;
  size_t nkeys, ikey;
  char** keys = NULL;
  if (strcmp(t_units, "hr") == 0) {
    t_end = 24.0 * t_end;
  }
  int ret;
  generic_t state_send = init_generic_map();
  generic_t state_recv = init_generic_map();
  ret = timestep_calc(t_start, t_units, state_send, model);
  if (ret < 0) {
    printf("timesync(C): Error in initial timestep calculation.");
    return -1;
  }

  // Set up connections matching yaml
  // Timestep synchronization connection will be 'statesync'
  comm_t* timesync = yggTimesync("statesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  comm_t* out = yggOutputType("output", out_dtype);

  // Initialize state and synchronize with other models
  double t = t_start;
  ret = rpcCall(timesync, t, state_send, &state_recv);
  if (ret < 0) {
    printf("timesync(C): Initial sync failed.\n");
    return -1;
  }
  printf("timesync(C): t = %5.1f %-3s", t, t_units);
  nkeys = generic_map_get_keys(state_recv, &keys);
  for (ikey = 0; ikey < nkeys; ikey++) {
    printf(", %s = %+ 5.2f", keys[ikey],
	   generic_map_get_double(state_recv, keys[ikey]));
  }
  printf("\n");

  // Send initial state to output
  generic_t msg = copy_generic(state_recv);
  ret = generic_map_set_double(msg, "time", t, t_units);
  if (ret < 0) {
    printf("timesync(C): Failed to set time in initial output map.\n");
    return -1;
  }
  ret = yggSend(out, msg);
  if (ret < 0) {
    printf("timesync(C): Failed to send initial output for t=%f.\n", t);
    return -1;
  }
  destroy_generic(&msg);

  // Iterate until end
  while (t < t_end) {

    // Perform calculations to update the state
    t = t + t_step;
    ret = timestep_calc(t, t_units, state_send, model);
    if (ret < 0) {
      printf("timesync(C): Error in timestep calculation for t = %f.\n", t);
      return -1;
    }

    // Synchronize the state
    ret = rpcCall(timesync, t, state_send, &state_recv);
    if (ret < 0) {
      printf("timesync(C): sync for t=%f failed.\n", t);
      return -1;
    }
    printf("timesync(C): t = %5.1f %-3s", t, t_units);
    nkeys = generic_map_get_keys(state_recv, &keys);
    for (ikey = 0; ikey < nkeys; ikey++) {
      printf(", %s = %+ 5.2f", keys[ikey],
	     generic_map_get_double(state_recv, keys[ikey]));
	}
    printf("\n");

    // Send output
    msg = copy_generic(state_recv);
    ret = generic_map_set_double(msg, "time", t, t_units);
    if (ret < 0) {
      printf("timesync(C): Failed to set time in output map.\n");
      return -1;
    }
    ret = yggSend(out, msg);
    if (ret < 0) {
      printf("timesync(C): Failed to send output for t=%f.\n", t);
      return -1;
    }
    destroy_generic(&msg);

  }

  printf("Goodbye from C timesync\n");
  destroy_generic(&state_send);
  destroy_generic(&state_recv);
  return 0;
    
}
