subroutine yggassign_yggchar2character(in, out)
  type(yggchar_r), intent(in) :: in
  character(len=:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(character(len=in_size) :: out)
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_yggchar2character
! subroutine yggassign_character2yggchar(in, out)
! end subroutine yggassign_character2yggchar

! UINT
! subroutine yggassign_unsigned_1d_to_array(in, out)
!   type(unsigned_1d), intent(in) :: in
!   unsigned, dimension(:), allocatable :: out
!   integer :: i, in_size
!   in_size = size(in%x)
!   if (allocated(out)) then
!      deallocate(out)
!   end if
!   allocate(out(in_size))
!   do i = 1, in_size
!      out(i:i) = in%x(i)
!   end do
! end subroutine yggassign_unsigned_1d_to_array
! subroutine yggassign_unsigned_1d_from_array(in, out)
!   unsigned, dimension(:), target, intent(in) :: in
!   type(unsigned_1d) :: out
!   out%x => in
! end subroutine yggassign_unsigned_1d_from_array
subroutine yggassign_unsigned2_1d_to_array(in, out)
  type(unsigned2_1d), intent(in) :: in
  integer(kind=2), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_unsigned2_1d_to_array
subroutine yggassign_unsigned2_1d_from_array(in, out)
  integer(kind=2), dimension(:), target, intent(in) :: in
  type(unsigned2_1d) :: out
  out%x => in
end subroutine yggassign_unsigned2_1d_from_array
subroutine yggassign_unsigned4_1d_to_array(in, out)
  type(unsigned4_1d), intent(in) :: in
  integer(kind=4), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_unsigned4_1d_to_array
subroutine yggassign_unsigned4_1d_from_array(in, out)
  integer(kind=4), dimension(:), target, intent(in) :: in
  type(unsigned4_1d) :: out
  out%x => in
end subroutine yggassign_unsigned4_1d_from_array
subroutine yggassign_unsigned8_1d_to_array(in, out)
  type(unsigned8_1d), intent(in) :: in
  integer(kind=8), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_unsigned8_1d_to_array
subroutine yggassign_unsigned8_1d_from_array(in, out)
  integer(kind=8), dimension(:), target, intent(in) :: in
  type(unsigned8_1d) :: out
  out%x => in
end subroutine yggassign_unsigned8_1d_from_array
! INT
subroutine yggassign_integer_1d_to_array(in, out)
  type(integer_1d), intent(in) :: in
  integer, dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_integer_1d_to_array
subroutine yggassign_integer_1d_from_array(in, out)
  integer, dimension(:), target, intent(in) :: in
  type(integer_1d) :: out
  out%x => in
end subroutine yggassign_integer_1d_from_array
subroutine yggassign_integer2_1d_to_array(in, out)
  type(integer2_1d), intent(in) :: in
  integer(kind=2), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_integer2_1d_to_array
subroutine yggassign_integer2_1d_from_array(in, out)
  integer(kind=2), dimension(:), target, intent(in) :: in
  type(integer2_1d) :: out
  out%x => in
end subroutine yggassign_integer2_1d_from_array
subroutine yggassign_integer4_1d_to_array(in, out)
  type(integer4_1d), intent(in) :: in
  integer(kind=4), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_integer4_1d_to_array
subroutine yggassign_integer4_1d_from_array(in, out)
  integer(kind=4), dimension(:), target, intent(in) :: in
  type(integer4_1d) :: out
  out%x => in
end subroutine yggassign_integer4_1d_from_array
subroutine yggassign_integer8_1d_to_array(in, out)
  type(integer8_1d), intent(in) :: in
  integer(kind=8), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_integer8_1d_to_array
subroutine yggassign_integer8_1d_from_array(in, out)
  integer(kind=8), dimension(:), target, intent(in) :: in
  type(integer8_1d) :: out
  out%x => in
end subroutine yggassign_integer8_1d_from_array
! REAL
subroutine yggassign_real_1d_to_array(in, out)
  type(real_1d), intent(in) :: in
  real, dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_real_1d_to_array
subroutine yggassign_real_1d_from_array(in, out)
  real, dimension(:), target, intent(in) :: in
  type(real_1d) :: out
  out%x => in
end subroutine yggassign_real_1d_from_array
subroutine yggassign_real4_1d_to_array(in, out)
  type(real4_1d), intent(in) :: in
  real(kind=4), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_real4_1d_to_array
subroutine yggassign_real4_1d_from_array(in, out)
  real(kind=4), dimension(:), target, intent(in) :: in
  type(real4_1d) :: out
  out%x => in
end subroutine yggassign_real4_1d_from_array
subroutine yggassign_real8_1d_to_array(in, out)
  type(real8_1d), intent(in) :: in
  real(kind=8), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_real8_1d_to_array
subroutine yggassign_real8_1d_from_array(in, out)
  real(kind=8), dimension(:), target, intent(in) :: in
  type(real8_1d) :: out
  out%x => in
end subroutine yggassign_real8_1d_from_array
subroutine yggassign_real16_1d_to_array(in, out)
  type(real16_1d), intent(in) :: in
  real(kind=16), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_real16_1d_to_array
subroutine yggassign_real16_1d_from_array(in, out)
  real(kind=16), dimension(:), target, intent(in) :: in
  type(real16_1d) :: out
  out%x => in
end subroutine yggassign_real16_1d_from_array
! COMPLEX
subroutine yggassign_complex_1d_to_array(in, out)
  type(complex_1d), intent(in) :: in
  complex, dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_complex_1d_to_array
subroutine yggassign_complex_1d_from_array(in, out)
  complex, dimension(:), target, intent(in) :: in
  type(complex_1d) :: out
  out%x => in
end subroutine yggassign_complex_1d_from_array
subroutine yggassign_complex4_1d_to_array(in, out)
  type(complex4_1d), intent(in) :: in
  complex(kind=4), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_complex4_1d_to_array
subroutine yggassign_complex4_1d_from_array(in, out)
  complex(kind=4), dimension(:), target, intent(in) :: in
  type(complex4_1d) :: out
  out%x => in
end subroutine yggassign_complex4_1d_from_array
subroutine yggassign_complex8_1d_to_array(in, out)
  type(complex8_1d), intent(in) :: in
  complex(kind=8), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_complex8_1d_to_array
subroutine yggassign_complex8_1d_from_array(in, out)
  complex(kind=8), dimension(:), target, intent(in) :: in
  type(complex8_1d) :: out
  out%x => in
end subroutine yggassign_complex8_1d_from_array
subroutine yggassign_complex16_1d_to_array(in, out)
  type(complex16_1d), intent(in) :: in
  complex(kind=16), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_complex16_1d_to_array
subroutine yggassign_complex16_1d_from_array(in, out)
  complex(kind=16), dimension(:), target, intent(in) :: in
  type(complex16_1d) :: out
  out%x => in
end subroutine yggassign_complex16_1d_from_array
! LOGICAL
subroutine yggassign_logical_1d_to_array(in, out)
  type(logical_1d), intent(in) :: in
  logical, dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_logical_1d_to_array
subroutine yggassign_logical_1d_from_array(in, out)
  logical, dimension(:), target, intent(in) :: in
  type(logical_1d) :: out
  out%x => in
end subroutine yggassign_logical_1d_from_array
subroutine yggassign_logical1_1d_to_array(in, out)
  type(logical1_1d), intent(in) :: in
  logical(kind=1), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_logical1_1d_to_array
subroutine yggassign_logical1_1d_from_array(in, out)
  logical(kind=1), dimension(:), target, intent(in) :: in
  type(logical1_1d) :: out
  out%x => in
end subroutine yggassign_logical1_1d_from_array
subroutine yggassign_logical2_1d_to_array(in, out)
  type(logical2_1d), intent(in) :: in
  logical(kind=2), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_logical2_1d_to_array
subroutine yggassign_logical2_1d_from_array(in, out)
  logical(kind=2), dimension(:), target, intent(in) :: in
  type(logical2_1d) :: out
  out%x => in
end subroutine yggassign_logical2_1d_from_array
subroutine yggassign_logical4_1d_to_array(in, out)
  type(logical4_1d), intent(in) :: in
  logical(kind=4), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_logical4_1d_to_array
subroutine yggassign_logical4_1d_from_array(in, out)
  logical(kind=4), dimension(:), target, intent(in) :: in
  type(logical4_1d) :: out
  out%x => in
end subroutine yggassign_logical4_1d_from_array
subroutine yggassign_logical8_1d_to_array(in, out)
  type(logical8_1d), intent(in) :: in
  logical(kind=8), dimension(:), allocatable :: out
  integer :: i, in_size
  in_size = size(in%x)
  if (allocated(out)) then
     deallocate(out)
  end if
  allocate(out(in_size))
  do i = 1, in_size
     out(i:i) = in%x(i)
  end do
end subroutine yggassign_logical8_1d_to_array
subroutine yggassign_logical8_1d_from_array(in, out)
  logical(kind=8), dimension(:), target, intent(in) :: in
  type(logical8_1d) :: out
  out%x => in
end subroutine yggassign_logical8_1d_from_array

! TODO: ND
