import matplotlib.pyplot as plt
import pandas as pd
import math

NPB_BT_FILE = "./ratios_npb_bt.csv"
SSCA2_FILE = "./ratios_ssca2.csv"

npb_bt_df = pd.read_csv(NPB_BT_FILE)
ssca2_df = pd.read_csv(SSCA2_FILE)

merged_df = npb_bt_df.merge(ssca2_df, on="metric", suffixes=("_n", "_s")).rename(
    columns={"value_n": "npb_bt_w", "value_s": "ssca2 17"}
).set_index("metric")

merged_df = merged_df[(merged_df != 0).any(axis=1)].dropna(how="all")

n = len(merged_df)
cols = math.ceil(math.sqrt(n))
rows = math.ceil(n / cols)

fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
axes = axes.flatten()

for ax, (metric, row) in zip(axes, merged_df.iterrows()):
    values = row[["npb_bt_w", "ssca2 17"]].values

    bars = ax.bar(
        ["npb_bt", "ssca2"],
        values,
        color=["blue", "red"],
        width=1.0
    )

    ax.set_title(metric)
    ax.set_xticks([])

    ax.legend(bars, ["npb_bt", "ssca2"])

plt.tight_layout()
plt.savefig("perf_comp.png", dpi=300)
plt.close(fig)