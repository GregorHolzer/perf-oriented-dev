CC      = gcc
CFLAGS_LIB  = -O3 -Wall -Wextra -fPIC -shared
CFLAGS_TEST = -O3 -Wall -Wextra
TARGET  = libarena.so
SRC     = arena.c
TEST    = test
TEST_SRC = test.c

.PHONY: all clean test

all: $(TARGET) $(TEST)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS_LIB) -o $(TARGET) $(SRC)

$(TEST): $(TEST_SRC)
	$(CC) $(CFLAGS_TEST) -o $(TEST) $(TEST_SRC)

run: $(TARGET) $(TEST)
	LD_PRELOAD=./$(TARGET) ./$(TEST)

clean:
	rm -f $(TARGET) $(TEST)