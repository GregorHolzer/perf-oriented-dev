#include "linked_list.hpp"
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <vector>

#define SEED 1234
#define BENCHMARK_DURATION_SEC 5
#define MINIMUM_OPERATIONS 100
#define N 1000

class BenchmarkResult
{
public:
  long ins_del = 0, read_writes = 0;
  float elapsed_time_sec = 0.0f;
};

std::ostream&
operator<<(std::ostream& os, const BenchmarkResult& r)
{
  return os << "ins/del: " << r.ins_del << "\nreads/writes: " << r.read_writes
            << "\nelapsed: " << std::fixed << std::setprecision(10)
            << r.elapsed_time_sec << "s";
}

template<template<class...> class Container, class T>
inline void
read_write(Container<T>& c, T& element, int& idx, BenchmarkResult& result)
{
  if (result.read_writes % 2 == 0) {
    element = c[idx];
  } else {
    c[idx] = element;
  }
  ++result.read_writes;
  idx = (idx + 1) % c.size();
}

template<template<class...> class Container, class T>
inline void
insert_delete(Container<T>& c, T& element, int& idx, BenchmarkResult& result)
{
  if (result.ins_del % 2 == 0) {
    c.insert(c.begin() + idx, element);
  } else {
    c.erase(c.begin() + idx);
  }
  ++result.ins_del;
  idx = (idx + 1) % c.size();
}

template<template<class...> class Container, class T>
BenchmarkResult
benchmark(Container<T>& c, float insert_delete_fraction)
{
  int idx = 0;
  auto result = BenchmarkResult();
  auto start_time = omp_get_wtime();
  auto passed_time = omp_get_wtime() - start_time;
  auto element = c[idx];
  if (insert_delete_fraction == 0.0f) {
    while (passed_time < BENCHMARK_DURATION_SEC) {
      for (int i = 0; i < MINIMUM_OPERATIONS; ++i) {
        read_write(c, element, idx, result);
      }
      passed_time = omp_get_wtime() - start_time;
    }
  } else {
    int swap_rate = (int)(1.0f / insert_delete_fraction);
    while (passed_time < BENCHMARK_DURATION_SEC) {
      for (int i = 0; i < MINIMUM_OPERATIONS; ++i) {
        if (i % swap_rate == 0) {
          insert_delete(c, element, idx, result);
        } else {
          read_write(c, element, idx, result);
        }
      }
      passed_time = omp_get_wtime() - start_time;
    }
    auto vec = std::vector<int>(N);
  }
  result.elapsed_time_sec = passed_time;
  return result;
}

int
main(void) noexcept
{
  auto vec = std::vector<int>(N, 1);
  std::cout << benchmark(vec, 0.5) << std::endl;

  auto list = LinkedList<int>();
  for (int i = 0; i < N; i++)
    list.insert(list.begin() + i, i);
  std::cout << benchmark(list, 0.5) << std::endl;
}