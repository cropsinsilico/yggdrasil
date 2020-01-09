#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "YggInterface.h"


double calc_light_intensity(double ambient_light, 
			    double x1, double y1, double z1,
			    double x2, double y2, double z2,
			    double x3, double y3, double z3) {
  double a = sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2));
  double b = sqrt(pow(x3 - x2, 2) + pow(y3 - y2, 2));
  double c = sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2));
  double s = (a + b + c)/2.0;
  double A = sqrt(s*(s - a)*(s - b)*(s - c));
  return ambient_light * A * (10.0 - (z1 + z2 + z3)/3.0)/10.0;
}


int main(int argc,char *argv[]) {
  int i, ret, return_code = 0;

  yggInput_t AmbInput = yggAsciiTableInput("ambient_light");
  yggInput_t StructInput = yggAsciiArrayInput("canopy_structure");
  yggOutput_t LightOutput = yggAsciiTableOutput("light_intensity", "%lf\n");

  // Receive Ambient light
  double ambient_light;
  ret = yggRecv(AmbInput, &ambient_light);
  if (ret < 0) {
    printf("light: Error receiving ambient light.\n");
    return -1;
  }
  printf("light: ambient light = %f\n", ambient_light);

  // Malloc arrays for use
  double **x1 = (double**)malloc(3*sizeof(double*));
  double **x2 = (double**)malloc(3*sizeof(double*));
  double **x3 = (double**)malloc(3*sizeof(double*));
  for (i = 0; i < 3; i++) {
    x1[i] = NULL;
    x2[i] = NULL;
    x3[i] = NULL;
  }

  // Loop over canopy structures
  size_t npatch = 0;
  double light_intensity = 0.0;
  ret = 0;
  while (1) {
    ret = yggRecvRealloc(StructInput, &npatch,
			 &x1[0], &x1[1], &x1[2],
			 &x2[0], &x2[1], &x2[2],
			 &x3[0], &x3[1], &x3[2]);
    if (ret < 0) {
      printf("light: End of input.\n");
      break;
    }
    for (i = 0; i < (int)npatch; i++) {
      light_intensity = calc_light_intensity(ambient_light,
					     x1[0][i], x1[1][i], x1[2][i],
					     x2[0][i], x2[1][i], x2[2][i],
					     x3[0][i], x3[1][i], x3[2][i]);
      printf("light: structure = \t%f\t%f\t%f --> light_intensity = %f\n\t\t\t%f\t%f\t%f\n\t\t\t%f\t%f\t%f\n",
	     x1[0][i], x1[1][i], x1[2][i], light_intensity,
	     x2[0][i], x2[1][i], x2[2][i],
	     x3[0][i], x3[1][i], x3[2][i]);
      ret = yggSend(LightOutput, light_intensity);
      if (ret < 0) {
	printf("light: Error sending light intensity output.\n");
	return_code = -1;
	break;
      }
    }
    if (ret < 0)
      break;
  }

  for (i = 0; i < 3; i++) {
    if (x1[i] != NULL) free(x1[i]);
    if (x2[i] != NULL) free(x2[i]);
    if (x3[i] != NULL) free(x3[i]);
  }
  free(x1);
  free(x2);
  free(x3);
  return return_code;
}
