#include <cstdint>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unordered_map>
#include <utility>

typedef unsigned long dn;

auto
get_key(dn x, dn y) -> uint64_t
{
  return (uint64_t)x << 32 | (uint64_t)y;
}

auto
check_cache(dn x, dn y, dn& result, std::unordered_map<uint64_t, dn>& map)
  -> bool
{
  auto it = map.find(get_key(x, y));
  if (it == map.end())
    return false;
  result = it->second;
  return true;
}

auto
insert_cache(dn x, dn y, dn result, std::unordered_map<uint64_t, dn>& map)
  -> void
{
  map.insert({ get_key(x, y), result });
}

auto
delannoy(dn x, dn y) -> dn
{
  if (x == 0 || y == 0)
    return 1;

  dn a = delannoy(x - 1, y);
  dn b = delannoy(x - 1, y - 1);
  dn c = delannoy(x, y - 1);

  return a + b + c;
}

auto
delannoy(dn x, dn y, std::unordered_map<uint64_t, dn>& map) -> dn
{
  if (x == 0 || y == 0)
    return 1;

  dn result;

  if (check_cache(x, y, result, map))
    return result;

  result = delannoy(x - 1, y, map) + delannoy(x - 1, y - 1, map) +
           delannoy(x, y - 1, map);
  insert_cache(x, y, result, map);
  return result;
}

dn DELANNOY_RESULTS[] = { 1,
                          3,
                          13,
                          63,
                          321,
                          1683,
                          8989,
                          48639,
                          265729,
                          1462563,
                          8097453,
                          45046719,
                          251595969,
                          1409933619,
                          7923848253,
                          44642381823,
                          252055236609,
                          1425834724419,
                          8079317057869,
                          45849429914943,
                          260543813797441,
                          1482376214227923,
                          8443414161166173 };

int NUM_RESULTS = sizeof(DELANNOY_RESULTS) / sizeof(dn);

int
main(int argc, char** argv)
{
  if (argc < 2) {
    printf("Usage: delannoy N [+t]\n");
    exit(-1);
  }

  int n = atoi(argv[1]);
  if (n >= NUM_RESULTS) {
    printf("N too large (can only check up to %d)\n", NUM_RESULTS);
    exit(-1);
  }

  dn result = 0;

#ifdef USE_CACHE
  auto map = std::unordered_map<uint64_t, dn>{};
  result = delannoy(n, n, map);
#else
  result = delannoy(n, n);
#endif

  if (result == DELANNOY_RESULTS[n]) {
    printf("Verification: OK\n");
    return EXIT_SUCCESS;
  }
  printf("Verification: ERR\n");
  return EXIT_FAILURE;
}
