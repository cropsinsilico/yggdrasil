#include <stdio.h>
#include <stdlib.h>
// Include C header containing model calculation
#include "root.h"
#define LINESZ 1024


int main(int argc, char *argv[]) {
  int i, ret;
  double r_r, dt, R_t, R_tp1;
  char buff[LINESZ];

  // Create input/output files
  if (argc!=5) {
    printf("3 input files and 1 output file must be specified.\n");
    return -1;
  }
  FILE *RootGrowthRate = fopen(argv[1], "r");
  if (RootGrowthRate == NULL) {
    printf("root: Failed to open file: '%s'\n", argv[1]);
    return -1;
  }
  FILE *InitRootMass = fopen(argv[2], "r");
  if (InitRootMass == NULL) {
    printf("root: Failed to open file: '%s'\n", argv[2]);
    fclose(RootGrowthRate);
    return -1;
  }
  FILE *TimeStep = fopen(argv[3], "r");
  if (TimeStep == NULL) {
    printf("root: Failed to open file: '%s'\n", argv[3]);
    fclose(RootGrowthRate);
    fclose(InitRootMass);
    return -1;
  }
  FILE *NextRootMass = fopen(argv[4], "w");
  if (NextRootMass == NULL) {
    printf("root: Failed to open file: '%s'\n", argv[4]);
    fclose(RootGrowthRate);
    fclose(InitRootMass);
    fclose(TimeStep);
    return -1;
  }

  // Read root growth rate
  ret = -1;
  while (fgets (buff, LINESZ, RootGrowthRate)) {
    if (buff[0] == '#') continue;
    ret = sscanf(buff, "%lf", &r_r);
    break;
  }
  fclose(RootGrowthRate);
  if (ret != 1) {
    printf("root: Error reading root growth rate.\n");
    fclose(InitRootMass);
    fclose(TimeStep);
    fclose(NextRootMass);
    return -1;
  }
  printf("root: Read root growth rate: %lf\n", r_r);

  // Read initial root mass
  ret = -1;
  while (fgets (buff, LINESZ, InitRootMass)) {
    if (buff[0] == '#') continue;
    ret = sscanf(buff, "%lf", &R_t);
    break;
  }
  fclose(InitRootMass);
  if (ret != 1) {
    printf("root: Error reading initial root mass.\n");
    fclose(TimeStep);
    fclose(NextRootMass);
    return -1;
  }
  printf("root: Read initial root mass: %lf\n", R_t);

  // Write initial root mass
  if (fprintf(NextRootMass, "# root_mass\n# %%lf\n%lf\n", R_t) < 0) {
    printf("root: Error writing initial root mass.\n");
    fclose(TimeStep);
    fclose(NextRootMass);
    return -1;
  }

  // Keep advancing until there arn't any new input times
  i = 0;
  while (1) {

    // Read the time step
    if (fgets(buff, LINESZ, TimeStep) == NULL) {
      printf("root: No more time steps.\n");
      break;
    }
    if (buff[0] == '#') continue;
    if (sscanf(buff, "%lf", &dt) != 1) {
      printf("root: Error parsing timestep.\n");
      fclose(TimeStep);
      fclose(NextRootMass);
      return -1;
    }
    printf("root: Read next time step: %lf\n", dt);

    // Calculate root mass
    R_tp1 = calc_root_mass(r_r, dt, R_t);
    printf("root: Calculated next root mass: %lf\n", R_tp1);

    // Output root mass
    if (fprintf(NextRootMass, "%lf\n", R_tp1) < 0) {
      printf("root: Error writing root mass for timestep %d.\n", i+1);
      fclose(TimeStep);
      fclose(NextRootMass);
      return -1;
    }

    // Advance root mass to next timestep
    R_t = R_tp1;
    i++;
    // break;  // Only for timing of a single loop

  }

  fclose(TimeStep);
  fclose(NextRootMass);
  return 0;

}
