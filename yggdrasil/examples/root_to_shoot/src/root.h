#include "tools.h"

/*!
  @brief Calculation of root mass following time step.
  @param[in] r_r double Relative root growth rate.
  @param[in] dt double Duration of time step.
  @param[in] R_t double Current root mass.
  @returns double Root mass after time step.
 */
double calc_root_mass(double r_r, double dt, double R_t) {
  usleep(1e5);  // To simulate a longer calculation
  return R_t + (R_t * r_r * dt);
};
