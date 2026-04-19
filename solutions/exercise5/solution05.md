# Exercise 05

## Top 3 Most Effective Flags

### #1 — `-fpeel-loops` (+0.452% mean improvement)

Peels the first and last few iterations off a loop body, separating them from the main loop. This allows the compiler to eliminate redundant conditional checks (e.g. boundary or special-case checks) that only apply at the start or end of iteration, leaving the hot inner loop cleaner and more amenable to further optimization.

| Program   | Improvement |
|-----------|-------------|
| npb_bt_w  | +4.527%     |
| qap       | +0.043%     |
| ssca2     | −0.142%     |
| nbody     | −0.153%     |
| delannoy  | −0.155%     |
| mmul      | −1.406%     |
---

### #2 — `-floop-unroll-and-jam` (+0.093% mean improvement)

Unrolls outer loops and "jams" (fuses) the resulting copies of the inner loop together. This increases instruction-level parallelism and improves register reuse across iterations, particularly benefiting loops with independent iterations that the CPU can execute out-of-order.

| Program   | Improvement |
|-----------|-------------|
| npb_bt_w  | +0.823%     |
| mmul      | +0.248%     |
| qap       | +0.043%     |
| nbody     | −0.023%     |
| delannoy  | −0.258%     |
| ssca2     | −0.276%     |

---

### #3 — `-fvect-cost-model=dynamic` (+0.067% mean improvement)

Relaxes the vectorization cost model from `-O2`'s conservative `very-cheap` threshold to `dynamic`, allowing the compiler to vectorize loops where the profitability is uncertain at compile time. Under `dynamic`, the compiler emits both a vectorized and scalar path and selects between them at runtime based on actual loop trip counts.

| Program   | Improvement |
|-----------|-------------|
| npb_bt_w  | +1.646%     |
| mmul      | +0.414%     |
| qap       | −0.171%     |
| delannoy  | −0.052%     |
| nbody     | −0.348%     |
| ssca2     | −1.086%     |

> Beneficial where loops are long and regular (`npb_bt_w`, `mmul`). Counterproductive for `ssca2` and `nbody` — the runtime dispatch overhead and larger code footprint outweigh the vectorization gains for these workloads.