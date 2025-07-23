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


# add_subdirectory("config")
add_subdirectory("fortran")
# Define two variables in this directory above:
#   libs: dependencies
#   srcs: sources
add_library(gfnff STATIC ${srcs})
target_link_libraries(gfnff PUBLIC "${libs}")


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
