# Sheet 8

# Sheet 8

## Task A

**False Sharing** occurs under the following circumstances:

1. Two variables *x* and *y* are located in the same cache line.
2. This cache line is present in multiple private caches (e.g. several L1 caches of different CPU cores).
3. A thread writes to variable *x*, causing the entire cache line to be invalidated in the other caches.
4. Another thread accesses *y*, but must reload the cache line because it has been invalidated.

This is the concept of **False Sharing** - Differnt threads work with different variables but synchronisation is neccessary, because of an invalidated cache line.

The solution proposed in the PR is putting each element (in this case every ObjectUseData object) on a seperate cache line using the statement:

```c++
class alignas(get_hardware_destructive_interference_size()) ObjectUseData

constexpr std::size_t get_hardware_destructive_interference_size() { return 64; }
```

Alligns ObjectUseData to 64 bytes to avoid false sharing on architectures that have 64 byte cache lines.

[get_hardware_destructive_interference_size](https://en.cppreference.com/cpp/thread/hardware_destructive_interference_size)

## Task B

### [Pull Request](https://github.com/Kludex/uvicorn/pull/1214/changes)

Changing datastructure from **List** to **Dequeue** supporting operations like 

```python
list.pop(0) #O(n)
dequeue.popleft() #O(1)
```

in $O(1)$ instead of $O(n)$. [See here](https://docs.python.org/3/library/collections.html#collections.deque)

Queue contains data of Type `ASGISendEvent`

### TYPES OF DATA

| Characteristic | Status |
| :------------- | :----- |
| comparable     | no     |
| hash defined   | no     |
| countable      | unsure |

### QUANTITY OF DATA

| Characteristic | Status         |
| :------------- | :------------- |
| Total quantity | unsure         |
| Element size   | Possibly large |

### ACCESS PATTERNS

| Characteristic     | Status                            |
| :----------------- | :-------------------------------- |
| Type of access     | Insertion, Removal (FIFO)         |
| Position of access | Front, Back                       |
| Parallel access    | Unsure but dequeue is thread safe |

### TARGET HARDWARE CONSIDERATIONS

* Target Hardware is a CPU
* I assume program will not be limited by memory

The Access Patterns is the most indicating to change the datastructure from `list` to `dequeue`.