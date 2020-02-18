#include "c_wrappers.h"

void* ygg_output_f(const char *name) {
  return (void*)yggOutput(name);
}

void* ygg_input_f(const char *name) {
  return (void*)yggInput(name);
}

int ygg_send_f(const void *yggQ, const char *data, const size_t len) {
  return ygg_send((const comm_t*)yggQ, data, len);
}

int ygg_recv_f(void *yggQ, char *data, const size_t len) {
  return ygg_recv((comm_t*)yggQ, data, len);
}

int ygg_send_var_f(const void *yggQ, int nargs, void *args) {
  if (args == NULL) {
    ygglog_error("ygg_send_var_f: args pointer is NULL.");
    return -1;
  }
  va_list_t ap = init_va_ptrs(nargs, (void**)args);
  return vcommSend((const comm_t*)yggQ, nargs, ap);
}

int ygg_recv_var_f(void *yggQ, int nargs, void *args) {
  if (args == NULL) {
    ygglog_error("ygg_recv_var_f: args pointer is NULL.");
    return -1;
  }
  va_list_t ap = init_va_ptrs(nargs, (void**)args);
  ap.for_fortran = 1;
  return vcommRecv((comm_t*)yggQ, 0, nargs, ap);
}

int ygg_recv_var_realloc_f(void *yggQ, int nargs, void *args) {
  if (args == NULL) {
    ygglog_error("ygg_recv_var_realloc_f: args pointer is NULL.");
    return -1;
  }
  va_list_t ap = init_va_ptrs(nargs, (void**)args);
  ap.for_fortran = 1;
  return vcommRecv((comm_t*)yggQ, 1, nargs, ap);
}
