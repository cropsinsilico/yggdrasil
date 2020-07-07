subroutine copy_real4_nd(x_out, x_in)
  type(real4_nd), intent(in) :: x_in
  class(real4_nd), intent(inout) :: x_out
  if (associated(x_out%x)) deallocate(x_out%x)
  if (associated(x_out%shape)) deallocate(x_out%shape)
  print *, "copy", associated(x_in%x), associated(x_in%shape)
  allocate(x_out%x, source = x_in%x)
  allocate(x_out%shape, source = x_in%shape)
end subroutine copy_real4_nd
