#pragma once

#include "CommBase.hpp"

#ifdef MPIINSTALLED
#include <mpi.h>
#endif /*MPIINSTALLED*/
#if defined(MPIINSTALLED) && defined(MPI_COMM_WORLD)
namespace communicator {

typedef struct mpi_registry_t {
    MPI_Comm comm; //!< MPI communicator.
    size_t nproc; //!< Number of processes in procs.
    size_t* procs; //!< IDs for partner processes.
    size_t tag; //!< Tag for next message.
} mpi_registry_t;

class MPIComm : public CommBase<mpi_registry_t,void> {
public:
    MPIComm();

    ~MPIComm();

    int recv(std::string &data) override;
    int send(const std::string &data) override;
    int send_nolimit(const std::string &data) override;
    int comm_nmsg() override;

    int mpi_comm_source_id();

};

#endif

} // communicator
