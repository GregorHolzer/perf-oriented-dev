# Exercise 05

## Top 3 Most Effective Flags

### #1 — `-fpeel-loops` (+0.452% mean improvement)

Peels loops for which there is enough information that they do
not roll much (from profile feedback or static analysis).  It
also turns on complete loop peeling (i.e. complete removal of
loops with small constant number of iterations).

Enabled by -O3, -fprofile-use, and -fauto-profile.

| Program  | Improvement |
| -------- | ----------- |
| npb_bt_w | +4.527%     |
| qap      | +0.043%     |
| ssca2    | −0.142%     |
| nbody    | −0.153%     |
| delannoy | −0.155%     |
| mmul     | −1.406%     |
---

### #2 — `-floop-unroll-and-jam` (+0.093% mean improvement)

Apply unroll and jam transformations on feasible loops.  In a
loop nest this unrolls the outer loop by some factor and fuses
the resulting multiple inner loops.  This flag is enabled by
default at -O3.  

It is also enabled by -fprofile-use and -fauto-profile.

| Program  | Improvement |
| -------- | ----------- |
| npb_bt_w | +0.823%     |
| mmul     | +0.248%     |
| qap      | +0.043%     |
| nbody    | −0.023%     |
| delannoy | −0.258%     |
| ssca2    | −0.276%     |

---

### #3 — `-fvect-cost-model=dynamic` (+0.067% mean improvement)

Alter the cost model used for vectorization.  The model
argument should be one of unlimited, dynamic or cheap.  With
the unlimited model the vectorized code-path is assumed to be
profitable while with the dynamic model a runtime check guards
the vectorized code-path to enable it only for iteration
counts that will likely execute faster than when executing the
original scalar loop.  The cheap model disables vectorization
of loops where doing so would be cost prohibitive for example
due to required runtime checks for data dependence or
alignment but otherwise is equal to the dynamic model.  The
default cost model depends on other optimization flags and is
either dynamic or cheap.

| Program  | Improvement |
| -------- | ----------- |
| npb_bt_w | +1.646%     |
| mmul     | +0.414%     |
| qap      | −0.171%     |
| delannoy | −0.052%     |
| nbody    | −0.348%     |
| ssca2    | −1.086%     |