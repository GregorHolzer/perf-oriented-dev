import matplotlib.pyplot as plt
import pandas as pd

default_df = pd.read_csv("./DefaultAllocator.csv")

custom_df = pd.read_csv("./CustomAllocator.csv")

values = [
  default_df['wall_clock_s'].median(),
  custom_df['wall_clock_s'].median()
]

values = values / max(values)

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(["Default Allocator", "Custom Allocator"], values, color=["#DD8452", "#55A868"])

for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{val:.3f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_title("Default vs Custom Allocator", fontsize=14, fontweight="bold")
ax.set_ylabel("Wall Clock")
ax.set_ylim(0, max(values) * 1.1)
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
fig.savefig("./result.png", dpi=300)