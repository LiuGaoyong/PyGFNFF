!> F2PY interface of pygfnff.
!>
!> Status codes shared by all routines:
!>   0  success
!>   1  topology setup failed
!>   2  singlepoint calculation failed
!>   3  no (matching) cached calculator, call gfnff_init first
!>
!> None of the routines stops the program: errors are always reported
!> through the status code so that Python can raise an exception.
module gfnff
    use gfnff_interface
    implicit none

contains


!> One-shot singlepoint: the topology is built from scratch on every call.
subroutine gfnff_sp(nat, ichrg, numbers, positions, solvent, status, energy, grad)
    integer,intent(in) :: nat, ichrg
    integer,intent(in) :: numbers(nat)
    double precision,intent(in) :: positions(3, nat)      ! Bohr
    character(len=*),intent(in) :: solvent                ! '' or 'none': gas phase

    integer :: io
    integer,intent(out) :: status
    double precision,intent(out) :: energy          ! Hartree
    double precision,intent(out) :: grad(3, nat)    ! Hartree / Bohr
    logical, parameter :: pr = .false.
    type(gfnff_data) :: calculator

    status = 0
    energy = 0.0d0
    grad(:, :) = 0.0d0

    !> never write gfnff_topo / gfnff_adjacency into the working directory
    calculator%write_topo = .false.

    call calculator%init(nat,numbers,positions,print=pr,verbose=pr, &
    &                    ichrg=ichrg,iostat=io,solvent=solvent)
    if (io /= 0) then
        status = 1
        call calculator%deallocate()
        return
    end if

    call calculator%singlepoint(nat,numbers,positions,energy,grad,verbose=pr,iostat=io)
    if (io /= 0) status = 2
    call calculator%deallocate()
end subroutine gfnff_sp


!> Build the topology once and keep it in the module-level calculator
!> (`my_gfnff_data` of gfnff_interface). There is a single slot only.
subroutine gfnff_init(nat, ichrg, numbers, positions, solvent, status)
    integer,intent(in) :: nat, ichrg
    integer,intent(in) :: numbers(nat)
    double precision,intent(in) :: positions(3, nat)      ! Bohr
    character(len=*),intent(in) :: solvent                ! '' or 'none': gas phase

    integer :: io
    integer,intent(out) :: status
    logical, parameter :: pr = .false.

    status = 0
    call gfnff_free()
    allocate (my_gfnff_data)
    my_gfnff_data%write_topo = .false.

    call my_gfnff_data%init(nat,numbers,positions,print=pr,verbose=pr, &
    &                       ichrg=ichrg,iostat=io,solvent=solvent)
    if (io /= 0) then
        status = 1
        call gfnff_free()
    end if
end subroutine gfnff_init


!> Singlepoint with the topology cached by gfnff_init.
subroutine gfnff_energy(nat, numbers, positions, status, energy, grad)
    integer,intent(in) :: nat
    integer,intent(in) :: numbers(nat)
    double precision,intent(in) :: positions(3, nat)      ! Bohr

    integer :: io
    integer,intent(out) :: status
    double precision,intent(out) :: energy          ! Hartree
    double precision,intent(out) :: grad(3, nat)    ! Hartree / Bohr
    logical, parameter :: pr = .false.

    status = 0
    energy = 0.0d0
    grad(:, :) = 0.0d0

    if (.not. gfnff_cached(nat)) then
        status = 3
        return
    end if

    call my_gfnff_data%singlepoint(nat,numbers,positions,energy,grad,verbose=pr,iostat=io)
    if (io /= 0) status = 2
end subroutine gfnff_energy


!> Release the cached calculator (no-op if there is none).
subroutine gfnff_free()
    if (allocated(my_gfnff_data)) then
        call my_gfnff_data%deallocate()
        deallocate (my_gfnff_data)
    end if
end subroutine gfnff_free


!> Is there a cached calculator for a system of `nat` atoms?
logical function gfnff_cached(nat)
    integer,intent(in) :: nat

    gfnff_cached = .false.
    if (.not. allocated(my_gfnff_data)) return
    if (.not. allocated(my_gfnff_data%topo)) return
    if (.not. allocated(my_gfnff_data%topo%nb)) return
    gfnff_cached = size(my_gfnff_data%topo%nb, 2) == nat
end function gfnff_cached

end module gfnff
