#include "CisInterface.hpp"
#include <string>
#include <iostream>
using namespace std;


void grow_canopy(double growth_rate, double *layout,
		 int npatch, double **x1, double **x2, double **x3) {
  int i, j;
  for (i = 0; i < npatch; i++) {
    for (j = 0; j < 3; j++) {
      x1[j][i] = growth_rate * layout[j] * x1[j][i];
      x2[j][i] = growth_rate * layout[j] * x2[j][i];
      x3[j][i] = growth_rate * layout[j] * x3[j][i];
    }
  }

}

		
int main(int argc, char *argv[]) {

  int i, j, return_code = 0;
  CisInput in_layout("plant_layout");
  CisAsciiArrayInput in_struct("init_canopy_structure");
  CisInput in_growth("growth_rate");
  char struct_format[200] = "%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\n";
  CisAsciiArrayOutput out_struct("canopy_structure", struct_format);

  // Malloc arrays for use
  double *layout = (double*)malloc(3*sizeof(double));
  double **x1 = (double**)malloc(3*sizeof(double*));
  double **x2 = (double**)malloc(3*sizeof(double*));
  double **x3 = (double**)malloc(3*sizeof(double*));
  for (i = 0; i < 3; i++) {
    x1[i] = NULL;
    x2[i] = NULL;
    x3[i] = NULL;
  }

  // Receive layout and initial structure
  int ret = 0, npatch = 0;
  ret = in_layout.recv(3, layout, layout + 1, layout + 2);
  if (ret < 0) {
    printf("canopy: Error receiving layout.\n");
    free(layout);
    free(x1);
    free(x2);
    free(x3);
    return -1;
  }
  printf("canopy: layout = %f, %f, %f\n",
	 layout[0], layout[1], layout[2]);
  npatch = in_struct.recv(9, &x1[0], &x1[1], &x1[2],
			  &x2[0], &x2[1], &x2[2],
			  &x3[0], &x3[1], &x3[2]);
  if (npatch < 0) {
    printf("canopy: Error receiving structure.\n");
    free(layout);
    free(x1);
    free(x2);
    free(x3);
    return -1;
  }
  printf("canopy: %d patches in initial structure:\n\t\t%f\t%f\t%f\n\t\t%f\t%f\t%f\n\t\t%f\t%f\t%f...\n",
	 npatch, x1[0][0], x1[1][0], x1[2][0],
	 x2[0][0], x2[1][0], x2[2][0],
	 x3[0][0], x3[1][0], x3[2][0]);
    
  // Loop over growth rates calculating new structure
  double growth_rate;
  while (1) {
    ret = in_growth.recv(1, &growth_rate);
    if (ret < 0) {
      printf("canopy: No more input.\n");
      break;
    }
    grow_canopy(growth_rate, layout, npatch, x1, x2, x3);
    printf("canopy: growth rate = %f --> \t%f\t%f\t%f\n\t\t\t\t\t%f\t%f\t%f\n\t\t\t\t\t%f\t%f\t%f...\n",
	   growth_rate, x1[0][0], x1[1][0], x1[2][0],
	   x2[0][0], x2[1][0], x2[2][0],
	   x3[0][0], x3[1][0], x3[2][0]);
    ret = out_struct.send(9, npatch,
			  x1[0], x1[1], x1[2],
			  x2[0], x2[1], x2[2],
			  x3[0], x3[1], x3[2]);
    if (ret < 0) {
      printf("canopy: Error sending structure output.\n");
      return_code = -1;
      break;
    }
  }
  
  for (i = 0; i < 3; i++) {
    if (x1[i] != NULL) free(x1[i]);
    if (x2[i] != NULL) free(x2[i]);
    if (x3[i] != NULL) free(x3[i]);
  }
  free(layout);
  free(x1);
  free(x2);
  free(x3);
  return return_code;
}
