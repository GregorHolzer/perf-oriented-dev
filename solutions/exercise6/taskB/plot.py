import matplotlib.pyplot as plt
import pandas as pd
import argparse


def plot(input_file, output_file):
    df = pd.read_csv(input_file)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df["size_kb"], df["latency_ns"], marker="o", linewidth=2, markersize=4, color="#378ADD")

    # Cache boundary regions
    regions = [
        (0,      32,    "#1D9E75", "L1 (32 KB)"),
        (32,     512,   "#378ADD", "L2 (512 KB)"),
        (512,    16384, "#7F77DD", "L3 (16 MB)"),
        (16384,  float("inf"), "#D85A30", "RAM"),
    ]
    for x_start, x_end, color, label in regions:
        x_end = min(x_end, df["size_kb"].max())
        ax.axvspan(x_start, x_end, alpha=0.1, color=color, label=label)

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xlabel("Buffer size (KB)", fontsize=12)
    ax.set_ylabel("Latency (ns)", fontsize=12)
    ax.set_title("Cache latency by buffer size", fontsize=14)
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.set_xticks(df["size_kb"])
    ax.set_xticklabels([
        f"{s}M" if s >= 1024 else f"{s}K"
        for s in df["size_kb"]
    ], rotation=45)

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

