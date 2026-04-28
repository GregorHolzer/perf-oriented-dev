import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

malloc_df   = pd.read_csv("./malloc.csv")
mimalloc_df = pd.read_csv("./mimalloc.csv")
rpmalloc_df = pd.read_csv("./rpmalloc.csv")

# Compute medians
allocators = ["malloc", "mimalloc", "rpmalloc"]
dfs = [malloc_df, mimalloc_df, rpmalloc_df]
medians = {name: df.median(numeric_only=True) for name, df in zip(allocators, dfs)}

colors = ["#4C72B0", "#DD8452", "#55A868"]

def save_bar(metric, ylabel, title, filename, scale=1.0):
    values = [medians[a][metric] / scale for a in allocators]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(allocators, values, color=colors, width=0.5, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            f"{val:.2f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_ylim(0, max(values) * 1.15)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(filename, dpi=300)
    plt.close(fig)
    print(f"Saved {filename}")

save_bar("wall_clock_s", "Seconds", "Wall Clock Time", "wall_clock.png")

user_vals = [medians[a]["user_cpu_s"] for a in allocators]
sys_vals  = [medians[a]["sys_cpu_s"]  for a in allocators]

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(allocators))
w = 0.5
bars_user = ax.bar(x, user_vals, w, label="User CPU", color=colors, edgecolor="white")
bars_sys  = ax.bar(x, sys_vals,  w, bottom=user_vals, label="System CPU",
                   color=[c + "88" for c in colors], edgecolor="white")  # semi-transparent

for i, (u, s) in enumerate(zip(user_vals, sys_vals)):
    ax.text(x[i], u + s + max(u + s for u, s in zip(user_vals, sys_vals)) * 0.01,
            f"{u+s:.2f}s", ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(allocators)
ax.set_title("CPU Time", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("Seconds", fontsize=12)
ax.set_ylim(0, max(u + s for u, s in zip(user_vals, sys_vals)) * 1.15)
ax.legend(framealpha=0.5)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
fig.savefig("cpu_time.png", dpi=300)
plt.close(fig)
print("Saved cpu_time.png")

save_bar("max_rss_kb", "MB", "Peak Memory Usage", "max_rss.png", scale=1024)