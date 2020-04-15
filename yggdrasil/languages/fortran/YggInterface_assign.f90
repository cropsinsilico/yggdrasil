subroutine yggassign_yggchar2character(in, out)
  type(yggchar_r), intent(in) :: in
  character(len=:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  allocate(character(len=in_size) :: out)
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_yggchar2character
! subroutine yggassign_character2yggchar(in, out)
! end subroutine yggassign_character2yggchar
