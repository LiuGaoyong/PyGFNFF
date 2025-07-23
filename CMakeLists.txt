cmake_minimum_required(VERSION 3.17.2...3.26)

project(
  _pygfnff
  VERSION 0.0.1
  LANGUAGES C Fortran
)

# Python, Numpy & F2PY headers
find_package(
  Python REQUIRED
  COMPONENTS Interpreter
  Development.Module NumPy
)
execute_process(
  COMMAND "${Python_EXECUTABLE}"
  -c "import numpy.f2py; print(numpy.f2py.get_include())"
  OUTPUT_VARIABLE F2PY_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# General configuration information
add_subdirectory("config")
option(WITH_OpenMP "Enable OpenMP support"                  FALSE)
option(WITH_GBSA   "Build with implicit solvation support"  TRUE)
option(WITH_TESTS  "Enable test binary build"               FALSE)
option(build_exe   "Build an executable"                    FALSE)
option(PYTHON_BINDINGS  "Create Python bindings"            FALSE)
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
add_subdirectory("fortran")
add_library("${PROJECT_NAME}-lib" STATIC ${srcs})
set_target_properties(
  "${PROJECT_NAME}-lib"
  PROPERTIES
  POSITION_INDEPENDENT_CODE TRUE
  OUTPUT_NAME "${PROJECT_NAME}"
  VERSION "${PROJECT_VERSION}"
  SOVERSION "${PROJECT_VERSION_MAJOR}"
  WINDOWS_EXPORT_ALL_SYMBOLS TRUE
  # Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/include"
)
target_link_libraries("${PROJECT_NAME}-lib" PUBLIC "${lib-deps}")
target_include_directories(
  "${PROJECT_NAME}-lib"
  PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/${module-dir}>
)
if(NOT EXISTS "${PROJECT_BINARY_DIR}/include")
    file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/include")
endif()


# set(f2py_module_name "molalign")
# set(fortran_src_file "${f2pysrcs}")
# set(f2py_module_c "${f2py_module_name}module.c")
# # Convert to C file by F2PY
# add_custom_command(
#   OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${f2py_module_c}"
#   COMMAND ${PYTHON_EXECUTABLE}  -m "numpy.f2py"
#           "${fortran_src_file}"
#           -m ${f2py_module_name}
#           --lower # Important
#   DEPENDS "${fortran_src_file}" # Fortran source
# )

# python_add_library(
#   ${CMAKE_PROJECT_NAME} MODULE
#   "${f2py_module_name}module.c"
#   "${F2PY_INCLUDE_DIR}/fortranobject.c"
#   "${fortran_src_file}" WITH_SOABI
# )
# target_include_directories(
#   ${CMAKE_PROJECT_NAME} PUBLIC
#   ${F2PY_INCLUDE_DIR}
# )
# target_link_libraries(
#   ${CMAKE_PROJECT_NAME} PUBLIC
#   Python::NumPy
#   MolAlignLib
# )
# install(
#   TARGETS ${CMAKE_PROJECT_NAME}
#   DESTINATION pymolalign
# )
