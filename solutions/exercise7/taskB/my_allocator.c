#define NUM_OF_PAGES 1

typedef struct arena{
  size_t total_size;
  void* start;
  void* current_pos;
} arena;

arena* my_arena = NULL;



void* malloc(size_t size);

void free(void* p);




