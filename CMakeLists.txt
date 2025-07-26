cmake_minimum_required(VERSION 3.17.2...3.26)

project(
  _pygfnff
  VERSION 0.0.1
  LANGUAGES C Fortran
)

########################################################################
################      External Fortran Library        ##################
########################################################################
# General configuration information
# Compiler settings for GNU and Intel Fortran compilers
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
  set(dialect "-g -O0 -fbacktrace -ffree-line-length-none -fbacktrace")
  set(bounds "-fbounds-check -ffpe-trap=invalid,zero,overflow")
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
  set(dialect "-g -O2 -r8 -align array64byte -traceback")
  set(bounds "-check all -fpe0")
else()
  message(FATAL_ERROR "Please use an Intel or GNU compiler!")
endif()
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${dialect}")
set(CMAKE_Fortran_FLAGS_DEBUG "${CMAKE_Fortran_FLAGS_DEBUG} ${bounds}")
option(WITH_OpenMP "Enable OpenMP support"                  FALSE)
option(WITH_GBSA   "Build with implicit solvation support"  TRUE)
# OpenMP parallelization
if(NOT TARGET "OpenMP::OpenMP_Fortran")
  if (WITH_OpenMP)
    find_package("OpenMP" REQUIRED)
    add_compile_definitions(WITH_OpenMP)
  else()
    # Create dummy library
    add_library("OpenMP::OpenMP_Fortran" INTERFACE IMPORTED)
  endif()
endif()
# Linear algebra (contains BLAS)
# Compatible with Windows MSYS
#   https://www.soinside.com/question/JW92rdzwmdNuSooN8P4Tx7
set(CMAKE_FIND_LIBRARY_PREFIXES ";lib")
message(STATUS "BLAS libraries: ${BLAS_LIBRARIES}")
message(STATUS "LAPACK libraries: ${LAPACK_LIBRARIES}")
if(NOT TARGET "LAPACK::LAPACK")
    find_package("LAPACK" REQUIRED)
endif()
set(
  lib-deps
  "OpenMP::OpenMP_Fortran"
  "LAPACK::LAPACK"
  "$<$<VERSION_LESS:${CMAKE_VERSION},3.20>:BLAS::BLAS>"
)
# Custom compile arguments
IF(WITH_GBSA)
    add_definitions(-DWITH_GBSA)
ENDIF()

set(srcs)
set(flib "gfnff_fortran")
add_subdirectory("fortran")
add_library(${flib} STATIC ${srcs})
set_target_properties(
  ${flib}
  PROPERTIES
  POSITION_INDEPENDENT_CODE TRUE
  OUTPUT_NAME "${PROJECT_NAME}"
  VERSION "${PROJECT_VERSION}"
  SOVERSION "${PROJECT_VERSION_MAJOR}"
  WINDOWS_EXPORT_ALL_SYMBOLS TRUE
  # Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/include"
)
target_link_libraries(${flib} PUBLIC "${lib-deps}")
target_include_directories(
  ${flib} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/${module-dir}>
)
if(NOT EXISTS "${PROJECT_BINARY_DIR}/include")
    file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/include")
endif()


########################################################################
################        Numpy F2PY Library          ####################
########################################################################
# Python, Numpy & F2PY headers, fortranobject dependencies
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)
include(UseF2Py)
# Create the F2Py `numpyobject` library.
f2py_object_library(f2py_object OBJECT)

set(fortran_src_file "${f2pysrcs}")
set(py_module_name "_pygfnfflib")
f2py_generate_module("${py_module_name}" "${fortran_src_file}" OUTPUT_VARIABLE f_files)
MESSAGE(STATUS "This var key = ${f_files}.")
python_add_library("${py_module_name}" MODULE "${f_files}" "${fortran_src_file}" WITH_SOABI)
target_link_libraries("${py_module_name}" PRIVATE f2py_object ${flib})
install(TARGETS ${py_module_name} DESTINATION pygfnff)