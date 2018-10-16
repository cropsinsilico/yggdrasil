#include <stdio.h>
#include <stdlib.h>
#include "CisInterface.h"


double calc_root_mass(double r_r, double R_t) {
  return R_t + (R_t * r_r);
}


int main(int argc, char *argv[]) {
  int i, ret, nstep;
  double r_r, R_t, R_tp1;

  cisInput_t RootInput = cisInput("root_input");
  cisOutput_t NextRootMass = cisOutputFmt("next_root_mass", "%lf\n");

  // Receive number of timesteps, root growth rate, and initial root mass
  ret = cisRecv(RootInput, &nstep, &r_r, &R_t);
  if (ret < 0) {
    printf("root: Error receiving root input.\n");
    return -1;
  }
  printf("received nsteps = %d\n", nstep);

  // Send initial root mass
  ret = cisSend(NextRootMass, R_t);
  if (ret < 0) {
    printf("root: Error sending initial root mass.\n");
    return -1;
  }

  // Loop over timesteps, outputing root masses
  for (i = 0; i < nstep; i++) {

    R_tp1 = calc_root_mass(r_r, R_t);
    ret = cisSend(NextRootMass, R_tp1);
    if (ret < 0) {
      printf("root: Error sending root mass for timestep %d.\n", i+1);
      return -1;
    }

    R_t = R_tp1;

  }

  return 0;

}
