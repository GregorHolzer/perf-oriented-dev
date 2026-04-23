# Sheet 06

## Task B

The Benchmark allocates a buffer of a given size in KB. This buffer contains $n$ elements of the struct: 

```c
typedef struct node
{
  struct node *next;
} node;
```

Another buffer of $n$ Integers is created and filled with the numbers 0 to $n - 1$. The buffer is then shuffeld according to [Fisher-Yates](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle) shuffle. 

The node-buffer is transformed into a linked list where the following element of a node is determined by the integer-buffer:

```c
for (size_t i = 0; i < num_elements - 1; ++i)
  {
    buffer[perm[i]].next = &buffer[perm[i + 1]];
  }
  buffer[perm[num_elements - 1]].next = &buffer[perm[0]];
```

This results in a circle within the node-buffer that covers all nodes.

This is neccessary to avoid the cpu from recognizing access patterns and prefetching any elements.

## Task C

