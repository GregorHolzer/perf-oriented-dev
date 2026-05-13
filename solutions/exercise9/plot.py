import matplotlib
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import os

LCC3 = True
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
sizes            = [8, 512, 8_000_000]
size_labels      = {8: "8 B", 512: "512 B", 8_000_000: "8 MB"}
size_tags        = {8: "8", 512: "512", 8_000_000: "8M"}

fractions        = [0.0, 0.1, 0.5]
fraction_labels  = {0.0: "r=0.0  (read-only)", 0.1: "r=0.1  (10% writes)", 0.5: "r=0.5  (50% writes)"}
fraction_markers = {0.0: "o", 0.1: "s", 0.5: "^"}

colors  = {"Vector": "#2196F3", "List": "#FF5722", "List (shuffled)": "#4CAF50"}
markers = {"Vector": "o",       "List": "s",       "List (shuffled)": "^"}

datasets = [
    ("Vector",          vector_df),
    ("List",            list_df),
    ("List (shuffled)", list_shuffled_df),
]

XTICKS = [10, 1000, 100_000, 10_000_000]
X_TICKS_REST = [10, 1000]
os.makedirs("./plots", exist_ok=True)


def style_ax(ax, size, show_xlabel=True, show_ylabel=True):
    ax.set_xscale("log")
    if size < 8_000_000:
        ax.set_xticks(XTICKS)
    else:
        ax.set_xticks(X_TICKS_REST)
    ax.xaxis.set_major_formatter(matplotlib.ticker.LogFormatterSciNotation())
    ax.set_yscale("log")
    ax.set_ylim(bottom=1)
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    if show_xlabel:
        ax.set_xlabel("Elements", fontsize=9)
    if show_ylabel:
        ax.set_ylabel("Total operations (normalized)", fontsize=9)

def scatter_lines(ax, sub, label, marker=None):
    m = marker or markers[label]
    ax.scatter(sub["elements"], sub["total_ops"],
               color=colors[label], marker=m, s=60, zorder=3, label=label)
    ax.plot(sub["elements"], sub["total_ops"],
            color=colors[label], alpha=0.25, linewidth=1)


title = "Local"
if LCC3:
    title = "LCC3"

# ── FILE 1: 3×3 (rows=sizes, cols=fractions) ──────────────────────────────────
fig, axes = plt.subplots(3, 3, figsize=(15, 12), sharey=False)
fig.suptitle(f"{title}", fontsize=14, fontweight="bold")

for row, size in enumerate(sizes):
    for col, frac in enumerate(fractions):
        ax = axes[row][col]
        for label, df in datasets:
            sub = df[(df["size"] == size) & (df["fraction"] == frac)].sort_values("elements")
            scatter_lines(ax, sub, label)
        style_ax(ax, size, show_xlabel=(row == 2), show_ylabel=False)
        if row == 0:
            ax.set_title(fraction_labels[frac], fontsize=10)
        if col == 0:
            ax.set_ylabel(f"{size_labels[size]}\nTotal ops (norm.)", fontsize=9)
        if row == 0 and col == 2:
            ax.legend(fontsize=8)

handles = [Line2D([0], [0], marker=markers[l], color=colors[l],
                  linestyle="None", markersize=7, label=l) for l, _ in datasets]
fig.legend(handles=handles, loc="lower center", ncol=3,
           fontsize=9, bbox_to_anchor=(0.5, -0.02), frameon=True)
fig.tight_layout()
fig.savefig(f"./plots/{title.lower()}_bench_3x3.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved bench_3x3.png")


# ── FILE 2: 1×3 (one subplot per size, all fractions squeezed in) ─────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)

for ax, size in zip(axes, sizes):
    for label, df in datasets:
        for frac in fractions:
            sub = df[(df["size"] == size) & (df["fraction"] == frac)].sort_values("elements")
            scatter_lines(ax, sub, label, marker=fraction_markers[frac])
    style_ax(ax, size)
    ax.set_title(f"Element size: {size_labels[size]}", fontsize=10)

handles = []
for label, _ in datasets:
    for frac in fractions:
        handles.append(Line2D([0], [0], marker=fraction_markers[frac], color=colors[label],
                               linestyle="None", markersize=7,
                               label=f"{label}  r={frac}"))
fig.legend(handles=handles, loc="lower center", ncol=len(datasets),
           fontsize=8, bbox_to_anchor=(0.5, -0.18), frameon=True)
fig.tight_layout()
fig.savefig(f"./plots/{title.lower()}_bench_1x3.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved bench_1x3.png")


# ── FILES 3–5: one per element size, 1×3 subplots (one per fraction) ──────────
for size in sizes:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
    fig.suptitle(f"{title} — Element size: {size_labels[size]}",
                 fontsize=14, fontweight="bold", y=1.01)

    for ax, frac in zip(axes, fractions):
        for label, df in datasets:
            sub = df[(df["size"] == size) & (df["fraction"] == frac)].sort_values("elements")
            scatter_lines(ax, sub, label)
        style_ax(ax, size)
        ax.set_title(fraction_labels[frac], fontsize=10)
        ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(f"./plots/{title.lower()}_bench_size_{size_tags[size]}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved bench_size_{size_tags[size]}.png")
