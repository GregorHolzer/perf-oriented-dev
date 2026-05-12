cmake_minimum_required(VERSION 3.10)
project(perf_oriented_prog_samples)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenMP REQUIRED)

if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

if(NOT DEFINED ENTRY_SIZE)
  set(ENTRY_SIZE 8)
endif()

add_executable(benchmark benchmark/benchmark.cpp)
target_link_libraries(benchmark PRIVATE OpenMP::OpenMP_CXX)

target_compile_definitions(benchmark PRIVATE SIZE=${ENTRY_SIZE})
