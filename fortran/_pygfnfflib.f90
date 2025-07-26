module gfnff
    use gfnff_interface
    implicit none

contains


subroutine gfnff_sp(nat, ichrg, numbers, posotions, status, energy, grad)
    integer,intent(in) :: nat, ichrg
    integer,intent(in) :: numbers(nat)
    double precision,intent(in) :: posotions(3, nat)      ! Bohr
    !f2py depend(posotions) :: nat=shape(posotions,1)
    !f2py depend(numbers) :: nat=size(numbers)

    integer :: io
    integer,intent(out) :: status
    double precision,intent(out) :: energy          ! Hartree
    double precision,intent(out) :: grad(3, nat)    ! Hartree / Bohr
    logical, parameter :: pr = .false.
    type(gfnff_data) :: calculator

    !> calculation
    call calculator%init(nat,numbers,posotions,print=pr,verbose=pr,ichrg=ichrg,iostat=io)
    if (io == 0) then
        ! Topology setup successful
        status = 0
    else
        ! Topology setup exited with errors
        status = 1
        error stop
    end if
    call gfnff_singlepoint(nat,numbers,posotions,calculator,energy,grad,pr,iostat=io)
    if (io == 0) then
        ! Singlepoint successful!
        status = 0
    else
        ! Singlepoint exited with errors
        status = 2
        error stop
    end if
end subroutine gfnff_sp


! subroutine gfnff_alpb(nat, ichrg, numbers, posotions, sol, energy, grad, io)
!     integer,intent(in) :: nat
!     integer,intent(in) :: sol
!     integer,intent(in) :: ichrg
!     integer,intent(in) :: numbers(nat)
!     double precision,intent(out) :: energy
!     double precision,intent(out) :: grad(nat, 3)
!     double precision,intent(in) :: posotions(nat, 3)
!     integer,intent(out) :: io

!     !f2py intent(in) :: nat, ichrg, numbers, posotions, io, sol
!     !f2py intent(out) :: energy, grad
!     !f2py depend(nat) :: grad, posotions

!     logical :: pr = .false.
!     type(gfnff_data) :: calculator
!     character(len=:),allocatable :: alpbsolvent
!     alpbsolvent = 'h2o'

!     !> calculation
!     call gfnff_initialize(nat,numbers,posotions,calculator,print=pr,ichrg=ichrg,iostat=io)
!     call gfnff_singlepoint(nat,numbers,posotions,calculator,energy,grad,pr,iostat=io)
! end subroutine gfnff_alpb

end module gfnff
