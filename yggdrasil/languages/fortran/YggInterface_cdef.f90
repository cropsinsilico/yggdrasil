  INTERFACE
     FUNCTION ygg_output_type_c(name, datatype) RESULT(channel) &
          BIND(C, name="yggOutputType")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
       TYPE(C_PTR), INTENT(in) :: datatype
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_output_type_c
  
     FUNCTION ygg_input_type_c(name, datatype) RESULT(channel) &
          BIND(C, name="yggInputType")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
       TYPE(C_PTR), INTENT(in) :: datatype
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_input_type_c
  
     FUNCTION ygg_output_fmt_c(name, fmt_string) RESULT(channel) &
          BIND(C, name="yggOutputFmt")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: fmt_string(*)
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_output_fmt_c
  
     FUNCTION ygg_input_fmt_c(name, fmt_string) RESULT(channel) &
          BIND(C, name="yggInputFmt")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: name(*)
       CHARACTER(KIND=C_CHAR), INTENT(IN) :: fmt_string(*)
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_input_fmt_c
  
     FUNCTION ygg_output_c(name) RESULT(channel) &
          BIND(C, name="ygg_output_f")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), dimension(*), INTENT(IN) :: name
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_output_c
  
     FUNCTION ygg_input_c(name) RESULT(channel) &
          BIND(C, name="ygg_input_f")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR
       IMPLICIT NONE
       CHARACTER(KIND=C_CHAR), dimension(*), INTENT(IN) :: name
       TYPE(C_PTR) :: channel
     END FUNCTION ygg_input_c
  
     FUNCTION ygg_send_c(ygg_q, data, data_len) RESULT (flag) &
          BIND(C, name="ygg_send_f")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR, &
            C_INT
       IMPLICIT NONE
       TYPE(C_PTR), VALUE, INTENT(IN) :: ygg_q
       CHARACTER(KIND=C_CHAR), DIMENSION(*), INTENT(IN) :: data
       ! TYPE(C_PTR), VALUE, INTENT(IN) :: data
       INTEGER(KIND=C_INT), VALUE, INTENT(IN) :: data_len
       INTEGER(KIND=C_INT) :: flag
     END FUNCTION ygg_send_c
  
     ! This might need to be a subroutine
     FUNCTION ygg_recv_c(ygg_q, data, data_len) RESULT (flag) &
          BIND(C, name="ygg_recv_f")
       USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_PTR, C_CHAR, &
            C_INT
       IMPLICIT NONE
       TYPE(C_PTR), VALUE, INTENT(IN) :: ygg_q
       ! TYPE(C_PTR), VALUE, INTENT(IN) :: data
       CHARACTER(KIND=C_CHAR), DIMENSION(*) :: data
       INTEGER(KIND=C_INT), VALUE, INTENT(IN) :: data_len
       INTEGER(KIND=C_INT) :: flag
     END FUNCTION ygg_recv_c
     
  END INTERFACE
