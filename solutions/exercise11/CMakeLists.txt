cmake_minimum_required(VERSION 3.10)
project(perf_oriented_prog_samples)

set(CMAKE_BUILD_TYPE Release)

set(CMAKE_CXX_STANDARD 23)

if(MSVC)
  add_compile_options(/W4 /WX)
else()
  add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

find_package(OpenMP REQUIRED)

add_executable(delannoy delannoy/delannoy.cc)
target_link_libraries(delannoy PRIVATE OpenMP::OpenMP_CXX)

option(USE_CACHE "Enable memoization cache for Delannoy" OFF)
option(DYNAMIC "Solve with dyn programming" OFF)

if(USE_CACHE)
  target_compile_definitions(delannoy PRIVATE USE_CACHE)
elseif(DYNAMIC)
  target_compile_definitions(delannoy PRIVATE DYNAMIC)
endif()
