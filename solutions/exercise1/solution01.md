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

### Delanoy

Program calculates the Delanoy Number for a square grid of lenth *n*.
The Delanoy Number equals the number of unique ways from the lower left to the upper right corner by only going north, east or northeast. The workload is scaled by the size of the grid *n*

* Runing:

   ```bash
    ./delannoy <n>
    ```

* Measurements:

   | n  | Wall Clock Time | CPU Time | System Time | Max Memory Usage |
   |----|-----------------|----------|-------------|------------------|
   | 13 | 0.67 s          | 0.67 s   | 0.00 s      | 1384 kB          |
   | 14 | 3.75 s          | 3.74 s   | 0.00 s      | 1504 kB          |
   | 15 | 56.44 s         | 56.28 s  | 0.00 s      | 1464 kB          |
