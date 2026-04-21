import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_benchmark(csv_path, output_path):
    try:
        df = pd.read_csv(csv_path, usecols=[0, 3], names=["defines", "value"], header=0)
    except Exception as e:
        print(f"ERROR: Could not read CSV. {e}")
        return
    df['defines'] = df['defines'].apply(lambda x: x.replace("M_T=", "M:").replace("N_T=", "N:").replace("K_T=", "K:").replace("_", " "))
    stats = df.groupby("defines")["value"].median().sort_values(ascending=True).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))

    norm = plt.Normalize(stats["value"].min(), stats["value"].max())
    colors = plt.cm.RdYlGn_r(norm(stats["value"]))

    bars = ax.barh(stats["defines"], stats["value"], color=colors, edgecolor="white", linewidth=0.5)

    ax.set_xlabel("Median Wall Clock Time (Seconds)", fontsize=10)
    
    ax.grid(axis="x", linestyle="--", alpha=0.2)

    max_val = stats["value"].max()

    ax.set_xlim(left=0, right=max_val * 1.15)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + (width * 0.02),
                bar.get_y() + bar.get_height()/2, 
                f'{width:.3f}s', 
                va='center', ha='left', fontsize=9, fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor())
    print(f"✓ Chart saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="Input results.csv")
    parser.add_argument("--output", default="benchmark_results.png", help="Output filename")
    args = parser.parse_args()

    plot_benchmark(args.csv, args.output)