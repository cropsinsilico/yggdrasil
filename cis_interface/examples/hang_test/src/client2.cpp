#include <czmq.h>

int main() {
  char address[100] = "tcp://127.0.0.1:49154";
  zsock_t *s = zsock_new(ZMQ_PAIR);
  zsock_set_linger(s, 100);
  zsock_bind(s, "%s", address);
  sleep(10);
  zframe_t *f = zframe_recv(s);
  printf("Client2: Received %d bytes: %s\n", zframe_size(f), zframe_data(f));
  zframe_destroy(&f);
  zsock_destroy(&s);
  return 0;
}
