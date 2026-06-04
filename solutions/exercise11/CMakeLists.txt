cmake_minimum_required(VERSION 3.10)
project(perf_oriented_prog_samples)

set(CMAKE_BUILD_TYPE Release)

set(CMAKE_CXX_STANDARD 23)

if(MSVC)
  add_compile_options(/W4 /WX)
else()
  add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

add_executable(delannoy delannoy/delannoy.cc)

option(USE_CACHE "Enable memoization cache for Delannoy" OFF)

if(USE_CACHE)
  target_compile_definitions(delannoy PRIVATE USE_CACHE)
endif()
