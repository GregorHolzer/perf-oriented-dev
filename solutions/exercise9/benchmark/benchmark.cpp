#include "linked_list.hpp"
#include <forward_list>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <omp.h>
#include <sys/resource.h>
#include <vector>

#define SEED 1234
#define BENCHMARK_DURATION_SEC 2
#define MINIMUM_ROUNDS 100
#ifndef SIZE
#define SIZE 8
#endif

struct MyEntry
{
  char data[SIZE];
};

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

template<class T>
typename LinkedList<T>::iterator
get_iterator(LinkedList<T>& list, int n)
{
  auto it = list.begin();
  for (int i = 0; i < n; ++i)
    ++it;
  return it;
}

template<class T>
typename std::vector<T>::iterator
get_iterator(std::vector<T>& vector, int n)
{
  return vector.begin() + n;
}

template<class T>
void
insert_container(std::vector<T>& vector, T& element, size_t pos)
{
  auto iterator = get_iterator(vector, pos);
  vector.insert(iterator, element);
}

template<class T>
void
erase_container(std::vector<T>& vector, size_t pos)
{
  auto iterator = get_iterator(vector, pos);
  vector.erase(iterator);
}

template<class T>
void
insert_container(LinkedList<T>& list, T& element, size_t pos)
{
  auto iterator = get_iterator(list, pos);
  list.insert_after(iterator, element);
}

template<class T>
void
erase_container(LinkedList<T>& list, size_t pos)
{
  auto iterator = get_iterator(list, pos);
  list.erase_after(iterator);
}

template<template<class...> class Container, class T, class I>
inline void
read_write(Container<T>& c, I& iterator, int& idx, BenchmarkResult& result)
{
  if (result.read_writes % 2 == 0) {
    iterator = get_iterator(c, idx);
  } else {
    auto element = std::make_unique<T>();
    *(get_iterator(c, idx)) = *element;
  }
  ++result.read_writes;
  idx = (idx + 1) % c.size();
}

template<template<class...> class Container, class T>
inline void
insert_delete(Container<T>& c, int& idx, BenchmarkResult& result)
{
  if (result.ins_del % 2 == 0) {
    auto element = std::make_unique<T>();
    insert_container(c, *element, idx);
  } else {
    erase_container(c, idx);
  }
  ++result.ins_del;
  idx = (idx + 1) % c.size();
}

template<template<class...> class Container, class T, class I>
BenchmarkResult
benchmark(Container<T>& c, float insert_delete_fraction, I& iterator)
{
  auto line = std::string(50, '-');
  std::cout << "Starting Benchmark\n" << line << std::endl;
  int idx = 0;
  auto result = BenchmarkResult();
  auto start_time = omp_get_wtime();
  auto passed_time = omp_get_wtime() - start_time;
  auto element = std::make_unique<T>();
  if (insert_delete_fraction == 0.0f) {
    while (passed_time < BENCHMARK_DURATION_SEC) {
      read_write(c, iterator, idx, result);
      passed_time = omp_get_wtime() - start_time;
    }
  } else {
    int swap_rate = (int)(1.0f / insert_delete_fraction);
    int operation_counter = 0;
    while (passed_time < BENCHMARK_DURATION_SEC) {
      if (operation_counter % swap_rate == 0) {
        insert_delete(c, idx, result);
      } else {
        read_write(c, iterator, idx, result);
      }
      ++operation_counter;
      passed_time = omp_get_wtime() - start_time;
    }
  }
  result.elapsed_time_sec = passed_time;
  return result;
}

int
main(int argc, char** argv)
{
  if (argc != 4) {
    std::cout
      << "Usage: ./benchmark <container_type> <number_elements> <ins_del_ratio>"
      << std::endl;
    return EXIT_FAILURE;
  }
  struct rlimit rl;
  getrlimit(RLIMIT_STACK, &rl);
  rl.rlim_cur = 256 * 1024 * 1024;
  setrlimit(RLIMIT_STACK, &rl);
  std::string container_type = argv[1];
  int n = std::stoi(argv[2]);
  float ratio = std::stof(argv[3]);

  auto element = std::make_unique<MyEntry>();

  if (container_type == "vector") {
    auto vec = std::vector<MyEntry>();
    auto iterator = vec.begin();
    vec.reserve(n + 10);
    for (int i = 0; i < n; ++i) {
      vec.push_back(*element);
    }
    std::cout << benchmark(vec, ratio, iterator) << std::endl;
  } else if (container_type == "list") {
    auto list = LinkedList<MyEntry>();
    auto iterator = list.before_begin();
    for (int i = 0; i < n; ++i) {
      list.push_front(*element);
    }
    std::cout << benchmark(list, ratio, iterator) << std::endl;
  } else if (container_type == "list_shuffled") {
    auto list = LinkedList<MyEntry>();
    auto iterator = list.before_begin();
    for (int i = 0; i < n; ++i) {
      list.push_front(*element);
    }
    list.shuffle_list(SEED);
    std::cout << benchmark(list, ratio, iterator) << std::endl;
  }
}
