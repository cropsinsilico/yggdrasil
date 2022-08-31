#ifndef YGGINTERFACEP_ZMQCOMM_HPP
#define YGGINTERFACEP_ZMQCOMM_HPP

#include "CommBase.hpp"

#ifdef ZMQINSTALLED
#include <zmq.h>
#include <vector>

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

// TODO clean up
typedef struct ygg_zsock_t {
    ~ygg_zsock_t() {
#ifdef _OPENMP
        // Recreation of czmq zsock_destroy that is OMP aware
        tag = 0xDeadBeef;
        zmq_close (handle);
        freen (endpoint);
        freen (cache);
#else
        zsock_destroy(this);
#endif

    }
    uint32_t tag;               //  Object tag for runtime detection
    void *handle;               //  The libzmq socket handle
    char *endpoint;             //  Last bound endpoint, if any
    char *cache;                //  Holds last zsock_brecv strings
    int type;                   //  Socket type
    size_t cache_size;          //  Current size of cache
    uint32_t routing_id;        //  Routing ID for server sockets
} ygg_zsock_t;

void ygg_zsock_destroy(zsock_t **self_p) {
    // Recreation of czmq zsock_destroy that is OMP aware
    /* assert(self_p); */
    if (*self_p) {
        auto *self = (ygg_zsock_t*)(*self_p);
        /* assert (zsock_is (*self_p)); */
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

/*!
  @brief Struct to store info for reply.
*/
typedef struct zmq_reply_t {
    ~zmq_reply_t() {
        for (auto it : sockets) {
            if (it != nullptr)
                ygg_zsock_destroy(&it);
        }
        for (auto it : addresses) {
            if (it != nullptr)
                delete it;
        }
        sockets.clear();
        addresses.clear();
    }
    size_t nsockets() const {
        return sockets.size();
    }
    std::vector<zsock_t*> sockets;
    std::vector<Address*> addresses;
    int n_msg = 0;
    int n_rep = 0;
} zmq_reply_t;

class ZMQComm : public CommBase<zsock_t,zmq_reply_t> {
public:
    explicit ZMQComm(const std::string &name = "", Address *address = new Address(), const Direction direction = NONE,
                     DataType* datatype = nullptr);
    ~ZMQComm();
    int send(const std::string &data) override;
    int send_nolimit(const std::string &data) override {
        return send(data);
    }
    int set_reply_recv(Address* adr);
    int recv(std::string &data) override;
    void open() override;
    void close() override;
    int comm_nmsg() override;
    static std::string check_reply_send(const std::string &data);
    int do_reply_recv(const int &isock, const char *msg);
    static void init();
    static void shutdown();
    static void* process_ctx() { return ygg_s_process_ctx;}
    void init_reply();
    std::string set_reply_send();
    int find_reply_socket(Address *address = nullptr);
    int new_zmq_address();
    int check_reply_recv(std::string &data, const size_t &len);
private:
    zsock_t *sock;
    static void *ygg_s_process_ctx;
    static zsock_t *new_zsock(const int &type);
    static zsock_t *create_zsock(const int &type);
    zframe_t* recv_zframe();
    int do_reply_send();
    void init_zmq_reply();
    void destroy();
};

#endif //YGGINTERFACEP_ZMQCOMM_HPP
