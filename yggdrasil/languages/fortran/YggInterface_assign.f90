subroutine yggassign_yggchar2character(in, out)
  type(yggchar_r), intent(in) :: in
  character(len=:), allocatable :: out
  integer :: i
  allocate(character(len=size(in%x)) :: out)
  do i = 1, size(in%x)
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_yggchar2character
! subroutine yggassign_character2yggchar(in, out)
! end subroutine yggassign_character2yggchar
