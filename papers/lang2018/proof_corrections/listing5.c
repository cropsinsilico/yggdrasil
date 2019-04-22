#include <stdio.h>
#include <stdlib.h>
// Include C interface
#include "YggInterface.h"
// Include C header containing model calculation
#include "root.h"


int main(int argc, char *argv[]) {
  int i, ret;
  double r_r, dt, R_t, R_tp1;

  // Create input/output channels
  yggInput_t RootGrowthRate = yggInput("root_growth_rate");
  yggInput_t InitRootMass = yggInput("init_root_mass");
  yggInput_t TimeStep = yggInput("root_time_step");
  yggOutput_t NextRootMass = yggOutputFmt("next_root_mass", "%lf\n");

  // Receive root growth rate
  ret = yggRecv(RootGrowthRate, &r_r);
  if (ret < 0) {
    printf("root: Error receiving root growth rate.\n");
    return -1;
  }
  printf("root: Received root growth rate: %lf\n", r_r);

  // Receive initial root mass
  ret = yggRecv(InitRootMass, &R_t);
  if (ret < 0) {
    printf("root: Error receiving initial root mass.\n");
    return -1;
  }
  printf("root: Received initial root mass: %lf\n", R_t);

  // Send initial root mass
  ret = yggSend(NextRootMass, R_t);
  if (ret < 0) {
    printf("root: Error sending initial root mass.\n");
    return -1;
  }

  // Keep advancing until there arn't any new input times
  i = 0;
  while (1) {

    // Receive the time step
    ret = yggRecv(TimeStep, &dt);
    if (ret < 0) {
      printf("root: No more time steps.\n");
      break;
    }
    printf("root: Received next time step: %lf\n", dt);

    // Calculate root mass
    R_tp1 = calc_root_mass(r_r, dt, R_t);
    printf("root: Calculated next root mass: %lf\n", R_tp1);

    // Output root mass
    ret = yggSend(NextRootMass, R_tp1);
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
