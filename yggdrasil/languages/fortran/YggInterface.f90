MODULE fygg
  USE ISO_C_BINDING
  IMPLICIT none

  PUBLIC :: yggarg, yggcomm

  INCLUDE "YggInterface_cdef.f90"

  TYPE :: yggarg
     CLASS(*), ALLOCATABLE :: item
  END TYPE yggarg

  TYPE :: yggcomm
     TYPE(C_PTR) :: comm
  END TYPE yggcomm

CONTAINS
  FUNCTION ygg_output(name) RESULT(channel)
    IMPLICIT NONE
    CHARACTER(LEN=*), INTENT(IN) :: name
    CHARACTER(LEN=LEN_TRIM(name)+1) :: c_name
    TYPE(yggcomm) :: channel
    c_name = TRIM(name)//C_NULL_CHAR
    channel%comm = ygg_output_c(c_name)
  END FUNCTION ygg_output
  
  FUNCTION ygg_input(name) RESULT(channel)
    IMPLICIT NONE
    CHARACTER(LEN=*), INTENT(IN) :: name
    CHARACTER(LEN=LEN_TRIM(name)+1) :: c_name
    TYPE(yggcomm) :: channel
    c_name = TRIM(name)//C_NULL_CHAR
    channel%comm = ygg_input_c(c_name)
  END FUNCTION ygg_input
  
  FUNCTION ygg_send(ygg_q, data, data_len) RESULT (flag)
    IMPLICIT NONE
    TYPE(yggcomm), INTENT(IN) :: ygg_q
    TYPE(C_PTR) :: c_ygg_q
    CHARACTER(LEN=*), INTENT(IN) :: data
    CHARACTER(LEN=LEN(data)+1) :: c_data
    ! CHARACTER(LEN=LEN(data)+1) :: c_data
    ! CHARACTER(LEN=*), DIMENSION(1), TARGET :: data
    ! TYPE(C_PTR) :: c_data
    INTEGER, INTENT(IN) :: data_len
    INTEGER(KIND=C_INT) :: c_data_len
    INTEGER :: flag
    INTEGER(KIND=C_INT) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//C_NULL_CHAR
    ! c_data = C_LOC(data(1))
    c_data_len = data_len
    c_flag = ygg_send_c(c_ygg_q, c_data, c_data_len)
    flag = c_flag
  END FUNCTION ygg_send
  
  ! This might need to be a subroutine
  FUNCTION ygg_recv(ygg_q, data, data_len) RESULT (flag)
    IMPLICIT NONE
    TYPE(yggcomm) :: ygg_q
    TYPE(C_PTR) :: c_ygg_q
    CHARACTER(LEN=*) :: data
    CHARACTER(LEN=LEN(data)+1) :: c_data
    ! CHARACTER(LEN=*), DIMENSION(1), TARGET :: data
    ! TYPE(C_PTR) :: c_data
    INTEGER, INTENT(IN) :: data_len
    INTEGER(KIND=C_INT) :: c_data_len
    INTEGER :: flag
    INTEGER(KIND=C_INT) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = data//C_NULL_CHAR
    ! c_data = C_LOC(data(1))
    c_data_len = data_len
    c_flag = ygg_recv_c(c_ygg_q, c_data, c_data_len)
    data = c_data
    flag = c_flag
  END FUNCTION ygg_recv
  
  ! FUNCTION yggSend(ygg_q, args) RESULT (flag) BIND (C, name="
  
END MODULE fygg
