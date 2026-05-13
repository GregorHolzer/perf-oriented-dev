import matplotlib
from matplotlib import pyplot as plt
import pandas as pd
import os

LCC3 = False
file_dir = "./local"
if LCC3:
    file_dir = "./lcc3"

vector_df        = pd.read_csv(f"{file_dir}/vector.csv")
list_df          = pd.read_csv(f"{file_dir}/list.csv")
list_shuffled_df = pd.read_csv(f"{file_dir}/list_shuffled.csv")

def prepare(df):
    df = df.copy()
    df["total_ops"] = (df["ins_del"] + df["reads_writes"]) * (2.0 / df["elapsed"])
    return df.groupby(["elements", "size", "fraction"], as_index=False)["total_ops"].median()

vector_df        = prepare(vector_df)
list_df          = prepare(list_df)
list_shuffled_df = prepare(list_shuffled_df)

# ── Config ─────────────────────────────────────────────────────────────────────
sizes     = [8, 512, 8_000_000]
size_labels = {8: "8 Byte", 512: "512 Byte", 8_000_000: "8 MByte"}

fractions = [0.0, 0.1, 0.5]
fraction_labels = {0.0: "ins_del=0.0", 0.1: "ins_del=0.1", 0.5: "ins_del=0.5"}

colors  = {"Vector": "#2196F3", "List": "#FF5722", "List (shuffled)": "#4CAF50"}
markers = {"Vector": "o",       "List": "s",       "List (shuffled)": "^"}

datasets = [
    ("Vector",          vector_df),
    ("List",            list_df),
    ("List (shuffled)", list_shuffled_df),
]

# ── 3×3 grid: rows = sizes, cols = fractions ───────────────────────────────────
fig, axes = plt.subplots(3, 3, figsize=(15, 12), sharey=False)
fig.suptitle("Benchmark — all configurations", fontsize=14, fontweight="bold")

for row, size in enumerate(sizes):
    for col, frac in enumerate(fractions):
        ax = axes[row][col]

        for label, df in datasets:
            sub = df[(df["size"] == size) & (df["fraction"] == frac)].sort_values("elements")
            ax.scatter(
                sub["elements"], sub["total_ops"],
                color=colors[label], marker=markers[label],
                s=60, zorder=3, label=label,
            )
            ax.plot(sub["elements"], sub["total_ops"],
                    color=colors[label], alpha=0.25, linewidth=1)

        ax.set_xscale("log")
        ax.set_xticks([10, 1000, 100000, 10000000])
        ax.xaxis.set_major_formatter(matplotlib.ticker.LogFormatterSciNotation())
        ax.set_yscale("log")
        ax.set_ylim(bottom=1)
        ax.grid(True, linestyle="--", alpha=0.4, axis='y')

        # row labels (size) on the left, col labels (fraction) on top
        if row == 0:
            ax.set_title(fraction_labels[frac], fontsize=10)
        if col == 0:
            ax.set_ylabel(f"{size_labels[size]}\nTotal ops (norm.)", fontsize=9)
        if row == 2:
            ax.set_xlabel("Elements", fontsize=9)
from matplotlib.lines import Line2D
handles = [
    Line2D([0], [0], marker=markers[label], color=colors[label],
           linestyle="None", markersize=7, label=label)
    for label, _ in datasets
]
fig.legend(handles=handles, loc="lower center", ncol=3,
           fontsize=9, bbox_to_anchor=(0.5, -0.02), frameon=True)

fig.tight_layout()
os.makedirs("./plots", exist_ok=True)
fig.savefig("./plots/bench_all.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Saved bench_all.png")

# Create 1 row, 3 columns (one per element size)
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
fig.suptitle("Benchmark — Grouped by Element Size", fontsize=14, fontweight="bold")

# Define line alpha or styles to distinguish ratios (fractions)
ratio_alphas = {frac: (i + 1) / len(fractions) for i, frac in enumerate(fractions)}
# Alternatively, use different line styles for the ratios
ratio_styles = {frac: style for frac, style in zip(fractions, ["-", "--", ":"])}

for col, size in enumerate(sizes):
    ax = axes[col]
    ax.set_title(f"Size: {size_labels[size]}", fontsize=12, fontweight="bold")
    
    for label, df in datasets:
        for frac in fractions:
            sub = df[(df["size"] == size) & (df["fraction"] == frac)].sort_values("elements")
            
            # Plotting each ratio as a separate line for the container
            ax.plot(
                sub["elements"], sub["total_ops"],
                color=colors[label],
                linestyle=ratio_styles[frac],
                alpha=0.8,
                linewidth=1.5,
                label=f"{label} (Ratio: {fraction_labels[frac]})" if col == 0 else "_"
            )
            
            ax.scatter(
                sub["elements"], sub["total_ops"],
                color=colors[label],
                marker=markers[label],
                s=30, alpha=0.6, zorder=3
            )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(bottom=1)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_xlabel("Elements", fontsize=10)
    
    if col == 0:
        ax.set_ylabel("Total ops (norm.)", fontsize=10)

# Create a clear legend for Containers (Color) and Ratios (Line Style)
legend_elements = []
# Container colors
for label, _ in datasets:
    legend_elements.append(Line2D([0], [0], color=colors[label], marker=markers[label], 
                                  lw=1.5, label=label))
# Ratio line styles
for frac in fractions:
    legend_elements.append(Line2D([0], [0], color="black", linestyle=ratio_styles[frac], 
                                  label=f"Ratio: {fraction_labels[frac]}"))

fig.legend(handles=legend_elements, loc="lower center", ncol=len(datasets) + len(fractions),
           fontsize=9, bbox_to_anchor=(0.5, -0.08), frameon=True)

fig.tight_layout()
os.makedirs("./plots", exist_ok=True)
fig.savefig("./plots/bench_by_size.png", dpi=150, bbox_inches="tight")

print("Saved bench_by_size.png")