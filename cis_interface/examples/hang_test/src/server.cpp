#include <czmq.h>

int main() {
  int ret = 0;
  char address1[100] = "tcp://127.0.0.1:34410";
  char address2[100] = "tcp://127.0.0.1:49154";
  char test_msg[100] = "Hello world";
  int test_siz = strlen(test_msg) + 1;
  zsock_t *s1 = zsock_new(ZMQ_PAIR);
  zsock_t *s2 = zsock_new(ZMQ_PAIR);
  zsock_set_linger(s1, 100);
  zsock_set_linger(s2, 100);
  sleep(5); // Sleep to ensure client bound to address
  zsock_connect(s1, "%s", address1);
  zsock_connect(s2, "%s", address2);
  zframe_t *f = zframe_new(test_msg, test_siz);
  // sleep(15); // Sleep to test delay
  ret = zframe_send(&f, s1, ZFRAME_REUSE);
  printf("Sent %d bytes to client 1: %s\n", test_siz, test_msg);
  // sleep(15); // Sleep to test delay
  ret = zframe_send(&f, s2, 0);
  printf("Sent %d bytes to client 2: %s\n", test_siz, test_msg);
  zframe_destroy(&f);
  zsock_destroy(&s1);
  zsock_destroy(&s2);
  return ret;
}
