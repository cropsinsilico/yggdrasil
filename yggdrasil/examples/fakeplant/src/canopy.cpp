#include "YggInterface.hpp"
#include <string>
#include <iostream>
using namespace std;


void grow_canopy(double tstep, double *growth_rate, double *layout,
		 int npatch, double **x1, double **x2, double **x3) {
  int i, j;
  for (i = 0; i < npatch; i++) {
    for (j = 0; j < 3; j++) {
      x1[j][i] = (1.0 + growth_rate[i] * tstep * layout[j]) * x1[j][i];
      x2[j][i] = (1.0 + growth_rate[i] * tstep * layout[j]) * x2[j][i];
      x3[j][i] = (1.0 + growth_rate[i] * tstep * layout[j]) * x3[j][i];
    }
  }

}

		
int main(int argc, char *argv[]) {

  int i, return_code = 0;
  YggInput in_layout("plant_layout");
  YggAsciiArrayInput in_struct("init_canopy_structure");
  YggInput in_time("time");
  YggInput in_growth("growth_rate");
  char struct_format[200] = "%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\n";
  YggAsciiArrayOutput out_struct("canopy_structure", struct_format);
  double time_prev, time_curr;
  time_curr = 0.0;

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
  ret = in_struct.recvRealloc(10, &npatch, &x1[0], &x1[1], &x1[2],
			      &x2[0], &x2[1], &x2[2],
			      &x3[0], &x3[1], &x3[2]);
  if (ret < 0) {
    printf("canopy: Error receiving structure\n");
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

  // Send canopy to output and get growth rate for it
  double *growth_rate = (double*)malloc(npatch*sizeof(double));
  ret = out_struct.send(10, npatch,
			x1[0], x1[1], x1[2],
			x2[0], x2[1], x2[2],
			x3[0], x3[1], x3[2]);
  if (ret < 0) {
    printf("canopy: Error sending initial structure to output.\n");
    return_code = -1;
  } else {
    for (i = 0; i < npatch; i++) {
      ret = in_growth.recv(1, growth_rate + i);
      if (ret < 0) {
	printf("canopy: Failed to get initial growth rate for patch %d.\n", i);
	return_code = -1;
	break;
      }
    }
  }

  // Loop over growth rates calculating new structure
  while (ret >= 0) {
    // Check for next time
    time_prev = time_curr;
    ret = in_time.recv(1, &time_curr);
    if (ret < 0) {
      printf("canopy: No more input.\n");
      break;
    }
    // Update structure and send to out
    grow_canopy(time_curr - time_prev, growth_rate, layout, npatch, x1, x2, x3);
    for (i = 0; i < npatch; i++) {
      printf("canopy: patch %d: growth rate = %f --> \t%f\t%f\t%f\n\t\t\t\t\t\t%f\t%f\t%f\n\t\t\t\t\t\t%f\t%f\t%f...\n",
	     i, growth_rate[i], x1[0][i], x1[1][i], x1[2][i],
	     x2[0][i], x2[1][i], x2[2][i],
	     x3[0][i], x3[1][i], x3[2][i]);
    }
    ret = out_struct.send(10, npatch,
			  x1[0], x1[1], x1[2],
			  x2[0], x2[1], x2[2],
			  x3[0], x3[1], x3[2]);
    if (ret < 0) {
      printf("canopy: Error sending structure output.\n");
      return_code = -1;
      break;
    }
    // Receive growth rate for each patch
    for (i = 0; i < npatch; i++) {
      ret = in_growth.recv(1, growth_rate + i);
      if (ret < 0) {
	printf("canopy: Failed to get growth rate for patch %d during time frame %f to %f\n",
	       i, time_prev, time_curr);
	return_code = -1;
	break;
      }
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
