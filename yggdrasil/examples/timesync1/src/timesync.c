#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.h"


int timestep_calc(double t, const char* t_units, generic_t state) {
  double x_period = 10.0; // Days
  double y_period = 5.0;  // Days
  double x, y;
  int ret = 0;
  if (strcmp(t_units, "day") == 0) {
    // No conversion necessary
  } else if (strcmp(t_units, "hr") == 0) {
    x_period = x_period * 24.0;
    y_period = y_period * 24.0;
  } else {
    printf("timestep_calc: Unsupported unit '%s'\n", t_units);
    ret = -1;
  }
  if (ret >= 0) {
    x = sin(2.0 * M_PI * t / x_period);
    y = cos(2.0 * M_PI * t / y_period);
    ret = generic_map_set_double(state, "x", x, "");
    ret = generic_map_set_double(state, "y", y, "");
  }
  return ret;
}


int main(int argc, char *argv[]) {

  double t_step = atof(argv[1]);
  char* t_units = argv[2];
  int exit_code = 0;
  printf("Hello from C timesync: timestep %f %s\n", t_step, t_units);
  double t_start = 0.0;
  double t_end = 5.0;
  if (strcmp(t_units, "hr") == 0) {
    t_end = 24.0 * t_end;
  }
  int ret;
  generic_t state = init_generic_map();
  ret = timestep_calc(t_start, t_units, state);
  if (ret < 0) {
    printf("timesync(C): Error in initial timestep calculation.");
    return -1;
  }

  // Set up connections matching yaml
  // Timestep synchronization connection will be 'timesync'
  comm_t* timesync = yggTimesync("timesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  comm_t* out = yggOutputType("output", out_dtype);

  // Initialize state and synchronize with other models
  double t = t_start;
  ret = rpcCall(timesync, t, state, &state);
  if (ret < 0) {
    printf("timesync(C): Initial sync failed.\n");
    return -1;
  }
  printf("timesync(C): t = %5.1f %-3s, x = %+ 5.2f, y = %+ 5.2f\n",
	 t, t_units, generic_map_get_double(state, "x"),
	 generic_map_get_double(state, "y"));

  // Send initial state to output
  generic_t msg = copy_generic(state);
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
    ret = timestep_calc(t, t_units, state);
    if (ret < 0) {
      printf("timesync(C): Error in timestep calculation for t = %f.\n", t);
      return -1;
    }

    // Synchronize the state
    ret = rpcCall(timesync, t, state, &state);
    if (ret < 0) {
      printf("timesync(C): sync for t=%f failed.\n", t);
      return -1;
    }
    printf("timesync(C): t = %5.1f %-3s, x = %+ 5.2f, y = %+ 5.2f\n",
	   t, t_units, generic_map_get_double(state, "x"),
	   generic_map_get_double(state, "y"));

    // Send output
    msg = copy_generic(state);
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
  destroy_generic(&state);
  return 0;
    
}
