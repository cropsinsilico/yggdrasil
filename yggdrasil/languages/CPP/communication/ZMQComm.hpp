#pragma once

#include "CommBase.hpp"
#ifdef ZMQINSTALLED
#include <zmq.hpp>
#else

#endif
#include <vector>
namespace communicator {

static unsigned _zmq_rand_seeded = 0;
static unsigned _last_port_set = 0;
static int _last_port = 49152;
/* static double _wait_send_t = 0;  // 0.0001; */
static char _reply_msg[100] = "YGG_REPLY";
static char _purge_msg[100] = "YGG_PURGE";
static int _zmq_sleeptime = 10000;
#ifdef _OPENMP
#pragma omp threadprivate(_reply_msg, _purge_msg, _zmq_sleeptime)
#endif

#ifdef ZMQINSTALLED

class ygg_sock_t : public zmq::socket_t {
#else
    class ygg_sock_t {
#endif
public:
    explicit ygg_sock_t(int type);

#ifdef ZMQINSTALLED

    static zmq::context_t &get_context();

    static void shutdown();

#else

#endif /*ZMQINSTALLED*/

    ~ygg_sock_t();

#ifdef _OPENMP
    uint32_t tag;
    int type;
private:
    static zmq::context_t ygg_s_process_ctx;
    static bool ctx_valid;
#endif
};

/*void ygg_zsock_destroy(zsock_t **self_p) {
    // Recreation of czmq zsock_destroy that is OMP aware
    if (*self_p) {
        auto *self = (ygg_zsock_t*)(*self_p);
        self->tag = 0xDeadBeef;
        zmq_close (self->handle);
        freen (self->endpoint);
        freen (self->cache);
        freen (self);
        *self_p = nullptr;
    }
};
#else
#define ygg_zsock_destroy zsock_destroy
#endif
*/

/*!
  @brief Struct to store info for reply.
*/
typedef struct zmq_reply_t {
    ~zmq_reply_t() {
        clear();
    }

    size_t nsockets() const {
        return sockets.size();
    }

    void clear() {
        for (auto it: sockets) {
            if (it != nullptr)
                delete it;
        }
        for (auto it: addresses) {
            if (it != nullptr)
                delete it;
        }
        sockets.clear();
        addresses.clear();
        n_msg = 0;
        n_rep = 0;
    }

    std::vector<ygg_sock_t *> sockets;
    std::vector<Address *> addresses;
    int n_msg = 0;
    int n_rep = 0;
} zmq_reply_t;

class ZMQComm : public CommBase<ygg_sock_t, zmq_reply_t> {
public:
    explicit ZMQComm(const std::string &name = "", Address *address = new Address(), Direction direction = NONE,
                     DataType *datatype = nullptr);
    ~ZMQComm();
    int send(const std::string &data) override;
    int send_nolimit(const std::string &data) override {
        return send(data);
    }
    int set_reply_recv(Address *adr);
    int recv(std::string &data) override;
    //void open() override;
    //void close() override;
    int comm_nmsg() override;
    static std::string check_reply_send(const std::string &data);
    int do_reply_recv(const int &isock, const char *msg);
    void init_reply();
    std::string set_reply_send();
    int find_reply_socket(Address *address = nullptr);
    int check_reply_recv(std::string &data, const size_t &len);
private:
    ygg_sock_t *sock;
    static ygg_sock_t *new_zsock(const int &type);
    static ygg_sock_t *create_zsock(const int &type);
    ygg_sock_t *recv_zframe();
    int do_reply_send();
    void init_zmq_reply();
    void destroy();
    bool create_new();
    bool connect_to_existing();
};

}
