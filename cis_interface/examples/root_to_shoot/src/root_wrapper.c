#include <stdio.h>
#include <stdlib.h>
// Include C interface
#include "CisInterface.h"
// Include C header containing model calculation
#include "root.h"


int main(int argc, char *argv[]) {
  int i, ret;
  double r_r, dt, R_t, R_tp1;

  // Create input/output channels
  cisInput_t RootGrowthRate = cisInput("root_growth_rate");
  cisInput_t InitRootMass = cisInput("init_root_mass");
  cisInput_t TimeStep = cisInput("root_time_step");
  cisOutput_t NextRootMass = cisOutputFmt("next_root_mass", "%lf\n");

  // Receive root growth rate
  ret = cisRecv(RootGrowthRate, &r_r);
  if (ret < 0) {
    printf("root: Error receiving root growth rate.\n");
    return -1;
  }
  printf("root: Received root growth rate: %lf\n", r_r);

  // Receive initial root mass
  ret = cisRecv(InitRootMass, &R_t);
  if (ret < 0) {
    printf("root: Error receiving initial root mass.\n");
    return -1;
  }
  printf("root: Received initial root mass: %lf\n", R_t);

  // Send initial root mass
  ret = cisSend(NextRootMass, R_t);
  if (ret < 0) {
    printf("root: Error sending initial root mass.\n");
    return -1;
  }

  // Keep advancing until there arn't any new input times
  i = 0;
  while (1) {

    // Receive the time step
    ret = cisRecv(TimeStep, &dt);
    if (ret < 0) {
      printf("root: No more time steps.\n");
      break;
    }
    printf("root: Received next time step: %lf\n", dt);

    // Calculate root mass
    R_tp1 = calc_root_mass(r_r, dt, R_t);
    printf("root: Calculated next root mass: %lf\n", R_tp1);

    // Output root mass
    ret = cisSend(NextRootMass, R_tp1);
    if (ret < 0) {
      printf("root: Error sending root mass for timestep %d.\n", i+1);
      return -1;
    }

    // Advance root mass to next timestep
    R_t = R_tp1;
    i++;

  }

  return 0;

}
