#include "MPIComm.hpp"

using namespace communicator;

int MPIComm::mpi_comm_source_id() {
    if (is_send(direction)) return 0;
    if (x->handle == NULL) {
        ygglog_error("mpi_comm_source_id(%s): Queue handle is NULL.", x->name);
        return -1;
    }
    mpi_registry_t* reg = (mpi_registry_t*)(x->handle);
    MPI_Status status;
    int address = MPI_ANY_SOURCE;
    if (MPI_Probe(address, reg->tag, reg->comm, &status) != MPI_SUCCESS) {
        ygglog_error("mpi_comm_source_id(%s): Error in probe for tag = %d",
                     x->name, reg->tag);
        return -1;
    }
    if (status.MPI_ERROR) {
        ygglog_error("mpi_comm_source_id(%s): Error in status for tag = %d: %d",
                     x->name, reg->tag, status.MPI_ERROR);
        return -1;
    }
    if (status.cancelled) {
        ygglog_error("mpi_comm_source_id(%s): Request canceled for tag = %d",
                     x->name, reg->tag);
        return -1;
    }
    if (status.count > 0) {
        for (size_t i = 0; i < reg->nproc; i++) {
            if (reg->procs[i] == status.MPI_SOURCE) {
                return status.MPI_SOURCE;
            }
        }
    }
    return 0;
}