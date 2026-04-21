cmake_minimum_required(VERSION 3.10)
project(perf_oriented_prog_samples)

set_property(GLOBAL PROPERTY C_STANDARD 11)

if(MSVC)
  add_compile_options(/W4 /WX)
else()
  add_compile_options(-Wall -Wextra -Wpedantic -O0)
endif()

add_executable(cache_benchmark benchmark/cache_benchmark.c)

target_link_libraries(cache_benchmark PRIVATE -fopenmp)