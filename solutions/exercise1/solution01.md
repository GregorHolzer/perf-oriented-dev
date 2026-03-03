# Solution Sheet 1

## Task A

### Building

```bash
mkdir build
cd build
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja
```

### Delanoy

Program calculates the Delanoy Number for a square grid of lenth *n*.
The Delanoy Number equals the number of unique ways from the lower left to the upper right corner by only going north, east or northeast. The workload is scaled by the size of the grid *n*

* Runing:

   ```bash
    ./delannoy <n>
    ```
