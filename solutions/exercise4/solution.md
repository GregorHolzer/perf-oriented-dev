# Sheet 4

## Task A

### Discussion of Results

* **npb_bt**: 
  Is almost allocating no memory exept for some I/O operations (fopen, printf)
* **ssca2**: 
  * Consumes an constant amount of memory (8.5 MiB) until 10000ms
  * Peak occures afterward consuming (24.5 MiB) 
  * Consumtion drops almost instantly to (19 MiB) 

Measuring the Heap-Usage of a program using **massif** adds a heavy overhead to execution time.

## Task B

### Reported events 

```bash
perf list | grep "\[Hardware cache event\]"
  L1-dcache-load-misses                              [Hardware cache event]
  L1-dcache-loads                                    [Hardware cache event]
  L1-dcache-prefetch-misses                          [Hardware cache event]
  L1-dcache-prefetches                               [Hardware cache event]
  L1-dcache-store-misses                             [Hardware cache event]
  L1-dcache-stores                                   [Hardware cache event]
  L1-icache-load-misses                              [Hardware cache event]
  L1-icache-loads                                    [Hardware cache event]
  LLC-load-misses                                    [Hardware cache event]
  LLC-loads                                          [Hardware cache event]
  LLC-prefetch-misses                                [Hardware cache event]
  LLC-prefetches                                     [Hardware cache event]
  LLC-store-misses                                   [Hardware cache event]
  LLC-stores                                         [Hardware cache event]
  branch-load-misses                                 [Hardware cache event]
  branch-loads                                       [Hardware cache event]
  dTLB-load-misses                                   [Hardware cache event]
  dTLB-loads                                         [Hardware cache event]
  dTLB-store-misses                                  [Hardware cache event]
  dTLB-stores                                        [Hardware cache event]
  iTLB-load-misses                                   [Hardware cache event]
  iTLB-loads                                         [Hardware cache event]
  node-load-misses                                   [Hardware cache event]
  node-loads                                         [Hardware cache event]
  node-prefetch-misses                               [Hardware cache event]
  node-prefetches                                    [Hardware cache event]
  node-store-misses                                  [Hardware cache event]
  node-stores                                        [Hardware cache event]
```

### Discussion of Results

The **ssca2** program is less efficient in terms of memory access compared to **npb_bt**. This is probably related to the fact that the data of **npb_bt** is largely located on the stack and access is cache friendly compard to **ssca2**.

Somehow the branch-load miss rate for **ssca2** is greater than one. That seems not very intiutive and I cannot explain this.

There is almost no overhead of measuring cpu counters with perf.