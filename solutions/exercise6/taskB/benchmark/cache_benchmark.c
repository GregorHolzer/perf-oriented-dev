#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#ifndef SEED
#define SEED 1234
#endif

typedef struct node
{
  struct node *next;
} node;

node *create_buffer(size_t num_elements)
{
  node *buffer = malloc(num_elements * sizeof(node));
  size_t *perm = malloc(num_elements * sizeof(size_t));
  for (size_t i = 0; i < num_elements; ++i)
  {
    perm[i] = i;
  }
  for (size_t i = num_elements - 1; i > 0; --i)
  {
    size_t j = rand() % (i + 1);
    size_t tmp = perm[i];
    perm[i] = perm[j];
    perm[j] = tmp;
  }
  for (size_t i = 0; i < num_elements - 1; ++i)
  {
    buffer[perm[i]].next = &buffer[perm[i + 1]];
  }
  buffer[perm[num_elements - 1]].next = &buffer[perm[0]];

  free(perm);
  return buffer;
}

int main(int argc, char **argv)
{
  if (argc != 3)
  {
    return 1;
  }
  int buffer_s = strtol(argv[1], NULL, 10);
  int samples = strtol(argv[2], NULL, 10);
  srand(SEED);
  size_t num_elements = buffer_s / sizeof(node);
  node *buffer = create_buffer(num_elements);
  node *current_node = &buffer[0];

  size_t total = (size_t)samples * num_elements;

  // Load as much into Caches as possible
  for (size_t i = 0; i < num_elements; ++i)
  {
    current_node = current_node->next;
  }

  double start = omp_get_wtime();
  for (size_t i = 0; i < total; ++i)
  {
    current_node = current_node->next;
  }
  double end = omp_get_wtime();

  printf("%d, %f, %p\n", buffer_s, (end - start) * 1e9 / total, (void *)current_node->next);
}