#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define NUM_OF_PAGES 130000

typedef struct arena
{
  size_t memory_size;
  void* start;
  void* current_pos;
  void* max_alloc;
} arena;

arena* my_arena = NULL;

void
create_arena()
{
  size_t page_size = sysconf(_SC_PAGE_SIZE);
  size_t total = NUM_OF_PAGES * page_size;
  void* mem = mmap(NULL,
                   NUM_OF_PAGES * page_size,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS,
                   -1,
                   0);

  if (mem == MAP_FAILED) {
    exit(1);
  }
  my_arena = mem;
  my_arena->start = (char*)mem + sizeof(arena);
  my_arena->current_pos = my_arena->start;
  my_arena->max_alloc = my_arena->current_pos;
  my_arena->memory_size = total - sizeof(arena);
}

void*
malloc(size_t size)
{
  if (my_arena == NULL) {
    create_arena();
  }
  size = (size + 7) & ~7;
  size_t used = (char*)my_arena->current_pos - (char*)my_arena->start;
  if (used + size > my_arena->memory_size) {
    exit(1);
  }
  void* req_mem = my_arena->current_pos;
  my_arena->current_pos = (char*)my_arena->current_pos + size;
  if (my_arena->current_pos > my_arena->max_alloc)
    my_arena->max_alloc = my_arena->current_pos;
  return req_mem;
}

void*
calloc(size_t nmemb, size_t size)
{
  void* req_mem = malloc(nmemb * size);
  if ((char*)req_mem + size < (char*)my_arena->max_alloc) {
    for (size_t i = 0; i < size; i++) {
      *((char*)req_mem + i) = 0;
    }
  }
  return req_mem;
}

void
free(void* p)
{
  if (my_arena == NULL)
    return;
  my_arena->current_pos = p;
}
