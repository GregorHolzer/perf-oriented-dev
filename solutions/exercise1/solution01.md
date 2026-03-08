# Solution Sheet 1

## Task A

### Building

```bash
mkdir build
cd build
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja
```

### Measurents

* Wall Clock Time: Total time of the program
* User Time: Time CPU spent running program code
* System Time: Time CPU spent executing kernel code requested form program
* CPU Time = User Time + System Time

### delanoy

Program calculates the Delanoy Number for a square grid of lenth *n*.
The Delanoy Number equals the number of unique ways from the lower left to the upper right corner by only going north, east or northeast. The workload is scaled by the size of the grid *n*

* Runing:

   ```bash
    ./delannoy <n>
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| 13 | 0.692 | 0.000 | 0.690 | 0.000 | 1479.000 | 5678.667 |
| 14 | 3.935 | 0.001 | 3.913 | 0.001 | 1493.000 | 10894.667 |
| 15 | 58.748 | 0.022 | 58.328 | 0.036 | 1496.000 | 2624.000 |

### filegen

Program creates a number of m directories within a seperate parent directory at the current location, each containing n files of size l to u.

* Runing:

   ```bash
    ./filegen <n> <m> <l> <u>
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| 10 50 10000 100000 | 0.193 | 0.000 | 0.185 | 0.000 | 1858.000 | 5050.667 |
| 100 50 10000 100000 | 2.005 | 0.002 | 1.945 | 0.000 | 1780.000 | 1056.000 |
| 100 50 100000 1000000 | 17.385 | 0.016 | 17.102 | 0.015 | 3315.000 | 2105.333 |
| 1000 100 1000 1000 | 4.103 | 0.059 | 3.910 | 0.034 | 1579.000 | 15300.000 |

### filesearch

Returns the largest file of the current directory and all subdirectories.

* Running:
  
   ```bash
    ./filesearch
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| (no args) | 0.177 | 0.000 | 0.168 | 0.000 | 1668.000 | 8074.667 |

### mmul

Multiplies to a matrix with the idendity matrix and verifies the result. The size can be configured at compile time.

* Running:
  
   ```bash
    ./mmul
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| (no args) | 0.760 | 0.000 | 0.750 | 0.000 | 24903.000 | 5550.667 |

## nbody

Runs a physics simulation of multiple objects in space and calculates, for each timestep, the gravitational forces applied to each object.

* Running:
  
   ```bash
    ./nbody
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| (no args) | 0.508 | 0.000 | 0.505 | 0.000 | 2031.000 | 2212.000 |

### qap

Optimizes the solution to a QAP problem. Takes the path f to a file as problem input.

* Running:
  
   ```bash
    ./nbody <f>
    ```

| args | wall_clock_s_mean | wall_clock_s_var | cpu_time_s_mean | cpu_time_s_var | max_rss_kb_mean | max_rss_kb_var |
| --- | --- | --- | --- | --- | --- | --- |
| ../../small_samples/qap/problems/chr10a.dat | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1681.000000 | 1444.000000 |
| ../../small_samples/qap/problems/chr15a.dat | 1.770000 | 0.000200 | 1.762500 | 0.000225 | 1706.000000 | 410.666667 |

