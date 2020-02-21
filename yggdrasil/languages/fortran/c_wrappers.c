#include "c_wrappers.h"

void ygg_c_free(void *x) {
  if (x != NULL) {
    free(x);
  }
}

void ygg_log_info_f(const char* fmt) {
  ygglog_info(fmt);
}
void ygg_log_debug_f(const char* fmt) {
  ygglog_debug(fmt);
  /* yggInfo(fmt); */
}
void ygg_log_error_f(const char* fmt) {
  ygglog_error(fmt);
}

void* ygg_output_f(const char *name) {
  return (void*)yggOutput(name);
}

void* ygg_input_f(const char *name) {
  return (void*)yggInput(name);
}

void* yggAsciiFileOutput_f(const char *name) {
  return (void*)yggAsciiFileOutput(name);
}

void* yggAsciiFileInput_f(const char *name) {
  return (void*)yggAsciiFileInput(name);
}

void* yggAsciiTableOutput_f(const char *name, const char *format_str) {
  return (void*)yggAsciiTableOutput(name, format_str);
}

void* yggAsciiTableInput_f(const char *name) {
  return (void*)yggAsciiTableInput(name);
}

void* yggAsciiArrayOutput_f(const char *name, const char *format_str) {
  return (void*)yggAsciiArrayOutput(name, format_str);
}

void* yggAsciiArrayInput_f(const char *name) {
  return (void*)yggAsciiArrayInput(name);
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
  return vcommSend((const comm_t*)yggQ, (size_t)nargs, ap);
}

int ygg_recv_var_f(void *yggQ, int nargs, void *args) {
  if (args == NULL) {
    ygglog_error("ygg_recv_var_f: args pointer is NULL.");
    return -1;
  }
  va_list_t ap = init_va_ptrs(nargs, (void**)args);
  ap.for_fortran = 1;
  return vcommRecv((comm_t*)yggQ, 0, (size_t)nargs, ap);
}

int ygg_recv_var_realloc_f(void *yggQ, int nargs, void *args) {
  if (args == NULL) {
    ygglog_error("ygg_recv_var_realloc_f: args pointer is NULL.");
    return -1;
  }
  va_list_t ap = init_va_ptrs(nargs, (void**)args);
  ap.for_fortran = 1;
  return vcommRecv((comm_t*)yggQ, 1, (size_t)nargs, ap);
}
