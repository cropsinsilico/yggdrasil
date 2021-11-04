module hellofunc
contains
  subroutine my_print(msg)
    implicit none
    character(len=*), intent(in) :: msg
    write(*, '("myPrint: ",A)') trim(msg)
  end subroutine my_print

end module hellofunc
