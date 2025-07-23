module _pygfnfflib
    use iso_fortran_env,only:wp => real64,stdout => output_unit
    use gfnff_interface
    implicit none

contains

subroutine gfnff_sp(nat, ichrg, at, xyz, energy, grad, io)
    integer,intent(in) :: nat
    integer,intent(in) :: ichrg
    integer,intent(in) :: at(nat)
    real(wp),intent(out) :: energy
    real(wp),intent(out) :: grad(nat, 3)
    real(wp),intent(in) :: xyz(nat, 3)
    integer,intent(out) :: io

    !f2py intent(in) :: nat, ichrg, at, xyz, io
    !f2py intent(out) :: energy, grad
    !f2py depend(nat) :: grad, xyz

    type(gfnff_data) :: calculator
    logical, parameter :: pr = .false.

    !> calculation
    call gfnff_initialize(nat,at,xyz,calculator,print=pr,ichrg=ichrg,iostat=io)
    call gfnff_singlepoint(nat,at,xyz,calculator,energy,grad,pr,iostat=io)
end subroutine gfnff_sp

! subroutine gfnff_alpb(nat, ichrg, at, xyz, sol, energy, grad, io)
!     integer,intent(in) :: nat
!     integer,intent(in) :: sol
!     integer,intent(in) :: ichrg
!     integer,intent(in) :: at(nat)
!     real(wp),intent(out) :: energy
!     real(wp),intent(out) :: grad(nat, 3)
!     real(wp),intent(in) :: xyz(nat, 3)
!     integer,intent(out) :: io

!     !f2py intent(in) :: nat, ichrg, at, xyz, io, sol
!     !f2py intent(out) :: energy, grad
!     !f2py depend(nat) :: grad, xyz

!     logical :: pr = .false.
!     type(gfnff_data) :: calculator
!     character(len=:),allocatable :: alpbsolvent
!     if sol == 0 then
!         alpbsolvent = 'h2o'
!     else
!         alpbsolvent = 'h2o'
!     end if

!     !> calculation
!     call gfnff_initialize(nat,at,xyz,calculator,print=pr,ichrg=ichrg,iostat=io)
!     call gfnff_singlepoint(nat,at,xyz,calculator,energy,grad,pr,iostat=io)
! end subroutine gfnff_alpb

end module _pygfnfflib
