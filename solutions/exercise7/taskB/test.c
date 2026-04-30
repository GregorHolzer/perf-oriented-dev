#include <stdio.h>
#include <stdlib.h>

int
main(void)
{
  int* a = malloc(sizeof(int));
  *a = 12;
  printf("a: %d\n", *a);
  printf("a: %p\n", a);
  free(a);
  int* b = malloc(sizeof(int));
  printf("b: %d\n", *b);
  printf("b: %p\n", b);
  free(b);
  int* c = calloc(1, sizeof(int));
  printf("c: %d\n", *c);
  printf("c: %p\n", c);
}