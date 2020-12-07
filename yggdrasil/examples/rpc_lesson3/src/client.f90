function model_function(in_buf, out_buf) result(ret)
  character(len=*), intent(in) :: in_buf
  type(yggchar_r) :: out_buf
  logical :: ret
  type(yggcomm) :: rpc
  WITH_GLOBAL_SCOPE(rpc = ygg_rpc_client("server_client"))
  write(*, '("client(F): ",A," (length = ",I3,")")') in_buf, len(in_buf)
  ret = ygg_rpc_call_realloc(rpc, yggarg(in_buf), yggarg(out_buf))
  if (.not.ret) then
     write(*, '("client(F): RPC CALL ERROR")')
     stop 1
  end if
end function model_function
