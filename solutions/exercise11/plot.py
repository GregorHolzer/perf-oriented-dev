import pandas as pd
import matplotlib.pyplot as plt
import sys

df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "results.csv")

modes = {
    "std":     "Recursive",
    "cache":   "Memoization",
    "dynamic": "Dynamic Programming",
}

fig, ax = plt.subplots(figsize=(8, 5))
fig.suptitle("Delannoy Benchmark", fontsize=14, fontweight="bold")

for mode, label in modes.items():
    data = df[df["mode"] == mode].groupby("n")["time_ms"].median()
    ax.plot(data.index, data.values, marker="o", label=label)

ax.set_ylabel("Time [ms]")
ax.set_yscale('log')
ax.set_xticks(range(1, df["n"].max() + 1, 2))
ax.grid(True, linestyle="--", alpha=0.5)

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)

plt.tight_layout()
plt.savefig("delannoy_results.png", dpi=300, bbox_inches="tight")