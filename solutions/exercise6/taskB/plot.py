import matplotlib.pyplot as plt
import pandas as pd
import argparse
import matplotlib.ticker as ticker
import numpy as np

lcc_3regions = [
        (0,      32,    "#1D9E75", "L1 (32 KB)"),
        (32,     256,   "#378ADD", "L2 (256 KB)"),
        (256,    12288, "#7F77DD", "L3 (12 MB)"),
        (12288,  float("inf"), "#D85A30", "RAM"),
    ]

LCC3 = False

TITLE_LCC3 = "LCC3 - Intel(R) Xeon(R) X5650"

def plot(input_file, output_file):
    df = pd.read_csv(input_file)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df["size_kb"], df["latency_ns"], marker="o", linewidth=2, markersize=4, color="#378ADD")

    regions = [
    (0,      32,    "#1D9E75", "L1 (32 KB)"),
    (32,     512,   "#378ADD", "L2 (512 KB)"),
    (512,    16384, "#7F77DD", "L3 (16 MB)"),
    (16384,  float("inf"), "#D85A30", "RAM"),
    ]
    title = "AMD Ryzen 5 3600X 6-Core"
    if LCC3: 
        regions = lcc_3regions
        title = TITLE_LCC3
    for x_start, x_end, color, label in regions:
        x_end = min(x_end, df["size_kb"].max())
        ax.axvspan(x_start, x_end, alpha=0.1, color=color, label=label)

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    max_power = int(np.ceil(np.log2(df["size_kb"].max())))
    powers_of_2 = [2**i for i in range(max_power + 1)]
    ax.set_xlabel("Buffer Size", fontsize=12)
    ax.set_ylabel("Latency [ns]", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.set_xlim(1, df["size_kb"].max())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))
    ax.xaxis.set_major_locator(ticker.FixedLocator(powers_of_2))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, pos: f"{int(x)} KB" if x < 1024 else f"{int(x/1024)} MB"
    ))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    print(f"Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")                
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plot(args.input, args.output)  

if __name__ == "__main__":
  main()

