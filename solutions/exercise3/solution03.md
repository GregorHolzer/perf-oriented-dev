
# Solution Sheet 1

## Task A

### Building

Modify CMake file:

```cmake
...
set(CMAKE_C_STANDARD 11)
...
add_compile_options(-pg)
...
```

Build:

```bash
mkdir build
cd build
cmake .. -G Ninja 
ninja
```

Run and receive gprof output:

```bash
./npb_bt_a
./npb_bt_b
gprof npb_bt_a
gprof npb_bt_b
```
### Interpret Output

| Function Name | Notes |
|---------------|-------|
| binvcrhs      | Consumes 22.68% of the time but is called very often -> 0 ms/call -> not much potential for optimization |
| compute_rhs   | Consumes 17.76% of the time ->  93.22 ms/call, is not called 202 times, has no children -> inspect this function |
| matmul_sub | Same characteristics as binvcrhs|
| y_solve, x_solve , z_solve | These three functions have basically the same behavior, they call **binvcrhs** and **matmul_sub**, they have also a high self ms/call: 93.22 -> also worth optimizing |

The rest of the functions are each responsible for less than 5% of thee program time, therefore irrelevant.