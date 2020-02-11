MODULE ygg
  USE ISO_C_BINDING
  IMPLICIT none

  TYPE :: yggarg
     CLASS(*), ALLOCATABLE :: item
  END TYPE yggarg

  TYPE :: yggcomm
     TYPE(C_PTR) :: comm
  END TYPE yggcomm

CONTAINS
  FUNCTION ygg_output_type(name, datatype) RESULT(channel) BIND(C, name="yggOutputType")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
    TYPE(C_PTR), INTENT(in) :: datatype
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_output_type
  
  FUNCTION ygg_input_type(name, datatype) RESULT(channel) BIND(C, name="yggInputType")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
    TYPE(C_PTR), INTENT(in) :: datatype
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_input_type
  
  FUNCTION ygg_output_fmt(name, fmt_string) RESULT(channel) BIND(C, name="yggOutputFmt")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: fmt_string(*)
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_output_fmt
  
  FUNCTION ygg_input_fmt(name, fmt_string) RESULT(channel) BIND(C, name="yggInputFmt")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: fmt_string(*)
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_input_fmt
  
  FUNCTION ygg_output_(name) RESULT(channel) BIND(C, name="yggOutput")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), dimension(*), INTENT(IN) :: name
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_output_
  FUNCTION ygg_output(name) RESULT(channel)
    CHARACTER(LEN=*) :: name
    CHARACTER(LEN=LEN_TRIM(name)+1) :: c_name
    TYPE(yggcomm) :: channel
    TYPE(C_PTR) :: c_channel
    c_name = TRIM(name)
    c_channel = ygg_output_(c_name)
    channel%comm = c_channel
  END FUNCTION ygg_output
  
  FUNCTION ygg_input_(name) RESULT(channel) BIND(C, name="yggInput")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
    CHARACTER(KIND=C_CHAR), dimension(*), INTENT(IN) :: name
    TYPE(C_PTR) :: channel
  END FUNCTION ygg_input_
  FUNCTION ygg_input(name) RESULT(channel)
    CHARACTER(LEN=*) :: name
    CHARACTER(LEN=LEN_TRIM(name)+1) :: c_name
    TYPE(yggcomm) :: channel
    TYPE(C_PTR) :: c_channel
    c_name = TRIM(name)
    c_channel = ygg_input_(c_name)
    channel%comm = c_channel
  END FUNCTION ygg_input
  
  FUNCTION ygg_send_(ygg_q, data, len) RESULT (flag) BIND(C, name="ygg_send")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR, C_INT
    TYPE(C_PTR), VALUE, INTENT(IN) :: ygg_q
    TYPE(C_PTR), VALUE, INTENT(IN) :: data
    INTEGER(KIND=C_INT), VALUE, INTENT(IN) :: len
    INTEGER(KIND=C_INT) :: flag
  END FUNCTION ygg_send_
  FUNCTION ygg_send(ygg_q, data, len) RESULT (flag)
    TYPE(yggcomm) :: ygg_q
    TYPE(C_PTR) :: c_ygg_q
    CHARACTER(LEN=*), DIMENSION(1), TARGET :: data
    TYPE(C_PTR) :: c_data
    INTEGER :: len
    INTEGER(KIND=C_INT) :: c_len
    INTEGER :: flag
    INTEGER(KIND=C_INT) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = C_LOC(data(1))
    c_len = len
    c_flag = ygg_send_(c_ygg_q, c_data, c_len)
    flag = c_flag
  END FUNCTION ygg_send
  
  ! This might need to be a subroutine
  FUNCTION ygg_recv_(ygg_q, data, len) RESULT (flag) BIND(C, name="ygg_recv")
    USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR, C_INT
    TYPE(C_PTR), VALUE, INTENT(IN) :: ygg_q
    TYPE(C_PTR), VALUE, INTENT(IN) :: data
    INTEGER(KIND=C_INT), VALUE, INTENT(IN) :: len
    INTEGER(KIND=C_INT) :: flag
  END FUNCTION ygg_recv_
  FUNCTION ygg_recv(ygg_q, data, len) RESULT (flag)
    TYPE(yggcomm) :: ygg_q
    TYPE(C_PTR) :: c_ygg_q
    CHARACTER(LEN=*), DIMENSION(1), TARGET :: data
    TYPE(C_PTR) :: c_data
    INTEGER :: len
    INTEGER(KIND=C_INT) :: c_len
    INTEGER :: flag
    INTEGER(KIND=C_INT) :: c_flag
    c_ygg_q = ygg_q%comm
    c_data = C_LOC(data(1))
    c_len = len
    c_flag = ygg_recv_(c_ygg_q, c_data, c_len)
    flag = c_flag
  END FUNCTION ygg_recv
  
  ! FUNCTION yggSend(ygg_q, args) RESULT (flag) BIND (C, name="
  
END MODULE ygg
