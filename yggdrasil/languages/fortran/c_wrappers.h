#ifndef YGG_FC_WRAPPERS_H_
#define YGG_FC_WRAPPERS_H_

#include "../C/YggInterface.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

void* ygg_output_f(const char *name);
void* ygg_input_f(const char *name);
int ygg_send_f(const void *yggQ, const char *data, const size_t len);
int ygg_recv_f(void *yggQ, char *data, const size_t len);
int ygg_send_var_f(const void *yggQ, int nargs, void *args);
int ygg_recv_var_f(void *yggQ, int nargs, void *args);
int ygg_recv_var_realloc_f(void *yggQ, int nargs, void *args);

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif


#endif /*YGG_FC_WRAPPERS_H_*/
