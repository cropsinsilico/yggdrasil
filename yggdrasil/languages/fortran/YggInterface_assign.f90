subroutine yggassign_yggchar2character(in, out)
  type(yggchar_r), intent(in) :: in
  character(len=:), allocatable :: out
  integer :: i
  print *, "yggassign_yggchar2character"
  print *, "len = ", size(in%x)
  allocate(character(len=size(in%x)) :: out)
  print *, "allocated"
  do i = 1, size(in%x)
     out(i:i) = in%x(i)
  end do
  print *, "yggassign_yggchar2character returns"
end subroutine yggassign_yggchar2character
! subroutine yggassign_character2yggchar(in, out)
! end subroutine yggassign_character2yggchar
