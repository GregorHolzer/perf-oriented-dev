import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys

df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "results.csv")

cached   = df[df["cache"] == True].groupby("n").median(numeric_only=True)
uncached = df[df["cache"] == False].groupby("n").median(numeric_only=True)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Delannoy Benchmark", fontsize=14, fontweight="bold")

ax = axes[0]
ax.plot(uncached.index, uncached["wall_clock_s"], marker="o", label="no cache")
ax.plot(cached.index,   cached["wall_clock_s"],   marker="o", label="cache")
ax.set_xticks(range(1, 16, 2))
ax.set_ylabel("Wall Clock Time [sec]")
ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
ax.grid(True, which="both", linestyle="--", alpha=0.5)

# --- Peak memory ---
ax = axes[1]
ax.plot(uncached.index, uncached["max_rss_kb"] / 1024, marker="o", label="no cache")
ax.plot(cached.index,   cached["max_rss_kb"]   / 1024, marker="o", label="cache")
ax.set_ylabel("Peak Memory [MB]")
ax.set_xticks(range(1, 16, 2))
ax.set_ylim(bottom=0, top=df["max_rss_kb"].max() / 1024 * 1.1)
ax.grid(True, linestyle="--", alpha=0.5)

handles, labels = axes[0].get_legend_handles_labels()
custom_labels = ["Default", "Memoization"]
fig.legend(handles, custom_labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.01))
plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig("delannoy_results.png", dpi=300, bbox_inches="tight")
