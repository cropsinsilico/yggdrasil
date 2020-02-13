#include "c_wrappers.h"

void* ygg_output_f(const char *name) {
  return (void*)yggOutput(name);
}

void* ygg_input_f(const char *name) {
  return (void*)yggInput(name);
}

int ygg_send_f(const void *yggQ, const char *data, const size_t len) {
  return ygg_send((const yggOutput_t)yggQ, data, len);
}

int ygg_recv_f(void *yggQ, char *data, const size_t len) {
  return ygg_recv((yggOutput_t)yggQ, data, len);
}
