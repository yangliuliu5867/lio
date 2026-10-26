cmake_minimum_required(VERSION 3.0.2)
project(lio_workspace)

set(CATKIN_TOPLEVEL TRUE)

# Search for catkin within the workspace before using the installed version.
set(_cmd "catkin_find_pkg" "catkin" "${CMAKE_SOURCE_DIR}")
execute_process(COMMAND ${_cmd}
  RESULT_VARIABLE _res
  OUTPUT_VARIABLE _out
  ERROR_VARIABLE _err
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_STRIP_TRAILING_WHITESPACE)
if(NOT _res EQUAL 0 AND NOT _res EQUAL 2)
  string(REPLACE ";" " " _cmd_str "${_cmd}")
  message(FATAL_ERROR "Search for catkin in workspace failed (${_cmd_str}): ${_err}")
endif()

if(_res EQUAL 0)
  set(catkin_EXTRAS_DIR "${CMAKE_SOURCE_DIR}/${_out}/cmake")
  include(${catkin_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
  add_subdirectory("${CMAKE_SOURCE_DIR}/${_out}")
else()
  find_package(catkin REQUIRED NO_POLICY_SCOPE)
endif()

catkin_workspace()
