cmake_minimum_required(VERSION 3.10)
project(perf_oriented_prog_samples)

set_property(GLOBAL PROPERTY C_STANDARD 11)

if(MSVC)
  add_compile_options(/W4 /WX)
else()
  add_compile_options(-Wall -Wextra -Wpedantic -Werror -O2)
endif()

if(NOT DEFINED S)
  set(S 2048)
endif()
if(NOT DEFINED T)
  set(T 2048)
endif()

add_executable(mmul mmul/mmul.c)

target_compile_definitions(mmul PRIVATE S=${S})
target_compile_definitions(mmul PRIVATE T=${T})